# Morocco Budget Insight 2026

Dashboard data-journalistique du **Projet de Loi de Finances 2026** (Maroc).
Pipeline reproductible PDF → CSV → JSON → graphiques Plotly, exposé via une
interface React (Vite + Tailwind) pensée pour les médias économiques.

| Sankey | Treemap |
|---|---|
| **D'où vient l'argent → où il va** : 421,33 MMDH de recettes ordinaires + 106,32 MMDH d'emprunts → 527,65 MMDH de dépenses du Budget Général. | **L'arbre des dépenses publiques** : 5 secteurs (Social, Souveraineté, Économique, Infra, Autre) → 39 ministères. |

---

## Architecture

```
data/raw/*.pdf        →  scripts/01_extract.py  →  data/clean/*.csv (extraction brute)
data/clean/*.csv      →  scripts/02_clean.py    →  data/clean/*_clean.csv + budget_canonical.csv
data/clean/*.csv      →  scripts/03_model.py    →  data/models/{sankey,treemap}_data.json
data/models/*.json    →  scripts/04_sankey.py   →  sankey_figure.json + sankey_preview.html
data/models/*.json    →  scripts/05_treemap.py  →  treemap_figure.json + treemap_preview.html
data/models/*.json    →  dashboard/             →  React + react-plotly.js (http://localhost:5173)
```

Chaque étape est **idempotente**, déclenche un rapport de validation et halt
si un invariant budgétaire est rompu.

### Invariants vérifiés (sources : BCPLF2026 p.14)

| Indicateur | Cible | Tolérance |
|---|---|---|
| Σ recettes ordinaires PLF 2026 | 421,33 MMDH | ±0,5 |
| Total dépenses Budget Général | 527,65 MMDH | ancrage strict |
| Ministères distincts | 39 | exact |
| Conservation Sankey | Σ entrées ≈ Σ sorties | ε ≤ 0,1 MMDH |
| Conservation Treemap | Σ feuilles = racine | ε ≤ 0,1 MMDH |

---

## Prérequis

- **Docker** + **Docker Compose v2.13+** (pour `service_completed_successfully`)
- *(optionnel pour dev natif)* Python 3.11, Node 20

L'hôte n'a pas besoin de `pandas` / `pdfplumber` — tout passe par les conteneurs.

---

## Installation

```bash
git clone https://github.com/<owner>/morocco_budget_insight_2026.git
cd morocco_budget_insight_2026
cp .env.example .env

# (optionnel) PDFs sources dans data/raw/ — ignorés par git
# placez-y : Note-presentation_Fr.pdf, BCPLF2026.pdf, SLF-23 Fr-2025.pdf
```

---

## Exécution

### Une seule commande (recommandé)

```bash
docker compose up
```

L'orchestration lance dans l'ordre :

1. **`pipeline`** (Python, one-shot) — exécute `02_clean.py` → `05_treemap.py`,
   produit `data/models/*.json`, écrit le flag `data/models/.pipeline_done` et
   sort avec code 0.
2. **`dashboard`** (React, Vite dev server) — attend le flag, copie les JSONs
   vers `dashboard/public/data/`, lance Vite avec hot-reload sur
   <http://localhost:5173>.

Les logs des deux conteneurs s'entrelacent dans le même terminal
(préfixes `budget_pipeline |` et `budget_dashboard |`).

### Commandes courantes

```bash
# Relancer le pipeline (modif de scripts/*.py) :
docker compose up --build --force-recreate pipeline dashboard

# Modif côté React : Vite hot-reload se charge tout seul.
# Sinon (modif de package.json par ex.) :
docker compose up --build dashboard

# Reset complet (efface volume nommé + conteneurs) :
docker compose down -v
docker compose up --build

# Lancer un script isolé dans le conteneur Python :
docker compose run --rm pipeline python scripts/03_model.py
```

### Linter Python (mêmes règles que CI)

```bash
flake8 scripts/ \
  --max-line-length=120 \
  --ignore=E501,W503,E241,E221,E302
```

---

## CI / CD

Le workflow `.github/workflows/ci.yml` exécute 5 jobs :

| Job | Rôle |
|---|---|
| `lint-python` | `py_compile` + `flake8` sur `scripts/*.py` |
| `build-python` | Build de l'image Docker `pipeline` |
| `build-react` | Build de l'image Docker `dashboard` (conditionnel à `dashboard/package.json`) |
| `check-structure` | Vérifie dossiers/fichiers obligatoires + `.gitignore` (data sensibles) |
| `deploy-pages` | Push sur `main` → publie `dashboard/dist/` sur GitHub Pages |

> Pour que `deploy-pages` produise un dashboard pleinement fonctionnel,
> `data/clean/*.csv` doit être disponible sur le runner (committé ou
> récupéré via une étape custom). Sans ces CSV, le pipeline est sauté et
> les figures retournent 404 dans le navigateur.

---

## Sources des données

| Source | Référence | Usage |
|---|---|---|
| Note de présentation PLF 2026 (MEF, FR) | p. 29 (recettes), p. 163-164 (dépenses ministérielles) | Recettes + dépenses 2026 |
| Bulletin de la Cour des Comptes — BCPLF2026 | p. 14 | Invariants 421,33 / 527,65 MMDH |
| SLF-23 (Lois de Finances 2024 et 2025) | Pages 19-23 | Comparatif historique |

Tous les documents sont publics, publiés par le **Ministère de l'Économie et
des Finances** du Maroc et la **Cour des Comptes**.

---

## Taxonomie sectorielle (figée)

Mapping ministère → secteur, défini dans `scripts/02_clean.py` (constantes
`TAXONOMIE_SECTEUR` + overrides exacts) :

| Secteur | Ministères-clés |
|---|---|
| **Social** | Éducation, Enseignement Supérieur, Santé, Solidarité, Jeunesse-Culture, Inclusion économique |
| **Souveraineté** | Défense, Intérieur, Justice, Affaires Étrangères, Habous, Cour Royale, Chambres |
| **Économique** | Économie/Finances, Industrie, Commerce, Tourisme, Agriculture, Pêche |
| **Infra** | Équipement-Eau, Transport, Aménagement-Habitat, Transitions énergétique et numérique |
| **Autre** | SGG, HCP, Conseils consultatifs, Instances de contrôle, Dépenses Imprévues |

Le matching utilise une normalisation MAJUSCULES + sans accents, ponctuation
remplacée par espaces, puis des limites de mot (`\b`) pour éviter les
collisions (ex. `CULTURE` ne matche pas `AGRICULTURE`).

---

## Structure du dépôt

```
.
├── .github/workflows/ci.yml         # 5 jobs CI/CD
├── docker/
│   ├── entrypoint.sh                # orchestre 02 → 05 et écrit le flag
│   ├── wait-and-start.sh            # attend flag + copie JSONs + Vite
│   ├── python/Dockerfile            # image pipeline
│   └── react/Dockerfile             # image dashboard
├── docker-compose.yml               # services pipeline + dashboard
├── scripts/
│   ├── 01_extract.py                # PDF → CSV brut
│   ├── 02_clean.py                  # consolidation + taxonomie
│   ├── 03_model.py                  # modélisation Sankey/Treemap
│   ├── 04_sankey.py                 # figure Plotly Sankey
│   └── 05_treemap.py                # figure Plotly Treemap
├── dashboard/
│   ├── src/
│   │   ├── components/{layout,charts}/
│   │   ├── hooks/usePlotlyFigure.js
│   │   ├── pages/                   # Overview, Recettes, Dépenses, Méthodologie
│   │   ├── data/narratives.js       # prose éditoriale FR
│   │   └── styles/{tokens,index}.css
│   ├── scripts/copy-data.mjs        # predev/prebuild (data/models → public/data)
│   ├── tailwind.config.js
│   ├── vite.config.js
│   └── package.json
├── data/
│   ├── raw/      (gitignored — PDFs sources)
│   ├── clean/    (gitignored — CSVs nettoyés)
│   └── models/   (gitignored — JSONs des figures)
├── requirements.txt
└── README.md
```

---

## Crédits

- **Auteur** : Abdelhakim Bennouri
- **Données** : Ministère de l'Économie et des Finances (Maroc), Cour des
  Comptes — sources publiques officielles
- **Stack** : Python 3.11 (pdfplumber, pandas, plotly), Node 20 (Vite,
  React 18, Tailwind 3, react-plotly.js, plotly.js-dist-min), Docker
  Compose v2

---

## Licence

Code distribué sous licence MIT. Données budgétaires : domaine public
(documents officiels du gouvernement marocain).
