#!/usr/bin/env python3
"""
03_model.py — Génère sankey_data.json + treemap_data.json (PLF 2026)

Lit 4 CSVs nettoyés produits par 02_clean.py (data/clean/) :
  - recettes_plf2026_clean.csv
  - depenses_ministere_plf2026_clean.csv
  - dette_clean.csv                   (informationnel — millésime LF 2025)
  - chiffres_cles_plf2026_enrichi.csv (ancrages 421.33 / 527.65)

Construit deux modèles JSON (data/models/) :
  - sankey_data.json   — Recettes (par type) + Emprunts → Budget Général
                         → Dépenses (par catégorie). Max 12 nodes/couche,
                         regroupement <2% dans "Autres recettes".
  - treemap_data.json  — Hiérarchie 3 niveaux : Dépenses → secteur → ministère.
                         Valeurs MMDH + part_pct (sur 100 DH).

Validations (ε=0.1) :
  2.4 — Σ inputs Budget ≈ Σ outputs Budget (conservation Sankey)
  2.5 — Σ feuilles Treemap == racine

Sorties annexes : rapport de validation lisible sur stdout.

Codes de sortie :
  0 — succès
  1 — erreur d'environnement (CSV source manquant, dossier introuvable)
  2 — anomalie critique (couche >12 nodes, conservation rompue, profondeur >3)
"""

import json
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

BASE   = Path(__file__).resolve().parent.parent
CLEAN  = BASE / "data" / "clean"
MODELS = BASE / "data" / "models"

# ── Constantes du modèle ──────────────────────────────────────────────────────

SCHEMA_VERSION       = "1.0"
EPSILON_MMDH         = 0.1     # tolérance conservation des flux
THRESHOLD_PCT        = 2.0     # <2% → regroupé dans "Autres"
MAX_NODES_PER_LAYER  = 12      # contrainte Sankey
MAX_TREEMAP_LEVELS   = 3       # racine + secteur + ministère

# Ancrages éditoriaux (BCPLF2026 p.14) — invariants projet.
CIBLE_RECETTES_MMDH  = 421.33
CIBLE_DEPENSES_MMDH  = 527.65
TOLERANCE_ANCHOR     = 0.5     # tolérance d'écart vs ancrage officiel

REQUIRED_CSV = [
    "recettes_plf2026_clean.csv",
    "depenses_ministere_plf2026_clean.csv",
    "dette_clean.csv",
    "chiffres_cles_plf2026_enrichi.csv",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def safe_num(x):
    return float(x) if pd.notna(x) else 0.0


def short_label(s, max_len=70):
    s = str(s).strip()
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def round_mmdh(x, n=4):
    return round(float(x), n)


# ── Chargement ────────────────────────────────────────────────────────────────

def load_clean_csvs():
    """2.1 — Lit les 4 CSVs nettoyés. Halt en cas de manquant."""
    sources = {}
    missing = []
    for name in REQUIRED_CSV:
        p = CLEAN / name
        if not p.exists():
            missing.append(name)
            continue
        sources[name] = pd.read_csv(p)
    if missing:
        print(f"❌ Fichiers introuvables dans {CLEAN} : {missing}",
              file=sys.stderr)
        sys.exit(1)
    return sources


def get_anchor(ck_df, label, default):
    """Lit une valeur d'ancrage depuis chiffres_cles_plf2026_enrichi.csv."""
    rows = ck_df[ck_df["label"] == label]
    if rows.empty:
        return float(default)
    return float(rows["valeur_mmdh"].iloc[0])


# ── Sankey (2.2) ──────────────────────────────────────────────────────────────

def build_sankey(rec_df, dep_df, ck_df):
    """
    Construit le modèle Sankey équilibré :
      Sources  : 9 recettes ordinaires + Emprunts (déficit dérivé)
      Hub      : Budget Général
      Targets  : 2 catégories de dépenses (Fonctionnement, Investissement)
    Les valeurs côté Sources et Targets sont normalisées sur l'ancrage
    officiel `depenses_total_plf2026` (527.65 MMDH) — ce qui garantit
    la conservation parfaite et l'alignement narratif.
    """
    # Ancrages officiels
    target_recettes = get_anchor(ck_df, "recettes_total_plf2026",
                                 CIBLE_RECETTES_MMDH)
    target_depenses = get_anchor(ck_df, "depenses_total_plf2026",
                                 CIBLE_DEPENSES_MMDH)

    # ── Source layer : recettes ordinaires (PLF 2026, hors total) ──
    rec = rec_df.loc[~rec_df["is_total"]].copy()
    rec_sum = float(rec["plf_2026_mmdh"].sum())  # ≈ 421.33
    if abs(rec_sum - target_recettes) > TOLERANCE_ANCHOR:
        print(f"⚠️  Σ recettes brutes ({rec_sum:.4f}) "
              f"≠ ancrage ({target_recettes}) "
              f"au-delà de la tolérance ±{TOLERANCE_ANCHOR}",
              file=sys.stderr)

    rec_records = []
    for _, r in rec.iterrows():
        val = float(r["plf_2026_mmdh"])
        rec_records.append({
            "label":     str(r["designation"]),
            "categorie": r["categorie"] if pd.notna(r["categorie"]) else "autre",
            "value":     val,
            "pct_total": val / target_depenses * 100.0,
        })

    # Regroupement <2% dans "Autres recettes"
    kept   = [x for x in rec_records if x["pct_total"] >= THRESHOLD_PCT]
    others = [x for x in rec_records if x["pct_total"] < THRESHOLD_PCT]

    sources = []
    for x in kept:
        sources.append({
            "name":      x["label"],
            "categorie": x["categorie"],
            "value":     round_mmdh(x["value"]),
        })
    if others:
        sources.append({
            "name":           "Autres recettes",
            "categorie":      "recettes_autres",
            "value":          round_mmdh(sum(x["value"] for x in others)),
            "children_count": len(others),
            "children":       [
                {"label": x["label"],
                 "value": round_mmdh(x["value"]),
                 "pct_total": round(x["pct_total"], 4)}
                for x in others
            ],
        })

    # Emprunts = déficit dérivé (toujours > 2% en pratique → jamais regroupé)
    emprunts = round_mmdh(target_depenses - target_recettes)
    sources.append({
        "name":      "Emprunts",
        "categorie": "emprunts",
        "value":     emprunts,
    })

    # ── Target layer : dépenses par catégorie ──
    # On part des totaux de fonctionnement et d'investissement réellement
    # extraits des données ministérielles (PLF 2026) puis on normalise sur
    # `target_depenses` pour garantir Σ inputs = Σ outputs sur l'ancrage.
    dep = dep_df.loc[~dep_df["is_total"]].copy()
    fonct_raw = float(dep["fonctionnement_mmdh"].fillna(0).sum())
    inv_raw   = float(dep["invest_total_mmdh"].fillna(0).sum())
    raw_total = fonct_raw + inv_raw
    if raw_total <= 0:
        print("❌ Total dépenses ministérielles nul — Sankey impossible",
              file=sys.stderr)
        sys.exit(2)

    scale = target_depenses / raw_total
    fonct_val = round_mmdh(fonct_raw * scale)
    inv_val   = round_mmdh(inv_raw   * scale)
    # Correction de l'arrondi pour conservation exacte
    delta = round_mmdh(target_depenses - (fonct_val + inv_val))
    inv_val = round_mmdh(inv_val + delta)

    destinations = [
        {"name": "Fonctionnement", "categorie": "fonctionnement", "value": fonct_val},
        {"name": "Investissement", "categorie": "investissement", "value": inv_val},
    ]

    # ── Construction nodes/links ──
    nodes = []

    def add_node(name, kind, **extra):
        idx = len(nodes)
        nodes.append({"index": idx, "name": name, "kind": kind, **extra})
        return idx

    src_indices = []
    for s in sources:
        idx = add_node(s["name"], "source",
                       categorie=s["categorie"],
                       value=s["value"])
        src_indices.append((idx, s["value"]))

    budget_idx = add_node("Budget Général", "hub",
                          value=round_mmdh(target_depenses))

    dst_indices = []
    for d in destinations:
        idx = add_node(d["name"], "destination",
                       categorie=d["categorie"],
                       value=d["value"])
        dst_indices.append((idx, d["value"]))

    links = []
    for src_idx, val in src_indices:
        links.append({"source": src_idx, "target": budget_idx,
                      "value": round_mmdh(val)})
    for dst_idx, val in dst_indices:
        links.append({"source": budget_idx, "target": dst_idx,
                      "value": round_mmdh(val)})

    # ── Validations Sankey ──
    layer_counts = {
        "sources":      len(src_indices),
        "hub":          1,
        "destinations": len(dst_indices),
    }
    over = {k: v for k, v in layer_counts.items() if v > MAX_NODES_PER_LAYER}
    if over:
        print(f"❌ Couche dépasse {MAX_NODES_PER_LAYER} nodes : {over}",
              file=sys.stderr)
        sys.exit(2)

    sum_in  = round_mmdh(sum(lk["value"] for lk in links if lk["target"] == budget_idx))
    sum_out = round_mmdh(sum(lk["value"] for lk in links if lk["source"] == budget_idx))
    delta_flux = abs(sum_in - sum_out)
    if delta_flux > EPSILON_MMDH:
        print(f"❌ Conservation Sankey rompue : "
              f"entrées={sum_in} sorties={sum_out} Δ={delta_flux} (ε={EPSILON_MMDH})",
              file=sys.stderr)
        sys.exit(2)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at":   datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "unit":           "MMDH",
        "totals": {
            "recettes_ordinaires_brutes":   round_mmdh(rec_sum),
            "recettes_ordinaires_ancrage":  round_mmdh(target_recettes),
            "emprunts_derives":             emprunts,
            "budget_general":               round_mmdh(target_depenses),
            "depenses_total":               round_mmdh(target_depenses),
        },
        "nodes": nodes,
        "links": links,
        "meta": {
            "layer_counts":          layer_counts,
            "threshold_pct":         THRESHOLD_PCT,
            "epsilon_mmdh":          EPSILON_MMDH,
            "sum_inputs_budget":     sum_in,
            "sum_outputs_budget":    sum_out,
            "conservation_delta":    round_mmdh(delta_flux),
            "autres_recettes_count": len(others),
            "scale_destinations":    round(scale, 6),
            "raw_ministry_total":    round_mmdh(raw_total),
            "raw_fonctionnement":   round_mmdh(fonct_raw),
            "raw_investissement":   round_mmdh(inv_raw),
            "anchors": {
                "recettes_total_plf2026": round_mmdh(target_recettes),
                "depenses_total_plf2026": round_mmdh(target_depenses),
                "source": "BCPLF2026 p.14 (chiffres_cles_plf2026_enrichi.csv)",
            },
        },
    }


# ── Treemap (2.3) ─────────────────────────────────────────────────────────────

def build_treemap(dep_df):
    """
    Hiérarchie : Dépenses publiques (racine) → secteur → ministère.
    Valeurs en MMDH ; pct_dh = part sur 100 DH dépensés (= % du total).
    Profondeur stricte = 3 niveaux.
    """
    dep = dep_df.loc[~dep_df["is_total"]].copy()
    dep["fonct"]  = dep["fonctionnement_mmdh"].fillna(0).astype(float)
    dep["invest"] = dep["invest_total_mmdh"].fillna(0).astype(float)
    dep["total"]  = dep["fonct"] + dep["invest"]
    dep = dep[dep["total"] > 0].copy()
    dep["secteur"] = dep["secteur"].fillna("Autre").replace("", "Autre")

    grand_total = float(dep["total"].sum())
    if grand_total <= 0:
        print("❌ Treemap : grand total nul.", file=sys.stderr)
        sys.exit(2)

    root = {
        "name":   "Dépenses publiques",
        "value":  round_mmdh(grand_total),
        "pct_dh": 100.0,
        "level":  0,
        "children": [],
    }

    secteurs = (
        dep.groupby("secteur", dropna=False)["total"]
           .sum().reset_index()
           .sort_values("total", ascending=False)
    )

    for _, sec_row in secteurs.iterrows():
        sec_name  = str(sec_row["secteur"])
        sec_total = float(sec_row["total"])
        sec_node = {
            "name":   sec_name,
            "value":  round_mmdh(sec_total),
            "pct_dh": round(sec_total / grand_total * 100.0, 4),
            "level":  1,
            "children": [],
        }
        sec_min = (
            dep[dep["secteur"] == sec_name]
            .sort_values("total", ascending=False)
        )
        for _, m in sec_min.iterrows():
            min_name  = str(m["ministere"])
            min_total = float(m["total"])
            sec_node["children"].append({
                "name":           min_name,
                "short_name":     short_label(min_name, 70),
                "value":          round_mmdh(min_total),
                "pct_dh":         round(min_total / grand_total * 100.0, 4),
                "pct_secteur":    round(min_total / sec_total   * 100.0, 4),
                "level":          2,
                "fonctionnement": round_mmdh(m["fonct"]),
                "investissement": round_mmdh(m["invest"]),
            })
        root["children"].append(sec_node)

    # Validation 2.5 — conservation Σ feuilles == racine
    leaves_sum = sum(
        c["value"] for sec in root["children"] for c in sec["children"]
    )
    delta = abs(round_mmdh(leaves_sum) - round_mmdh(root["value"]))
    if delta > EPSILON_MMDH:
        print(f"❌ Treemap : Σ feuilles ({leaves_sum:.4f}) ≠ racine "
              f"({root['value']:.4f}) Δ={delta:.4f} (ε={EPSILON_MMDH})",
              file=sys.stderr)
        sys.exit(2)

    # Validation profondeur ≤ 3 niveaux
    def max_depth(node, current=1):
        if not node.get("children"):
            return current
        return max(max_depth(c, current + 1) for c in node["children"])

    depth_levels = max_depth(root)
    if depth_levels > MAX_TREEMAP_LEVELS:
        print(f"❌ Treemap : profondeur {depth_levels} > "
              f"{MAX_TREEMAP_LEVELS} niveaux", file=sys.stderr)
        sys.exit(2)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at":   datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "unit":           "MMDH",
        "pct_base":       "pct_dh = part sur 100 DH dépensés (= % du total)",
        "root":           root,
        "meta": {
            "n_secteurs":     len(root["children"]),
            "n_ministeres":   sum(len(s["children"]) for s in root["children"]),
            "depth_levels":   depth_levels,
            "max_levels":     MAX_TREEMAP_LEVELS,
            "total_mmdh":     round_mmdh(grand_total),
            "leaves_sum":     round_mmdh(leaves_sum),
            "epsilon_mmdh":   EPSILON_MMDH,
            "conservation_delta": round_mmdh(delta),
        },
    }


# ── Rapport (2.7) ─────────────────────────────────────────────────────────────

def report(sankey, treemap, dette_df):
    print()
    print("=" * 72)
    print("  RAPPORT DE VALIDATION — 03_model.py")
    print("=" * 72)

    print()
    print("  ── SANKEY ──")
    s_meta = sankey["meta"]
    s_tot  = sankey["totals"]
    print(f"    Schema version           : {sankey['schema_version']}")
    print(f"    Couches                  : {s_meta['layer_counts']} "
          f"(max {MAX_NODES_PER_LAYER}/couche)")
    print(f"    Recettes ordinaires      : {s_tot['recettes_ordinaires_brutes']:>10.4f} MMDH "
          f"(ancrage {s_tot['recettes_ordinaires_ancrage']})")
    print(f"    Emprunts dérivés         : {s_tot['emprunts_derives']:>10.4f} MMDH "
          f"(= dépenses − recettes ancrées)")
    print(f"    Budget Général           : {s_tot['budget_general']:>10.4f} MMDH")
    print(f"    Σ entrées Budget         : {s_meta['sum_inputs_budget']:>10.4f} MMDH")
    print(f"    Σ sorties Budget         : {s_meta['sum_outputs_budget']:>10.4f} MMDH")
    print(f"    Δ conservation           : {s_meta['conservation_delta']:>10.4f} MMDH "
          f"(ε={EPSILON_MMDH})")
    cons_ok = s_meta["conservation_delta"] <= EPSILON_MMDH
    print(f"    Conservation flux        : {'✅' if cons_ok else '❌'}")
    print(f"    Recettes <2% regroupées  : {s_meta['autres_recettes_count']} lignes "
          f"→ 'Autres recettes'")
    print(f"    Brut ministériel         : {s_meta['raw_ministry_total']:>10.4f} MMDH "
          f"(fonct={s_meta['raw_fonctionnement']} + invest={s_meta['raw_investissement']})")
    print(f"    Facteur normalisation    : ×{s_meta['scale_destinations']:.6f} "
          f"(brut → ancrage 527.65)")

    print()
    print("  ── TREEMAP ──")
    t_meta = treemap["meta"]
    print(f"    Schema version           : {treemap['schema_version']}")
    print(f"    Profondeur               : {t_meta['depth_levels']} niveaux "
          f"(max {t_meta['max_levels']})")
    print(f"    Secteurs                 : {t_meta['n_secteurs']}")
    print(f"    Ministères (feuilles)    : {t_meta['n_ministeres']}")
    print(f"    Total racine             : {t_meta['total_mmdh']:>10.4f} MMDH")
    print(f"    Σ feuilles               : {t_meta['leaves_sum']:>10.4f} MMDH")
    print(f"    Δ conservation           : {t_meta['conservation_delta']:>10.4f} MMDH "
          f"(ε={EPSILON_MMDH})")
    leaf_ok = t_meta["conservation_delta"] <= EPSILON_MMDH
    print(f"    Conservation hiérarchie  : {'✅' if leaf_ok else '❌'}")

    print()
    print("  ── Dette publique (informationnel) ──")
    d_total = dette_df.loc[dette_df["is_total"], "lf_2025_mmdh"]
    if not d_total.empty:
        print(f"    Charges dette LF 2025    : {float(d_total.iloc[0]):>10.4f} MMDH "
              f"(non utilisée — pas de série PLF 2026 explicite)")
    else:
        print("    Charges dette LF 2025    : indisponible")

    print()
    print("  ── Sorties data/models/ ──")
    print("    sankey_data.json")
    print("    treemap_data.json")
    print("=" * 72)


# ── Point d'entrée ────────────────────────────────────────────────────────────

def main():
    if not CLEAN.exists():
        print(f"❌ Dossier introuvable : {CLEAN}", file=sys.stderr)
        sys.exit(1)
    MODELS.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print("  MODÉLISATION SANKEY + TREEMAP — MAROC PLF 2026")
    print("=" * 72)

    sources = load_clean_csvs()
    print(f"  ✅ {len(sources)} CSV nettoyés chargés depuis data/clean/")

    rec_df   = sources["recettes_plf2026_clean.csv"]
    dep_df   = sources["depenses_ministere_plf2026_clean.csv"]
    dette_df = sources["dette_clean.csv"]
    ck_df    = sources["chiffres_cles_plf2026_enrichi.csv"]

    sankey  = build_sankey(rec_df, dep_df, ck_df)
    treemap = build_treemap(dep_df)

    sankey_path  = MODELS / "sankey_data.json"
    treemap_path = MODELS / "treemap_data.json"
    sankey_path.write_text(
        json.dumps(sankey, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    treemap_path.write_text(
        json.dumps(treemap, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report(sankey, treemap, dette_df)


if __name__ == "__main__":
    main()
