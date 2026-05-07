# 📊 Guide du Projet — Analyse et Visualisation du Budget de l'État Marocain 2026

---

# 🎯 1. Objectif du projet

Dans un contexte où la transparence budgétaire devient essentielle, ce projet vise à **analyser et visualiser les finances publiques du Maroc pour l’année 2026**.

L’objectif est de produire une **analyse claire, rigoureuse et visuellement impactante**, permettant de :

- Comprendre **la structure des recettes de l’État**
- Analyser **la répartition des dépenses publiques**
- Visualiser **l’allocation des investissements par secteur**
- Expliquer **la logique de redistribution de chaque 100 dirhams investis**

👉 Le livrable final doit être **professionnel**, comparable à un travail de **data journalisme**, et exploitable par des médias économiques.

---

# 🔭 2. Vision globale du projet (Pipeline complet)

Le projet suit un **workflow structuré de data science et data engineering** :

```
Collecte des données
        ↓
Nettoyage & Préparation
        ↓
Modélisation des données
        ↓
Analyse économique
        ↓
Visualisation (Sankey + Treemap)
        ↓
Intégration Dashboard (React)
        ↓
Storytelling & Interprétation
        ↓
Production des livrables
```

👉 Chaque étape dépend de la précédente.
👉 Une erreur au début impacte tout le projet.

---

# 🧭 3. Étapes du projet (ordre exact à suivre)

---

## 🔹 Étape 1 — Collecte des données

### 🎯 Objectif :

Rassembler des **données fiables et officielles** sur le budget marocain 2026.

### 📚 Sources obligatoires :

- Loi de finances 2026 (PLF / LF)
- Ministère de l’Économie et des Finances (MEF)
- Bank Al-Maghrib (BAM)
- Haut-Commissariat au Plan (HCP)
- Rapports budgétaires officiels
- Documents parlementaires
- Rapports d’institutions publiques

### 📌 Données à collecter :

#### ➤ Recettes de l’État :

- Recettes fiscales : TVA, IR, IS, droits de douane
- Recettes non fiscales
- Emprunts et financements
- Autres ressources

#### ➤ Dépenses publiques :

- Dépenses de fonctionnement
- Dépenses d’investissement
- Charges de la dette
- Dépenses par ministère / secteur

### ✅ Résultat attendu :

Dataset brut structuré (CSV / Excel)

---

## 🔹 Étape 2 — Nettoyage et préparation des données

### 🎯 Objectif :

Transformer les données brutes en données exploitables.

### 🔧 Actions :

- Uniformiser les unités (MAD)
- Nettoyer les valeurs manquantes
- Vérifier cohérence (recettes ≈ budget ≈ dépenses)
- Structurer catégories

### ✅ Résultat :

Dataset propre

---

## 🔹 Étape 3 — Modélisation des données

### 🎯 Objectif :

Préparer les données pour Sankey et Treemap

### 📁 Sankey :

\| Source | Target | Value |

### 📁 Treemap :

\| Secteur | Montant | % |

### ✅ Résultat :

Datasets prêts

---

## 🔹 Étape 4 — Analyse économique

### 🎯 Objectif :

Interpréter les données

### 🔍 Questions :

1. Quelle est la principale source de revenus de l’État ?
2. Quelle est la part des impôts vs emprunts ?
3. Quels secteurs reçoivent le plus de financement ?
4. Existe-t-il des déséquilibres ?
5. Quelle est la logique de redistribution ?

### ✅ Résultat :

Insights économiques

---

## 🔹 Étape 5 — Sankey (Plotly)

### 🎯 Objectif :

Visualiser flux financiers

Structure :
Recettes → Budget → Dépenses

### ✅ Résultat :

Graphique Sankey interactif

---

## 🔹 Étape 6 — Treemap (Plotly)

### 🎯 Objectif :

Répartition des 100 dirhams

### ✅ Résultat :

Treemap interactif

---

## 🔹 Étape 7 — Stack technique & Dashboard

### 🧠 Stack choisie :

- Python (Pandas + Plotly)
- React (Dashboard)
- HTML / CSS

### ⚙️ Architecture :

```
Python → traitement + génération graphes (JSON)
        ↓
Export JSON
        ↓
React Dashboard
        ↓
Affichage interactif (react-plotly.js)
```

### 📌 Avantages :

- Flexibilité
- Interactivité élevée
- Niveau professionnel

### ⚠️ Limites :

- Complexité
- Intégration technique

---

## 🔹 Étape 8 — Intégration Dashboard React

### 🎯 Objectif :

Créer une interface interactive

### 📌 Contenu :

- Sankey
- Treemap
- Filtres (optionnel)
- Textes explicatifs

### ✅ Résultat :

Dashboard moderne

---

## 🔹 Étape 9 — Storytelling

### 🎯 Objectif :

Rendre compréhensible pour le public

### ✅ Résultat :

Message clair

---

## 🔹 Étape 10 — Livrables

- Rapport PDF
- Visualisations
- Dataset
- Note média

---

# 🚀 Conclusion

Projet = Data + Tech + Storytelling

