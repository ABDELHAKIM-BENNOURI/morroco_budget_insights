#!/usr/bin/env python3
"""
05_treemap.py — Figure Plotly Treemap à partir de data/models/treemap_data.json

Inputs :
  - data/models/treemap_data.json   (produit par 03_model.py, schema 1.0)

Outputs :
  - data/models/treemap_figure.json   (JSON Plotly pour react-plotly.js)
  - data/models/treemap_preview.html  (preview HTML standalone, plotly via CDN)

Hiérarchie aplatie : Dépenses publiques → secteur → ministère.
Palette dégradée par secteur (chaque ministère reçoit une teinte du secteur,
plus claire à mesure qu'il pèse moins → contraste préservé sur le top).

Hover : "<b>{label}</b> : {valeur} MMDH = {x} DH sur 100 DH"
        (+ part dans le secteur pour les feuilles)

Codes de sortie :
  0 — succès
  1 — erreur d'environnement (JSON source manquant, schema incompatible)
"""

import json
import sys
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timezone

BASE         = Path(__file__).resolve().parent.parent
MODELS       = BASE / "data" / "models"
TREEMAP_DATA = MODELS / "treemap_data.json"
TREEMAP_FIG  = MODELS / "treemap_figure.json"
TREEMAP_HTML = MODELS / "treemap_preview.html"

EXPECTED_SCHEMA = "1.0"

# ── Palette par secteur (couleur de base) ─────────────────────────────────────
SECTEUR_COLOR = {
    "Social":       "#1F77B4",   # bleu
    "Souveraineté": "#C0504D",   # rouge atténué (cohérence Sankey emprunts)
    "Économique":   "#2CA02C",   # vert
    "Infra":        "#6A4C93",   # violet
    "Autre":        "#7F7F7F",   # gris
}
ROOT_COLOR     = "#2C3E50"       # bleu nuit pour la racine
FALLBACK_COLOR = "#888888"

# Plage du dégradé : 0 = couleur pure, 0.55 = blanchi à 55 %
MIN_LIGHTEN = 0.00
MAX_LIGHTEN = 0.55

FONT_FAMILY = "Inter, Helvetica, Arial, sans-serif"


# ── Helpers couleurs ──────────────────────────────────────────────────────────

def hex_to_rgb(hx):
    h = hx.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_hex(r, g, b):
    return f"#{r:02X}{g:02X}{b:02X}"


def lighten(base_hex, factor):
    """factor ∈ [0,1] : 0 = couleur pure, 1 = blanc."""
    factor = max(0.0, min(1.0, factor))
    r, g, b = hex_to_rgb(base_hex)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return rgb_to_hex(r, g, b)


# ── Chargement ────────────────────────────────────────────────────────────────

def load_treemap_data():
    if not TREEMAP_DATA.exists():
        print(f"❌ Fichier introuvable : {TREEMAP_DATA}", file=sys.stderr)
        print("   → Lancer d'abord : python scripts/03_model.py", file=sys.stderr)
        sys.exit(1)
    with TREEMAP_DATA.open(encoding="utf-8") as f:
        data = json.load(f)
    sv = data.get("schema_version")
    if sv != EXPECTED_SCHEMA:
        print(f"❌ Schema incompatible : attendu '{EXPECTED_SCHEMA}', obtenu '{sv}'",
              file=sys.stderr)
        sys.exit(1)
    if "root" not in data:
        print("❌ JSON malformé : 'root' manquant.", file=sys.stderr)
        sys.exit(1)
    return data


# ── Aplatissement de l'arbre (4.2) ────────────────────────────────────────────

def short_label(s, max_len=46):
    s = str(s).strip()
    # Supprime préfixe "MINISTERE [DE LA/DU/DES/DELEGUE...] " pour gagner en lisibilité
    prefixes = (
        "MINISTERE DELEGUE AUPRES DU CHEF DU GOUVERNEMENT CHARGE DE LA ",
        "MINISTERE DELEGUE AUPRES DU CHEF DU GOUVERNEMENT CHARGE DE L'",
        "MINISTERE DELEGUE AUPRES DU CHEF DU GOUVERNEMENT CHARGE DES ",
        "MINISTERE DELEGUE AUPRES DU CHEF DU GOUVERNEMENT CHARGE DU ",
        "MINISTERE DE LA ",
        "MINISTERE DE L'",
        "MINISTERE DES ",
        "MINISTERE DU ",
        "MINISTERE ",
    )
    for p in prefixes:
        if s.startswith(p):
            s = s[len(p):]
            break
    if len(s) <= max_len:
        return s
    return s[: max_len - 1].rstrip() + "…"


def flatten_tree(root):
    """
    Aplatit la hiérarchie en 6 listes parallèles :
        ids, labels, parents, values, secteurs, customdata.
    Conformité Plotly Treemap : `parents` référence des `ids` (pas des labels).
    """
    ids       = []
    labels    = []
    parents   = []
    values    = []
    secteurs  = []
    customdata = []

    # --- Niveau 0 : racine
    root_id = root["name"]
    ids.append(root_id)
    labels.append(root["name"])
    parents.append("")
    values.append(float(root["value"]))
    secteurs.append(None)
    customdata.append([
        root["name"],
        float(root["value"]),
        float(root["pct_dh"]),
        "",   # pas de précision « % du secteur »
    ])

    # --- Niveau 1 : secteurs
    for sec in root.get("children", []):
        sec_name = sec["name"]
        sec_id   = f"{root_id} ▸ {sec_name}"
        ids.append(sec_id)
        labels.append(sec_name)
        parents.append(root_id)
        values.append(float(sec["value"]))
        secteurs.append(sec_name)
        customdata.append([
            sec_name,
            float(sec["value"]),
            float(sec["pct_dh"]),
            "",
        ])

        # --- Niveau 2 : ministères
        for m in sec.get("children", []):
            min_name = m["name"]
            min_id   = f"{sec_id} ▸ {min_name}"
            ids.append(min_id)
            labels.append(short_label(min_name))
            parents.append(sec_id)
            values.append(float(m["value"]))
            secteurs.append(sec_name)
            customdata.append([
                min_name,                        # nom complet pour hover
                float(m["value"]),
                float(m["pct_dh"]),
                f"{float(m['pct_secteur']):.2f} % du secteur {sec_name}",
            ])

    return ids, labels, parents, values, secteurs, customdata


# ── Couleurs (4.5 — palette dégradée par secteur) ─────────────────────────────

def assign_colors(root, ids, secteurs):
    """
    - Racine        → ROOT_COLOR
    - Secteur       → couleur pure de SECTEUR_COLOR
    - Ministère     → teinte du secteur, plus claire selon le rang (par valeur)
    """
    # Pré-calcul du rang des ministères par secteur (0 = plus gros)
    rank_by_id = {}
    for sec in root.get("children", []):
        children = sorted(
            sec.get("children", []),
            key=lambda c: float(c["value"]),
            reverse=True,
        )
        n = max(len(children) - 1, 1)
        for rank, m in enumerate(children):
            min_id = f"{root['name']} ▸ {sec['name']} ▸ {m['name']}"
            rank_by_id[min_id] = (rank, n, sec["name"])

    colors = []
    for node_id, sec_name in zip(ids, secteurs):
        if sec_name is None:
            colors.append(ROOT_COLOR)
            continue
        if node_id in rank_by_id:
            rank, n, sec = rank_by_id[node_id]
            base = SECTEUR_COLOR.get(sec, FALLBACK_COLOR)
            factor = MIN_LIGHTEN + (rank / n) * (MAX_LIGHTEN - MIN_LIGHTEN)
            colors.append(lighten(base, factor))
        else:
            # Niveau secteur : couleur pure
            colors.append(SECTEUR_COLOR.get(sec_name, FALLBACK_COLOR))
    return colors


# ── Construction figure (4.3 / 4.4) ───────────────────────────────────────────

def build_figure(data):
    root = data["root"]
    ids, labels, parents, values, secteurs, customdata = flatten_tree(root)
    colors = assign_colors(root, ids, secteurs)

    # Hover (4.4) — applique à tous les niveaux
    hover_tpl = (
        "<b>%{customdata[0]}</b><br>"
        "Valeur : %{customdata[1]:.2f} MMDH<br>"
        "= %{customdata[2]:.2f} DH sur 100 DH"
        "<br>%{customdata[3]}"
        "<extra></extra>"
    )

    treemap = go.Treemap(
        branchvalues="total",
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        customdata=customdata,
        hovertemplate=hover_tpl,
        marker=dict(
            colors=colors,
            line=dict(width=1, color="#FFFFFF"),
        ),
        pathbar=dict(visible=True, side="top", thickness=22),
        tiling=dict(packing="squarify", squarifyratio=1.4),
        textinfo="label+value+percent root",
        texttemplate=(
            "<b>%{label}</b><br>"
            "%{value:.1f} MMDH<br>"
            "%{percentRoot:.1%}"
        ),
        textfont=dict(family=FONT_FAMILY, size=12, color="#FFFFFF"),
        insidetextfont=dict(family=FONT_FAMILY, size=12, color="#FFFFFF"),
        outsidetextfont=dict(family=FONT_FAMILY, size=12, color="#222"),
    )

    fig = go.Figure(data=[treemap])

    total       = float(root["value"])
    n_secteurs  = len(root.get("children", []))
    n_minist    = sum(len(s.get("children", [])) for s in root.get("children", []))

    title_html = (
        "<b>PLF 2026 — Dépenses par secteur et ministère</b>"
        "<br><span style='font-size:13px;color:#555;font-weight:400;'>"
        f"Total ministériel {total:.2f} MMDH · "
        f"{n_secteurs} secteurs · {n_minist} ministères"
        "</span>"
    )

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
        margin=dict(l=18, r=18, t=92, b=72),
        height=720,
        annotations=[
            dict(
                xref="paper", yref="paper",
                x=0.0, y=-0.07,
                xanchor="left", yanchor="top",
                showarrow=False,
                align="left",
                font=dict(family=FONT_FAMILY, size=11, color="#666"),
                text=(
                    "Source : PLF 2026 — Note de présentation MEF, p.163-164. "
                    f"Périmètre : Σ ministériel {total:.2f} MMDH "
                    "(fonctionnement + investissement). "
                    "Lecture : la valeur d'un ministère, divisée par 100, "
                    "donne sa part en DH sur chaque 100 DH dépensés."
                ),
            )
        ],
    )
    return fig


# ── Export ────────────────────────────────────────────────────────────────────

def export(fig):
    TREEMAP_FIG.write_text(fig.to_json(), encoding="utf-8")
    fig.write_html(
        str(TREEMAP_HTML),
        include_plotlyjs="cdn",
        full_html=True,
        config={"displaylogo": False, "responsive": True},
    )


def main():
    print("=" * 72)
    print("  PLOTLY TREEMAP — MAROC PLF 2026")
    print("=" * 72)

    if not MODELS.exists():
        MODELS.mkdir(parents=True, exist_ok=True)

    data = load_treemap_data()
    n_min = sum(
        len(s.get("children", []))
        for s in data["root"].get("children", [])
    )
    print(f"  ✅ {TREEMAP_DATA.name} chargé "
          f"(schema {data['schema_version']}, "
          f"{len(data['root']['children'])} secteurs, {n_min} ministères)")

    fig = build_figure(data)
    export(fig)

    print()
    print("  ── Sorties ──")
    print(f"    {TREEMAP_FIG.relative_to(BASE)}  "
          f"({TREEMAP_FIG.stat().st_size:,} B)")
    print(f"    {TREEMAP_HTML.relative_to(BASE)}  "
          f"({TREEMAP_HTML.stat().st_size:,} B)")
    print()
    print(f"  Généré le : {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print("=" * 72)


if __name__ == "__main__":
    main()
