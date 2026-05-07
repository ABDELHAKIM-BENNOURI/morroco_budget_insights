#!/usr/bin/env python3
"""
01_extract.py — Extraction ciblée des données budgétaires Maroc PLF 2026

Pages cibles identifiées par analyse préalable :
  Note-presentation_Fr.pdf  : p.29 (recettes), p.163-164 (dépenses/ministère), p.32 (CST)
  BCPLF2026.pdf             : p.14 (chiffres clés texte), p.52-54 (dépenses/ministère)
  SLF-23 Fr-2025.pdf        : p.19 (synthèse), p.20 (fonctionnement), p.22 (dette), p.23 (recettes)

Problèmes gérés :
  - OCR doublé (SLF) : extract_tables() fonctionne malgré texte brut corrompu
  - Faux tableaux : filtre sur nb_cols > 20 avec cells 1 char (texte vertical)
  - Fragments mono-colonne : filtre nb_cols < 2
  - Nombres : dirhams / MDH / MMDH, séparateurs mixtes (espace, point, virgule)
"""

import re
import pdfplumber
import pandas as pd
from pathlib import Path

# ── Chemins ───────────────────────────────────────────────────────────────────

BASE  = Path(__file__).resolve().parent.parent
RAW   = BASE / "data" / "raw"
CLEAN = BASE / "data" / "clean"
CLEAN.mkdir(parents=True, exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def clean_number(val):
    """
    Convertit les formats numériques marocains/français en float.

    Formats gérés :
      '140 735 176 000'  → 140735176000.0   (espaces = milliers, dirhams)
      '140 735,18'       → 140735.18        (espace milliers + virgule décimale, MDH)
      '643.597.000'      → 643597000.0      (points = milliers)
      '17,73'            → 17.73            (virgule décimale, %)
      '-13,64'           → -13.64
      '-' / '' / None    → None
    """
    if val is None:
        return None
    val = str(val).strip()
    val = re.sub(r'\*+', '', val)           # astérisques de notes de bas de page
    val = re.sub(r'[\n\r\t]', ' ', val)
    val = val.strip()

    if val in ('', '-', '–', '—', 'N/A', 'n/a', 'na'):
        return None

    val = val.replace(' ', '')              # supprime les espaces (séparateurs milliers)
    dot_count   = val.count('.')
    comma_count = val.count(',')

    try:
        if comma_count == 1 and dot_count == 0:
            # Format français : 17,73  ou  140735,18
            return float(val.replace(',', '.'))

        if comma_count == 0 and dot_count == 0:
            # Entier pur
            return float(val)

        if dot_count > 1 and comma_count == 0:
            # Points = séparateurs milliers : 643.597.000
            return float(val.replace('.', ''))

        if dot_count == 1 and comma_count == 0:
            parts = val.split('.')
            if len(parts[1]) == 3:
                # Point = séparateur milliers (ex: 131.608 → 131608)
                return float(val.replace('.', ''))
            return float(val)               # point décimal standard

        if dot_count >= 1 and comma_count == 1:
            # Format : 140.735,18  →  140735.18
            return float(val.replace('.', '').replace(',', '.'))

    except ValueError:
        pass
    return None


def to_mmdh(val_dirhams):
    """Dirhams → MMDH (milliards de dirhams)."""
    if val_dirhams is None:
        return None
    return round(val_dirhams / 1_000_000_000, 4)


def to_mmdh_mdh(val_mdh):
    """MDH (millions de dirhams) → MMDH."""
    if val_mdh is None:
        return None
    return round(val_mdh / 1_000, 4)


def get_tables(pdf_path, page_num):
    """
    Retourne les tableaux valides d'une page (1-indexé).
    Filtre :
      - Tableaux avec < 2 colonnes (fragments)
      - Tableaux avec > 20 colonnes et cellules de 1 char (texte vertical parsé)
    """
    with pdfplumber.open(pdf_path) as pdf:
        tables = pdf.pages[page_num - 1].extract_tables()

    valid = []
    for t in (tables or []):
        if not t or len(t) < 2 or len(t[0]) < 2:
            continue
        if len(t[0]) > 20 and all(len(str(c or '')) <= 2 for c in t[0]):
            continue  # texte vertical parsé caractère par caractère
        valid.append(t)
    return valid


def get_text(pdf_path, page_num):
    with pdfplumber.open(pdf_path) as pdf:
        return pdf.pages[page_num - 1].extract_text() or ""


def best_table(tables, min_cols=3):
    """Retourne le tableau avec le plus grand nombre de cellules (≥ min_cols colonnes)."""
    candidates = [t for t in tables if len(t[0]) >= min_cols]
    if not candidates:
        candidates = tables
    return max(candidates, key=lambda t: len(t) * len(t[0]))


# ── Extracteurs ───────────────────────────────────────────────────────────────

def extract_recettes_plf2026():
    """
    Note-presentation_Fr.pdf — p.29
    Tableau des recettes du Budget Général : LF 2025 vs PLF 2026
    Unité source : dirhams → converti en MMDH
    """
    print("\n[1/8] Recettes PLF 2026 (Note-presentation p.29)")
    tables = get_tables(RAW / "Note-presentation_Fr.pdf", 29)
    if not tables:
        print("  ⚠️  Aucun tableau trouvé")
        return pd.DataFrame()

    t = best_table(tables, min_cols=3)
    rows = []
    for row in t:
        label = str(row[0] or '').replace('\n', ' ').strip()
        if not label or label.startswith('Désignation'):
            continue
        lf2025  = clean_number(row[1] if len(row) > 1 else None)
        plf2026 = clean_number(row[2] if len(row) > 2 else None)
        var_pct = clean_number(row[3] if len(row) > 3 else None)
        if lf2025 is None and plf2026 is None:
            continue
        rows.append({
            'designation':   label,
            'lf_2025_mmdh':  to_mmdh(lf2025),
            'plf_2026_mmdh': to_mmdh(plf2026),
            'variation_pct': var_pct,
            'source': 'Note-presentation_Fr p.29',
        })

    df = pd.DataFrame(rows)
    df.to_csv(CLEAN / "recettes_plf2026.csv", index=False, encoding='utf-8-sig')
    print(f"  ✅ {len(df)} lignes  →  data/clean/recettes_plf2026.csv")
    print(df[['designation', 'lf_2025_mmdh', 'plf_2026_mmdh']].to_string(index=False))
    return df


def extract_recettes_lf2024_2025():
    """
    SLF-23 Fr-2025.pdf — p.23
    Recettes Budget Général : LF 2024 vs LF 2025 (avec parts et variations)
    Unité source : MDH → MMDH
    Note : texte brut bruité (OCR doublé) mais extract_tables() opérationnel
    """
    print("\n[2/8] Recettes LF 2024 vs 2025 (SLF-23 p.23)")
    tables = get_tables(RAW / "SLF-23 Fr-2025.pdf", 23)
    if not tables:
        print("  ⚠️  Aucun tableau trouvé")
        return pd.DataFrame()

    t = best_table(tables, min_cols=4)
    rows = []
    for row in t:
        label = str(row[0] or '').replace('\n', ' ').strip()
        if not label or 'Désignation' in label:
            continue
        lf2024  = clean_number(row[1] if len(row) > 1 else None)
        lf2025  = clean_number(row[2] if len(row) > 2 else None)
        var_pct = clean_number(row[4] if len(row) > 4 else None)
        part    = clean_number(row[5] if len(row) > 5 else None)
        rows.append({
            'designation':  label,
            'lf_2024_mmdh': to_mmdh_mdh(lf2024),
            'lf_2025_mmdh': to_mmdh_mdh(lf2025),
            'variation_pct': var_pct,
            'part_2025_pct': part,
            'source': 'SLF-23 Fr-2025 p.23',
        })

    df = pd.DataFrame(rows)
    df = df[df['designation'].str.len() > 2]
    df.to_csv(CLEAN / "recettes_lf2024_2025.csv", index=False, encoding='utf-8-sig')
    print(f"  ✅ {len(df)} lignes  →  data/clean/recettes_lf2024_2025.csv")
    print(df[['designation', 'lf_2024_mmdh', 'lf_2025_mmdh']].to_string(index=False))
    return df


def extract_depenses_fonctionnement():
    """
    SLF-23 Fr-2025.pdf — p.20
    Dépenses de fonctionnement : LF 2024 vs LF 2025
    Unité source : MDH → MMDH
    """
    print("\n[3/8] Dépenses fonctionnement LF 2024 vs 2025 (SLF-23 p.20)")
    tables = get_tables(RAW / "SLF-23 Fr-2025.pdf", 20)
    if not tables:
        print("  ⚠️  Aucun tableau trouvé")
        return pd.DataFrame()

    t = best_table(tables, min_cols=4)
    rows = []
    for row in t:
        label = str(row[0] or '').replace('\n', ' ').strip()
        if not label or 'Désignation' in label:
            continue
        lf2024  = clean_number(row[1] if len(row) > 1 else None)
        lf2025  = clean_number(row[2] if len(row) > 2 else None)
        var_pct = clean_number(row[4] if len(row) > 4 else None)
        part    = clean_number(row[5] if len(row) > 5 else None)
        if lf2024 is None and lf2025 is None:
            continue
        rows.append({
            'designation':  label,
            'lf_2024_mmdh': to_mmdh_mdh(lf2024),
            'lf_2025_mmdh': to_mmdh_mdh(lf2025),
            'variation_pct': var_pct,
            'part_2025_pct': part,
            'source': 'SLF-23 Fr-2025 p.20',
        })

    df = pd.DataFrame(rows)
    df.to_csv(CLEAN / "depenses_fonctionnement_2024_2025.csv", index=False, encoding='utf-8-sig')
    print(f"  ✅ {len(df)} lignes  →  data/clean/depenses_fonctionnement_2024_2025.csv")
    print(df[['designation', 'lf_2024_mmdh', 'lf_2025_mmdh']].to_string(index=False))
    return df


def extract_dette():
    """
    SLF-23 Fr-2025.pdf — p.22
    Charges de la dette : extérieure vs intérieure, LF 2024 vs LF 2025
    Unité source : MDH → MMDH
    """
    print("\n[4/8] Charges de la dette (SLF-23 p.22)")
    tables = get_tables(RAW / "SLF-23 Fr-2025.pdf", 22)
    if not tables:
        print("  ⚠️  Aucun tableau trouvé")
        return pd.DataFrame()

    # Table de la dette : 5L x 5C
    t = best_table(tables, min_cols=3)
    rows = []
    for row in t:
        label = str(row[0] or '').replace('\n', ' ').strip()
        if not label:
            continue
        lf2024  = clean_number(row[1] if len(row) > 1 else None)
        lf2025  = clean_number(row[2] if len(row) > 2 else None)
        var_abs = clean_number(row[3] if len(row) > 3 else None)
        var_pct = clean_number(row[4] if len(row) > 4 else None)
        rows.append({
            'designation':  label,
            'lf_2024_mmdh': to_mmdh_mdh(lf2024),
            'lf_2025_mmdh': to_mmdh_mdh(lf2025),
            'variation_abs_mmdh': to_mmdh_mdh(var_abs),
            'variation_pct': var_pct,
            'source': 'SLF-23 Fr-2025 p.22',
        })

    df = pd.DataFrame(rows)
    df = df[df['designation'].str.len() > 2]
    df.to_csv(CLEAN / "dette_2024_2025.csv", index=False, encoding='utf-8-sig')
    print(f"  ✅ {len(df)} lignes  →  data/clean/dette_2024_2025.csv")
    print(df[['designation', 'lf_2024_mmdh', 'lf_2025_mmdh']].to_string(index=False))
    return df


def extract_synthese_budget():
    """
    SLF-23 Fr-2025.pdf — p.19
    Synthèse charges/ressources : Budget Général, SEGMA, CST — LF 2024 vs LF 2025
    Unité source : MDH → MMDH
    """
    print("\n[5/8] Synthèse budget LF 2024 vs 2025 (SLF-23 p.19)")
    tables = get_tables(RAW / "SLF-23 Fr-2025.pdf", 19)
    if not tables:
        print("  ⚠️  Aucun tableau trouvé")
        return pd.DataFrame()

    t = best_table(tables, min_cols=3)
    rows = []
    for row in t:
        label = str(row[0] or '').replace('\n', ' ').strip()
        if not label or 'Désignation' in label:
            continue
        lf2024  = clean_number(row[1] if len(row) > 1 else None)
        lf2025  = clean_number(row[2] if len(row) > 2 else None)
        var_pct = clean_number(row[4] if len(row) > 4 else None)
        if lf2024 is None and lf2025 is None:
            continue
        rows.append({
            'designation':  label,
            'lf_2024_mmdh': to_mmdh_mdh(lf2024),
            'lf_2025_mmdh': to_mmdh_mdh(lf2025),
            'variation_pct': var_pct,
            'source': 'SLF-23 Fr-2025 p.19',
        })

    df = pd.DataFrame(rows)
    df.to_csv(CLEAN / "synthese_budget_2024_2025.csv", index=False, encoding='utf-8-sig')
    print(f"  ✅ {len(df)} lignes  →  data/clean/synthese_budget_2024_2025.csv")
    print(df.to_string(index=False))
    return df


def extract_cst_plf2026():
    """
    Note-presentation_Fr.pdf — p.32
    Ressources des Comptes Spéciaux du Trésor : LF 2025 vs PLF 2026
    Unité source : dirhams → MMDH
    """
    print("\n[6/8] Comptes Spéciaux du Trésor (Note-presentation p.32)")
    tables = get_tables(RAW / "Note-presentation_Fr.pdf", 32)
    if not tables:
        print("  ⚠️  Aucun tableau trouvé")
        return pd.DataFrame()

    t = best_table(tables, min_cols=3)
    rows = []
    for row in t:
        label = str(row[0] or '').replace('\n', ' ').strip()
        if not label or 'Comptes' == label or 'Ressources' in label:
            continue
        lf2025  = clean_number(row[1] if len(row) > 1 else None)
        plf2026 = clean_number(row[2] if len(row) > 2 else None)
        var_pct = clean_number(row[3] if len(row) > 3 else None)
        rows.append({
            'designation':   label,
            'lf_2025_mmdh':  to_mmdh(lf2025),
            'plf_2026_mmdh': to_mmdh(plf2026),
            'variation_pct': var_pct,
            'source': 'Note-presentation_Fr p.32',
        })

    df = pd.DataFrame(rows)
    df = df[df['designation'].str.len() > 2]
    df.to_csv(CLEAN / "cst_plf2026.csv", index=False, encoding='utf-8-sig')
    print(f"  ✅ {len(df)} lignes  →  data/clean/cst_plf2026.csv")
    print(df[['designation', 'lf_2025_mmdh', 'plf_2026_mmdh']].to_string(index=False))
    return df


def extract_depenses_ministere_simple():
    """
    BCPLF2026.pdf — p.52-53-54
    Dépenses par ministère PLF 2026 : Personnel | Matériel | Investissement
    Unité source : dirhams → MMDH

    Pages 52-54 forment un seul tableau continu (coupé sur 3 pages).
    """
    print("\n[7/8] Dépenses par ministère PLF 2026 simple (BCPLF p.52-54)")
    path = RAW / "BCPLF2026.pdf"
    SKIP_LABELS = {'', 'Ordonnateur', 'Personnel', 'Matériel', 'Fonctionnement',
                   'Investissement', 'TOTAL'}

    all_rows = []
    for pg in [52, 53, 54]:
        tables = get_tables(path, pg)
        if not tables:
            print(f"  ⚠️  Page {pg} : aucun tableau")
            continue
        t = best_table(tables, min_cols=3)
        for row in t:
            label = str(row[0] or '').replace('\n', ' ').strip()
            if not label or len(label) < 3 or label in SKIP_LABELS:
                continue
            # Ignore header-like rows
            if any(h in label for h in ['Personnel', 'Matériel', 'Ordonnateur']):
                continue
            personnel = clean_number(row[1] if len(row) > 1 else None)
            materiel  = clean_number(row[2] if len(row) > 2 else None)
            invest    = clean_number(row[3] if len(row) > 3 else None)

            fonct = None
            if personnel is not None or materiel is not None:
                fonct = (personnel or 0) + (materiel or 0)

            all_rows.append({
                'ministere':             label,
                'personnel_mmdh':        to_mmdh(personnel),
                'materiel_mmdh':         to_mmdh(materiel),
                'fonctionnement_mmdh':   to_mmdh(fonct),
                'investissement_mmdh':   to_mmdh(invest),
                'source': f'BCPLF2026 p.{pg}',
            })

    df = pd.DataFrame(all_rows)
    df.to_csv(CLEAN / "depenses_ministere_plf2026_simple.csv", index=False, encoding='utf-8-sig')
    print(f"  ✅ {len(df)} lignes  →  data/clean/depenses_ministere_plf2026_simple.csv")
    print(df[['ministere', 'fonctionnement_mmdh', 'investissement_mmdh']].to_string(index=False))
    return df


def extract_depenses_ministere_detail():
    """
    Note-presentation_Fr.pdf — p.163-164
    Répartition par ministère : fonctionnement + investissement sur 3 années (2024/2025/2026)
    Structure : 16 colonnes
      0=Ordonnateur
      1-3 : Personnel (LF24 / LF25 / PLF26)
      4-6 : Matériel (LF24 / LF25 / PLF26)
      7-9 : Total fonctionnement (2024 / 2025 / PLF26)
      10-11 : Investissement CP+CE LF 2024
      12-13 : Investissement CP+CE LF 2025
      14-15 : Investissement CP+CE PLF 2026

    Extrait les colonnes PLF 2026 uniquement.
    Unité source : dirhams → MMDH
    """
    print("\n[8/8] Dépenses par ministère détail 2026 (Note-presentation p.163-164)")
    path = RAW / "Note-presentation_Fr.pdf"

    all_rows = []
    for pg in [163, 164]:
        tables = get_tables(path, pg)
        if not tables:
            continue
        t = max(tables, key=lambda x: len(x))

        for i, row in enumerate(t):
            if i < 3:          # 3 lignes d'en-tête fusionné
                continue
            if len(row) < 10:
                continue
            label = str(row[0] or '').replace('\n', ' ').strip()
            if not label or len(label) < 3:
                continue

            personnel_plf26   = clean_number(row[3])
            materiel_plf26    = clean_number(row[6])
            total_fonct_plf26 = clean_number(row[9])
            invest_cp_plf26   = clean_number(row[14]) if len(row) > 14 else None
            invest_ce_plf26   = clean_number(row[15]) if len(row) > 15 else None

            all_rows.append({
                'ministere':                 label,
                'personnel_plf2026_mmdh':    to_mmdh(personnel_plf26),
                'materiel_plf2026_mmdh':     to_mmdh(materiel_plf26),
                'fonctionnement_plf2026_mmdh': to_mmdh(total_fonct_plf26),
                'invest_cp_plf2026_mmdh':    to_mmdh(invest_cp_plf26),
                'invest_ce_plf2026_mmdh':    to_mmdh(invest_ce_plf26),
                'source': f'Note-presentation_Fr p.{pg}',
            })

    df = pd.DataFrame(all_rows)
    df.to_csv(CLEAN / "depenses_ministere_plf2026_detail.csv", index=False, encoding='utf-8-sig')
    print(f"  ✅ {len(df)} lignes  →  data/clean/depenses_ministere_plf2026_detail.csv")
    print(df[['ministere', 'fonctionnement_plf2026_mmdh', 'invest_cp_plf2026_mmdh']].to_string(index=False))
    return df


def extract_chiffres_cles():
    """
    BCPLF2026.pdf — p.14
    Chiffres clés PLF 2026 extraits du texte brut (données dans infographies).
    Recherche de patterns 'XXX MMDH' et labels associés.
    """
    print("\n[BONUS] Chiffres clés PLF 2026 texte brut (BCPLF p.14)")
    text = get_text(RAW / "BCPLF2026.pdf", 14)
    print(f"  Texte brut p.14 :\n{text}\n")

    # Patterns : chiffre suivi de MMDH avec label avant ou après
    pattern = r'([\d\s,\.]+)\s*MMDH'
    matches  = re.findall(pattern, text)
    rows = []
    for m in matches:
        val = clean_number(m)
        if val is not None:
            rows.append({'valeur_mmdh': val, 'source': 'BCPLF2026 p.14 (texte brut)'})

    df = pd.DataFrame(rows)
    df.to_csv(CLEAN / "chiffres_cles_plf2026.csv", index=False, encoding='utf-8-sig')
    print(f"  ✅ {len(df)} valeurs MMDH extraites")
    if not df.empty:
        print(df.to_string(index=False))
    return df


# ── Point d'entrée ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 65)
    print("  EXTRACTION BUDGÉTAIRE — MAROC PLF 2026")
    print("=" * 65)

    results = {
        "recettes_plf2026":              extract_recettes_plf2026(),
        "recettes_lf2024_2025":          extract_recettes_lf2024_2025(),
        "depenses_fonctionnement":       extract_depenses_fonctionnement(),
        "dette":                         extract_dette(),
        "synthese_budget":               extract_synthese_budget(),
        "cst_plf2026":                   extract_cst_plf2026(),
        "depenses_ministere_simple":     extract_depenses_ministere_simple(),
        "depenses_ministere_detail":     extract_depenses_ministere_detail(),
        "chiffres_cles":                 extract_chiffres_cles(),
    }

    print("\n" + "=" * 65)
    print("  RÉCAPITULATIF")
    print("=" * 65)
    total = 0
    for name, df in results.items():
        n = len(df)
        total += n
        status = "✅" if n > 0 else "⚠️ "
        print(f"  {status}  {name:<40s}  {n:3d} lignes")
    print(f"\n  Total : {total} lignes extraites dans data/clean/")
