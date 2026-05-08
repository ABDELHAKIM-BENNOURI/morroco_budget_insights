#!/usr/bin/env python3
"""
02_clean.py — Nettoyage et consolidation des CSVs PLF 2026

Lit les 9 CSVs bruts produits par 01_extract.py, applique :
  - suppression de lignes parasites ("Désignation" dans la dette)
  - filtrage des en-têtes sans données numériques
  - calcul de variation_pct et part_pct manquants
  - catégorisation des recettes (fiscales / non fiscales / emprunts)
  - flag is_total pour les lignes de totaux
  - fusion simple + detail des dépenses ministérielles (clé normalisée)
  - taxonomie sectorielle figée (Social / Souveraineté / Économique / Infra / Autre)
  - enrichissement des chiffres clés avec labels contextuels
  - validation de cohérence Σ recettes ≈ 421.33 MMDH (tolérance ±0.5)

Sorties (data/clean/) :
  - recettes_plf2026_clean.csv
  - depenses_ministere_plf2026_clean.csv
  - dette_clean.csv
  - budget_canonical.csv
  - chiffres_cles_plf2026_enrichi.csv

Codes de sortie :
  0 — succès
  1 — erreur d'environnement (dossier introuvable, fichier source manquant)
  2 — anomalie critique (incohérence budgétaire bloquante)
"""

import re
import sys
import unicodedata
import pandas as pd
from pathlib import Path

BASE  = Path(__file__).resolve().parent.parent
CLEAN = BASE / "data" / "clean"

# ── Constantes métier ─────────────────────────────────────────────────────────

CIBLE_RECETTES_MMDH = 421.33
CIBLE_DEPENSES_MMDH = 527.65
TOLERANCE_MMDH      = 0.5

SOURCE_FILES = [
    "recettes_plf2026.csv",
    "recettes_lf2024_2025.csv",
    "depenses_fonctionnement_2024_2025.csv",
    "dette_2024_2025.csv",
    "synthese_budget_2024_2025.csv",
    "cst_plf2026.csv",
    "depenses_ministere_plf2026_simple.csv",
    "depenses_ministere_plf2026_detail.csv",
    "chiffres_cles_plf2026.csv",
]

# Recettes PLF 2026 — catégorisation par numéro de désignation (préfixe "N -")
RECETTES_FISCALES_NUMS     = {'1', '2', '3', '4'}
RECETTES_NON_FISCALES_NUMS = {'5', '6', '7', '8', '9'}

# ── Taxonomie sectorielle figée (mémoire projet 2026-05-07) ───────────────────
# Mots-clés en MAJUSCULES sans accents (matching après normalisation).
# Ordre = priorité : Social > Souveraineté > Infra > Économique.
TAXONOMIE_SECTEUR = [
    ('Social', [
        'EDUCATION', 'ENSEIGNEMENT', 'SANTE', 'SOLIDARITE',
        'JEUNESSE', 'CULTURE', 'INCLUSION ECONOMIQUE',
        'PROTECTION SOCIALE', 'FAMILLE',
    ]),
    ('Souveraineté', [
        'DEFENSE NATIONALE', 'INTERIEUR', 'JUSTICE',
        'AFFAIRES ETRANGERES', 'HABOUS', 'AFFAIRES ISLAMIQUES',
        'PARLEMENT', 'POUVOIR JUDICIAIRE', 'PENITENTIAIRE',
        'ANCIENS RESISTANTS', 'COUR ROYALE',
        'CHAMBRE DES REPRESENTANTS', 'CHAMBRE DES CONSEILLERS',
        'JURIDICTIONS FINANCIERES',
    ]),
    ('Infra', [
        'EQUIPEMENT', 'TRANSPORT', 'LOGISTIQUE',
        'HABITAT', 'AMENAGEMENT DU TERRITOIRE', 'URBANISME',
        'TRANSITION ENERGETIQUE', 'TRANSITION NUMERIQUE',
        'DEVELOPPEMENT DURABLE',
    ]),
    ('Économique', [
        'ECONOMIE', 'FINANCES', 'INDUSTRIE', 'COMMERCE',
        'TOURISME', 'ARTISANAT', 'AGRICULTURE', 'PECHE',
        'INVESTISSEMENT', 'EMPLOI', 'COMPETENCES', 'PLAN',
        'CONVERGENCE',
    ]),
]

# Overrides exacts (institutions ambiguës ou non-ministères).
SECTEUR_OVERRIDES_EXACT = {
    'SA MAJESTE LE ROI':                                'Souveraineté',
    'CHEF DU GOUVERNEMENT':                             'Souveraineté',
    'SECRETARIAT GENERAL DU GOUVERNEMENT':              'Autre',
    'DEPENSES IMPREVUES ET DOTATIONS PROVISIONNELLES':  'Autre',
    'HAUT COMMISSARIAT AU PLAN':                        'Autre',
}

# Overrides par sous-chaîne (Conseils consultatifs, instances de contrôle).
SECTEUR_OVERRIDES_CONTAINS = [
    ('CONSEIL ECONOMIQUE',          'Autre'),
    ('CONSEIL NATIONAL DES DROITS', 'Autre'),
    ('INSTANCE NATIONALE',          'Autre'),
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def strip_accents(s):
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def normalize_label(s):
    """Uppercase + sans accents + ponctuation→espace + typos corrigés. Pour comparaison/jointure."""
    if s is None:
        return ''
    s = strip_accents(str(s)).upper()
    s = re.sub(r"[^\w\s]", ' ', s)               # ponctuation (`,`-`'`) → espace
    s = re.sub(r'\s+', ' ', s).strip()
    s = s.replace('ADMINISRATION', 'ADMINISTRATION')   # typo d'extraction p.164
    return s


def _kw_match(label, kw):
    """Match par limites de mot — empêche CULTURE de matcher AGRICULTURE."""
    return re.search(r'\b' + re.escape(kw) + r'\b', label) is not None


def safe_num(x):
    """NaN / None → 0.0 ; sinon float."""
    return float(x) if pd.notna(x) else 0.0


def is_total_row(label):
    """Détecte une ligne de total (insensible à la casse/accent)."""
    if label is None or pd.isna(label):
        return False
    norm = normalize_label(label)
    return norm == 'TOTAL' or norm.startswith('TOTAL ') or 'TOTAL DES' in norm


def classify_secteur(ministere):
    """Retourne le secteur selon la taxonomie figée."""
    norm = normalize_label(ministere)
    if not norm:
        return 'Autre'
    if norm in SECTEUR_OVERRIDES_EXACT:
        return SECTEUR_OVERRIDES_EXACT[norm]
    for pattern, sec in SECTEUR_OVERRIDES_CONTAINS:
        if pattern in norm:
            return sec
    for secteur, keywords in TAXONOMIE_SECTEUR:
        for kw in keywords:
            if _kw_match(norm, kw):
                return secteur
    return 'Autre'


def classify_recette_categorie(designation):
    """Catégorise une ligne du CSV recettes_plf2026 selon son préfixe numérique."""
    if designation is None or pd.isna(designation):
        return None
    m = re.match(r'^\s*(\d+)\s*[-–]', str(designation))
    if not m:
        return None
    num = m.group(1)
    if num in RECETTES_FISCALES_NUMS:
        return 'recettes_fiscales'
    if num in RECETTES_NON_FISCALES_NUMS:
        return 'recettes_non_fiscales'
    return None


def classify_recette_lf(designation):
    """Catégorise une ligne du CSV LF 2024/2025 (présence d'emprunts possible)."""
    if designation is None or pd.isna(designation):
        return None
    norm = normalize_label(designation)
    if 'EMPRUNT' in norm:
        return 'emprunts'
    if 'NON FISCAL' in norm:
        return 'recettes_non_fiscales'
    if 'RECETTES FISCALES' in norm:
        return 'recettes_fiscales'
    return None


# ── Cleaners par CSV ──────────────────────────────────────────────────────────

def load_all_sources():
    """1.1 — Lit les 9 CSVs et vérifie leur présence."""
    sources = {}
    missing = []
    for name in SOURCE_FILES:
        path = CLEAN / name
        if not path.exists():
            missing.append(name)
            continue
        sources[name] = pd.read_csv(path)
    if missing:
        print(f"❌ Fichiers sources manquants : {missing}", file=sys.stderr)
        sys.exit(1)
    return sources


def clean_recettes_plf2026(df):
    """Nettoie + catégorise + flagge totaux + calcule variation/part."""
    df = df.copy()
    df = df.dropna(subset=['designation'])
    df = df[df['designation'].astype(str).str.strip() != '']

    df['is_total']  = df['designation'].apply(is_total_row)
    df['categorie'] = df.apply(
        lambda r: 'total_recettes' if r['is_total']
        else classify_recette_categorie(r['designation']),
        axis=1,
    )

    # 1.4 — variation_pct si manquante
    can_var = (
        df['variation_pct'].isna()
        & df['lf_2025_mmdh'].notna()
        & df['plf_2026_mmdh'].notna()
        & (df['lf_2025_mmdh'] != 0)
    )
    df.loc[can_var, 'variation_pct'] = (
        (df.loc[can_var, 'plf_2026_mmdh'] - df.loc[can_var, 'lf_2025_mmdh'])
        / df.loc[can_var, 'lf_2025_mmdh'] * 100
    ).round(2)

    # 1.4 — part_pct sur PLF 2026 (base = total)
    total_plf = df.loc[df['is_total'], 'plf_2026_mmdh'].sum()
    if total_plf > 0:
        df['part_pct'] = (df['plf_2026_mmdh'] / total_plf * 100).round(2)
        df.loc[df['is_total'], 'part_pct'] = 100.0
    else:
        df['part_pct'] = pd.NA

    cols = ['designation', 'categorie', 'lf_2025_mmdh', 'plf_2026_mmdh',
            'variation_pct', 'part_pct', 'is_total', 'source']
    return df[cols].reset_index(drop=True)


def clean_recettes_lf2024_2025(df):
    """Nettoie le CSV LF 2024/2025 — filtre les en-têtes et calcule variation."""
    df = df.copy()
    # 1.3 — filtre lignes header sans données numériques
    df = df[df['lf_2024_mmdh'].notna() | df['lf_2025_mmdh'].notna()]

    df['is_total']  = df['designation'].apply(is_total_row)
    df['categorie'] = df['designation'].apply(classify_recette_lf)

    # 1.4 — variation_pct calculée si manquante
    can_var = (
        df['variation_pct'].isna()
        & df['lf_2024_mmdh'].notna()
        & df['lf_2025_mmdh'].notna()
        & (df['lf_2024_mmdh'] != 0)
    )
    df.loc[can_var, 'variation_pct'] = (
        (df.loc[can_var, 'lf_2025_mmdh'] - df.loc[can_var, 'lf_2024_mmdh'])
        / df.loc[can_var, 'lf_2024_mmdh'] * 100
    ).round(2)

    return df.reset_index(drop=True)


def clean_dette(df):
    """1.2 — supprime ligne parasite 'Désignation' + flag total + variation."""
    df = df.copy()
    df = df[~df['designation'].astype(str).str.strip().str.lower().eq('désignation')]
    df = df.dropna(subset=['designation'])
    df = df[df['lf_2024_mmdh'].notna() | df['lf_2025_mmdh'].notna()]

    df['is_total'] = df['designation'].apply(is_total_row)

    can_var = (
        df['variation_pct'].isna()
        & df['lf_2024_mmdh'].notna()
        & df['lf_2025_mmdh'].notna()
        & (df['lf_2024_mmdh'] != 0)
    )
    df.loc[can_var, 'variation_pct'] = (
        (df.loc[can_var, 'lf_2025_mmdh'] - df.loc[can_var, 'lf_2024_mmdh'])
        / df.loc[can_var, 'lf_2024_mmdh'] * 100
    ).round(2)

    cols = ['designation', 'lf_2024_mmdh', 'lf_2025_mmdh',
            'variation_abs_mmdh', 'variation_pct', 'is_total', 'source']
    return df[cols].reset_index(drop=True)


def merge_depenses_ministere(simple, detail):
    """1.7 — Fusion simple + detail (clé normalisée), 1.6 is_total, 1.8 secteur."""
    sp = simple.copy()
    dt = detail.copy()
    sp['_key'] = sp['ministere'].apply(normalize_label)
    dt['_key'] = dt['ministere'].apply(normalize_label)

    sp_trim = sp.rename(columns={
        'personnel_mmdh':       'personnel_simple_mmdh',
        'materiel_mmdh':        'materiel_simple_mmdh',
        'fonctionnement_mmdh':  'fonctionnement_simple_mmdh',
        'investissement_mmdh':  'investissement_simple_mmdh',
        'source':               'source_simple',
    })[['_key', 'ministere', 'personnel_simple_mmdh',
        'materiel_simple_mmdh', 'fonctionnement_simple_mmdh',
        'investissement_simple_mmdh', 'source_simple']]
    sp_trim = sp_trim.rename(columns={'ministere': 'ministere_simple'})

    merged = dt.merge(sp_trim, on='_key', how='outer')

    # Source de vérité : detail. Fallback simple sur ministere/colonnes manquantes.
    merged['ministere_final'] = merged['ministere'].fillna(merged['ministere_simple'])
    merged['source_final']    = merged['source'].fillna(merged['source_simple'])

    def coalesce(detail_col, simple_col):
        return merged[detail_col].where(merged[detail_col].notna(), merged[simple_col])

    merged['personnel_mmdh']       = coalesce('personnel_plf2026_mmdh',
                                              'personnel_simple_mmdh')
    merged['materiel_mmdh']        = coalesce('materiel_plf2026_mmdh',
                                              'materiel_simple_mmdh')
    merged['fonctionnement_mmdh']  = coalesce('fonctionnement_plf2026_mmdh',
                                              'fonctionnement_simple_mmdh')

    # Investissement : détail = CP + CE ; sinon fallback simple
    def compute_invest_total(row):
        cp = row.get('invest_cp_plf2026_mmdh')
        ce = row.get('invest_ce_plf2026_mmdh')
        if pd.notna(cp) or pd.notna(ce):
            return round(safe_num(cp) + safe_num(ce), 4)
        fallback = row.get('investissement_simple_mmdh')
        return float(fallback) if pd.notna(fallback) else None

    merged['invest_total_mmdh'] = merged.apply(compute_invest_total, axis=1)

    # Total ministère = fonctionnement + investissement
    def compute_total(row):
        f = row.get('fonctionnement_mmdh')
        i = row.get('invest_total_mmdh')
        if pd.isna(f) and pd.isna(i):
            return None
        return round(safe_num(f) + safe_num(i), 4)

    merged['total_mmdh'] = merged.apply(compute_total, axis=1)

    merged['is_total'] = merged['ministere_final'].apply(is_total_row)
    merged['secteur']  = merged.apply(
        lambda r: None if r['is_total'] else classify_secteur(r['ministere_final']),
        axis=1,
    )

    out = merged.drop(columns=['ministere', 'ministere_simple', 'source', 'source_simple'])
    out = out.rename(columns={
        'ministere_final':           'ministere',
        'invest_cp_plf2026_mmdh':    'invest_cp_mmdh',
        'invest_ce_plf2026_mmdh':    'invest_ce_mmdh',
        'source_final':              'source',
    })
    out = out.dropna(subset=['ministere'])
    out = out[out['ministere'].astype(str).str.strip() != '']

    cols = ['ministere', 'secteur', 'is_total',
            'personnel_mmdh', 'materiel_mmdh', 'fonctionnement_mmdh',
            'invest_cp_mmdh', 'invest_ce_mmdh', 'invest_total_mmdh',
            'total_mmdh', 'source']
    return out[cols].reset_index(drop=True)


def enrich_chiffres_cles(df):
    """1.9 — Ajoute label + contexte aux chiffres clés extraits du texte brut."""
    df = df.copy()
    labels = {
        round(CIBLE_RECETTES_MMDH, 2): (
            'recettes_total_plf2026',
            'Total des recettes ordinaires du Budget Général PLF 2026',
        ),
        round(CIBLE_DEPENSES_MMDH, 2): (
            'depenses_total_plf2026',
            'Total des dépenses du Budget Général PLF 2026',
        ),
    }

    def _lookup(v):
        return labels.get(round(float(v), 2), ('non_identifie', ''))

    df['label']    = df['valeur_mmdh'].apply(lambda v: _lookup(v)[0])
    df['contexte'] = df['valeur_mmdh'].apply(lambda v: _lookup(v)[1])
    return df[['label', 'valeur_mmdh', 'contexte', 'source']].reset_index(drop=True)


# ── Canonical (1.11) ──────────────────────────────────────────────────────────

def build_canonical(rec, dep, dette):
    """Assemble un CSV tidy unifié pour Sankey/Treemap (PLF 2026)."""
    rows = []

    # Recettes (hors total)
    for _, r in rec.iterrows():
        if r['is_total'] or pd.isna(r['plf_2026_mmdh']):
            continue
        rows.append({
            'type':       'recette',
            'niveau':     1,
            'categorie':  r['categorie'] or 'autre',
            'secteur':    '',
            'label':      r['designation'],
            'parent':     r['categorie'] or 'recettes',
            'value_mmdh': float(r['plf_2026_mmdh']),
            'is_total':   False,
            'year':       2026,
            'source':     r['source'],
        })

    # Dépenses ministérielles (hors total)
    for _, r in dep.iterrows():
        if r['is_total']:
            continue
        secteur = r['secteur'] or 'Autre'
        if pd.notna(r['fonctionnement_mmdh']) and float(r['fonctionnement_mmdh']) > 0:
            rows.append({
                'type':       'depense',
                'niveau':     2,
                'categorie':  'fonctionnement',
                'secteur':    secteur,
                'label':      r['ministere'],
                'parent':     'fonctionnement',
                'value_mmdh': float(r['fonctionnement_mmdh']),
                'is_total':   False,
                'year':       2026,
                'source':     r['source'],
            })
        if pd.notna(r['invest_total_mmdh']) and float(r['invest_total_mmdh']) > 0:
            rows.append({
                'type':       'depense',
                'niveau':     2,
                'categorie':  'investissement',
                'secteur':    secteur,
                'label':      r['ministere'],
                'parent':     'investissement',
                'value_mmdh': float(r['invest_total_mmdh']),
                'is_total':   False,
                'year':       2026,
                'source':     r['source'],
            })

    # Dette (LF 2025 — pas de PLF 2026 disponible dans les sources extraites)
    for _, r in dette.iterrows():
        if r['is_total'] or pd.isna(r['lf_2025_mmdh']):
            continue
        rows.append({
            'type':       'depense',
            'niveau':     2,
            'categorie':  'dette',
            'secteur':    'Souveraineté',
            'label':      r['designation'],
            'parent':     'dette',
            'value_mmdh': float(r['lf_2025_mmdh']),
            'is_total':   False,
            'year':       2025,
            'source':     r['source'],
        })

    return pd.DataFrame(rows)


# ── Validation (1.10) ─────────────────────────────────────────────────────────

def validate(rec, dep, dette, ck, sources):
    """Vérifie cohérence Σ recettes ≈ 421.33 MMDH (tolérance ±0.5)."""
    sum_rec = rec.loc[~rec['is_total'], 'plf_2026_mmdh'].sum()
    diff    = abs(sum_rec - CIBLE_RECETTES_MMDH)
    rec_ok  = diff <= TOLERANCE_MMDH

    sum_dep_min = dep.loc[~dep['is_total'], 'total_mmdh'].sum()

    cck_recettes = ck[ck['label'] == 'recettes_total_plf2026']['valeur_mmdh']
    cck_depenses = ck[ck['label'] == 'depenses_total_plf2026']['valeur_mmdh']
    cck_recettes_ok = (
        not cck_recettes.empty
        and abs(float(cck_recettes.iloc[0]) - CIBLE_RECETTES_MMDH) <= TOLERANCE_MMDH
    )
    cck_depenses_ok = (
        not cck_depenses.empty
        and abs(float(cck_depenses.iloc[0]) - CIBLE_DEPENSES_MMDH) <= TOLERANCE_MMDH
    )

    return {
        'sources_loaded':     len(sources),
        'sum_recettes_mmdh':  round(sum_rec, 4),
        'cible_recettes':     CIBLE_RECETTES_MMDH,
        'diff_recettes':      round(diff, 4),
        'tolerance':          TOLERANCE_MMDH,
        'recettes_ok':        bool(rec_ok),
        'sum_depenses_min':   round(sum_dep_min, 4),
        'cible_depenses':     CIBLE_DEPENSES_MMDH,
        'cck_recettes_ok':    bool(cck_recettes_ok),
        'cck_depenses_ok':    bool(cck_depenses_ok),
        'n_recettes_lignes':  int((~rec['is_total']).sum()),
        'n_ministeres':       int((~dep['is_total']).sum()),
        'n_dette_lignes':     int((~dette['is_total']).sum()),
        'n_chiffres_cles':    int(len(ck)),
    }


def report(v, rec, dep, dette, ck, canon):
    print()
    print("=" * 72)
    print("  RAPPORT DE VALIDATION — 02_clean.py")
    print("=" * 72)
    print(f"  Sources chargées       : {v['sources_loaded']}/9")
    print()
    print("  ── Recettes PLF 2026 ──")
    print(f"    Σ (hors total)       : {v['sum_recettes_mmdh']:>10.4f} MMDH")
    print(f"    Cible                : {v['cible_recettes']:>10.2f} MMDH"
          f"  (tolérance ±{v['tolerance']:.1f})")
    print(f"    Écart                : {v['diff_recettes']:>10.4f} MMDH")
    status = "✅ COHÉRENT" if v['recettes_ok'] else "❌ INCOHÉRENT (anomalie critique)"
    print(f"    Validation           : {status}")
    print()
    print("  ── Chiffres clés enrichis ──")
    print(f"    Recettes 421.33 MMDH : "
          f"{'✅' if v['cck_recettes_ok'] else '❌'}")
    print(f"    Dépenses 527.65 MMDH : "
          f"{'✅' if v['cck_depenses_ok'] else '❌'}")
    print()
    print("  ── Volumétrie ──")
    print(f"    Recettes lignes      : {v['n_recettes_lignes']}")
    print(f"    Ministères           : {v['n_ministeres']}")
    print(f"    Dette lignes         : {v['n_dette_lignes']}")
    print(f"    Chiffres clés        : {v['n_chiffres_cles']}")
    print()
    print("  ── Sorties data/clean/ ──")
    print(f"    recettes_plf2026_clean.csv             ({len(rec)} lignes)")
    print(f"    depenses_ministere_plf2026_clean.csv   ({len(dep)} lignes)")
    print(f"    dette_clean.csv                        ({len(dette)} lignes)")
    print(f"    budget_canonical.csv                   ({len(canon)} lignes)")
    print(f"    chiffres_cles_plf2026_enrichi.csv      ({len(ck)} lignes)")
    print()
    print("  ── Σ dépenses ministères (informationnel) ──")
    print(f"    Σ total_mmdh         : {v['sum_depenses_min']:>10.4f} MMDH")
    print(f"    Cible 527.65         : "
          f"écart = {abs(v['sum_depenses_min'] - v['cible_depenses']):.4f} MMDH")
    print("=" * 72)


# ── Point d'entrée ────────────────────────────────────────────────────────────

def main():
    if not CLEAN.exists():
        print(f"❌ Dossier introuvable : {CLEAN}", file=sys.stderr)
        sys.exit(1)

    print("=" * 72)
    print("  NETTOYAGE & CONSOLIDATION — MAROC PLF 2026")
    print("=" * 72)

    sources = load_all_sources()
    print(f"  ✅ {len(sources)} fichiers sources chargés depuis data/clean/")

    rec   = clean_recettes_plf2026(sources['recettes_plf2026.csv'])
    _     = clean_recettes_lf2024_2025(sources['recettes_lf2024_2025.csv'])
    dette = clean_dette(sources['dette_2024_2025.csv'])
    dep   = merge_depenses_ministere(
        sources['depenses_ministere_plf2026_simple.csv'],
        sources['depenses_ministere_plf2026_detail.csv'],
    )
    ck    = enrich_chiffres_cles(sources['chiffres_cles_plf2026.csv'])
    canon = build_canonical(rec, dep, dette)

    rec.to_csv(CLEAN / "recettes_plf2026_clean.csv",
               index=False, encoding='utf-8-sig')
    dep.to_csv(CLEAN / "depenses_ministere_plf2026_clean.csv",
               index=False, encoding='utf-8-sig')
    dette.to_csv(CLEAN / "dette_clean.csv",
                 index=False, encoding='utf-8-sig')
    canon.to_csv(CLEAN / "budget_canonical.csv",
                 index=False, encoding='utf-8-sig')
    ck.to_csv(CLEAN / "chiffres_cles_plf2026_enrichi.csv",
              index=False, encoding='utf-8-sig')

    v = validate(rec, dep, dette, ck, sources)
    report(v, rec, dep, dette, ck, canon)

    if not v['recettes_ok']:
        print("\n⛔ Anomalie critique : Σ recettes ≠ 421.33 MMDH "
              "(tolérance dépassée).", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
