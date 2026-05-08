#!/usr/bin/env python3
"""
04_sankey.py — Figure Plotly Sankey à partir de data/models/sankey_data.json

Inputs :
  - data/models/sankey_data.json   (produit par 03_model.py, schema 1.0)

Outputs :
  - data/models/sankey_figure.json   (JSON Plotly pour react-plotly.js)
  - data/models/sankey_preview.html  (preview HTML standalone, plotly via CDN)

Palette éditoriale :
  - Recettes fiscales       → #2E8B57   (vert profond)
  - Recettes non fiscales   → #5CAB7D   (vert clair)
  - Autres recettes         → #A4C2A5   (vert pâle, regroupement <2%)
  - Emprunts                → #C0504D   (rouge atténué — signal "dette")
  - Budget Général (hub)    → #1F4E79   (bleu profond)
  - Fonctionnement          → #E07B00   (orange foncé)
  - Investissement          → #F2A33A   (orange clair)

Hover : "{label} : {valeur} MMDH ({pct}%)".

Codes de sortie :
  0 — succès
  1 — erreur d'environnement (JSON source manquant, schema incompatible)
"""

import json
import sys
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timezone

BASE        = Path(__file__).resolve().parent.parent
MODELS      = BASE / "data" / "models"
SANKEY_DATA = MODELS / "sankey_data.json"
SANKEY_FIG  = MODELS / "sankey_figure.json"
SANKEY_HTML = MODELS / "sankey_preview.html"

EXPECTED_SCHEMA = "1.0"

# ── Palette éditoriale ────────────────────────────────────────────────────────
COLOR_RECETTE_FISC    = "#2E8B57"
COLOR_RECETTE_NONFISC = "#5CAB7D"
COLOR_RECETTE_AUTRES  = "#A4C2A5"
COLOR_EMPRUNTS        = "#C0504D"
COLOR_BUDGET          = "#1F4E79"
COLOR_DEPENSE_FONCT   = "#E07B00"
COLOR_DEPENSE_INVEST  = "#F2A33A"
COLOR_FALLBACK        = "#888888"

LINK_OPACITY = 0.45   # transparence des flux pour lisibilité du hub

FONT_FAMILY = "Inter, Helvetica, Arial, sans-serif"


# ── Helpers ───────────────────────────────────────────────────────────────────

def hex_to_rgba(hx, alpha=LINK_OPACITY):
    h = hx.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def color_for_node(node):
    kind = node.get("kind")
    cat  = node.get("categorie")
    if kind == "hub":
        return COLOR_BUDGET
    if kind == "source":
        if cat == "recettes_fiscales":
            return COLOR_RECETTE_FISC
        if cat == "recettes_non_fiscales":
            return COLOR_RECETTE_NONFISC
        if cat == "recettes_autres":
            return COLOR_RECETTE_AUTRES
        if cat == "emprunts":
            return COLOR_EMPRUNTS
        return COLOR_RECETTE_FISC
    if kind == "destination":
        if cat == "fonctionnement":
            return COLOR_DEPENSE_FONCT
        if cat == "investissement":
            return COLOR_DEPENSE_INVEST
        return COLOR_DEPENSE_FONCT
    return COLOR_FALLBACK


def short_node_label(name, max_len=44):
    """Raccourcit les libellés (et retire le préfixe 'N - ' des recettes)."""
    name = str(name).strip()
    if len(name) > 4 and name[0].isdigit() and " - " in name[:6]:
        name = name.split(" - ", 1)[1]
    if len(name) <= max_len:
        return name
    return name[: max_len - 1].rstrip() + "…"


def load_sankey_data():
    if not SANKEY_DATA.exists():
        print(f"❌ Fichier introuvable : {SANKEY_DATA}", file=sys.stderr)
        print("   → Lancer d'abord : python scripts/03_model.py", file=sys.stderr)
        sys.exit(1)
    with SANKEY_DATA.open(encoding="utf-8") as f:
        data = json.load(f)
    sv = data.get("schema_version")
    if sv != EXPECTED_SCHEMA:
        print(f"❌ Schema incompatible : attendu '{EXPECTED_SCHEMA}', obtenu '{sv}'",
              file=sys.stderr)
        sys.exit(1)
    if "nodes" not in data or "links" not in data:
        print("❌ JSON malformé : 'nodes' ou 'links' manquant.", file=sys.stderr)
        sys.exit(1)
    return data


# ── Construction figure ───────────────────────────────────────────────────────

def build_figure(data):
    nodes = data["nodes"]
    links = data["links"]
    total = float(data["totals"]["budget_general"])

    node_colors = [color_for_node(n) for n in nodes]
    node_labels = [short_node_label(n["name"]) for n in nodes]
    node_full   = [str(n["name"]) for n in nodes]
    node_values = [float(n.get("value", 0.0)) for n in nodes]
    node_pcts   = [(v / total * 100.0) if total else 0.0 for v in node_values]
    node_customdata = [
        [full, val, pct]
        for full, val, pct in zip(node_full, node_values, node_pcts)
    ]
    node_hover = (
        "<b>%{customdata[0]}</b><br>"
        "Valeur : %{customdata[1]:.2f} MMDH<br>"
        "Part : %{customdata[2]:.2f} %"
        "<extra></extra>"
    )

    src_idx = [int(lk["source"]) for lk in links]
    tgt_idx = [int(lk["target"]) for lk in links]
    values  = [float(lk["value"]) for lk in links]
    link_pcts = [(v / total * 100.0) if total else 0.0 for v in values]
    link_colors = [hex_to_rgba(node_colors[s]) for s in src_idx]
    link_customdata = [
        [node_full[s], node_full[t], v, p]
        for s, t, v, p in zip(src_idx, tgt_idx, values, link_pcts)
    ]
    link_hover = (
        "<b>%{customdata[0]} → %{customdata[1]}</b><br>"
        "Valeur : %{customdata[2]:.2f} MMDH<br>"
        "Part : %{customdata[3]:.2f} %"
        "<extra></extra>"
    )

    sankey = go.Sankey(
        arrangement="snap",
        valueformat=".2f",
        valuesuffix=" MMDH",
        node=dict(
            pad=20,
            thickness=22,
            line=dict(color="#1A1A1A", width=0.5),
            label=node_labels,
            color=node_colors,
            customdata=node_customdata,
            hovertemplate=node_hover,
        ),
        link=dict(
            source=src_idx,
            target=tgt_idx,
            value=values,
            color=link_colors,
            customdata=link_customdata,
            hovertemplate=link_hover,
        ),
    )

    fig = go.Figure(data=[sankey])

    anchors  = data["totals"]
    rec_anch = anchors.get("recettes_ordinaires_ancrage", anchors.get("recettes_ordinaires_brutes"))
    emp_anch = anchors.get("emprunts_derives")

    title_html = (
        "<b>PLF 2026 — De la recette à la dépense</b>"
        "<br><span style='font-size:13px;color:#555;font-weight:400;'>"
        f"Budget Général {total:.2f} MMDH · "
        f"Recettes ordinaires {rec_anch:.2f} MMDH · "
        f"Emprunts {emp_anch:.2f} MMDH"
        "</span>"
    )

    cons_delta = data.get("meta", {}).get("conservation_delta", 0.0)
    eps        = data.get("meta", {}).get("epsilon_mmdh", 0.1)

    fig.update_layout(
        title=dict(
            text=title_html,
            x=0.02, xanchor="left",
            y=0.97, yanchor="top",
            font=dict(family=FONT_FAMILY, size=20, color="#111"),
        ),
        font=dict(family=FONT_FAMILY, size=13, color="#222"),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        margin=dict(l=18, r=18, t=92, b=78),
        height=640,
        annotations=[
            dict(
                xref="paper", yref="paper",
                x=0.0, y=-0.09,
                xanchor="left", yanchor="top",
                showarrow=False,
                align="left",
                font=dict(family=FONT_FAMILY, size=11, color="#666"),
                text=(
                    "Source : PLF 2026 — Note de présentation MEF, BCPLF2026 p.14. "
                    f"Conservation Σ entrées ≈ Σ sorties (Δ={cons_delta:.4f} MMDH, ε={eps}). "
                    "Recettes <2% regroupées dans « Autres recettes »."
                ),
            )
        ],
    )
    return fig


# ── Export ────────────────────────────────────────────────────────────────────

def export(fig):
    SANKEY_FIG.write_text(fig.to_json(), encoding="utf-8")
    fig.write_html(
        str(SANKEY_HTML),
        include_plotlyjs="cdn",
        full_html=True,
        config={"displaylogo": False, "responsive": True},
    )


def main():
    print("=" * 72)
    print("  PLOTLY SANKEY — MAROC PLF 2026")
    print("=" * 72)

    if not MODELS.exists():
        MODELS.mkdir(parents=True, exist_ok=True)

    data = load_sankey_data()
    print(f"  ✅ {SANKEY_DATA.name} chargé "
          f"(schema {data['schema_version']}, "
          f"{len(data['nodes'])} nodes, {len(data['links'])} links)")

    fig = build_figure(data)
    export(fig)

    print()
    print("  ── Sorties ──")
    print(f"    {SANKEY_FIG.relative_to(BASE)}  "
          f"({SANKEY_FIG.stat().st_size:,} B)")
    print(f"    {SANKEY_HTML.relative_to(BASE)}  "
          f"({SANKEY_HTML.stat().st_size:,} B)")
    print()
    print(f"  Généré le : {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print("=" * 72)


if __name__ == "__main__":
    main()
