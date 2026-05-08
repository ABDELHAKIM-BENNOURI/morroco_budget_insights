/**
 * narratives.js — Textes éditoriaux du dashboard.
 *
 * Centralise toute la prose en français pour faciliter la relecture
 * et la mise à jour. Les chiffres exposés sont alignés sur les
 * invariants du pipeline Python (chiffres_cles_plf2026_enrichi.csv).
 */

export const narratives = {
  overview: {
    title: "PLF 2026 — Le Budget en un coup d'œil",
    lead:
      "Le Projet de Loi de Finances 2026 mobilise 527,65 milliards de dirhams. " +
      "Plus de 80 % du financement provient de l'impôt ; le solde — 106,32 MMDH — " +
      "est couvert par l'emprunt et viendra alourdir la dette publique.",
    paragraphs: [
      "Les recettes ordinaires atteignent 421,33 MMDH, en progression de 14,2 % " +
        "par rapport à la LF 2025. La hausse provient majoritairement de l'impôt " +
        "direct (+17,7 %), portée par les rendements de l'IS et de l'IR.",
      "Les dépenses du Budget Général s'élèvent à 527,65 MMDH, dont 62 % en " +
        "fonctionnement et 38 % en investissement. Le secteur social " +
        "(Éducation, Santé, Solidarité) capte 33 % de l'enveloppe ministérielle, " +
        "devant la Souveraineté (28 %).",
    ],
    kpis: [
      {
        label: "Recettes ordinaires",
        value: "421,33",
        suffix: "MMDH",
        accent: "recette",
        sublabel: "+14,2 % vs LF 2025",
      },
      {
        label: "Dépenses Budget Général",
        value: "527,65",
        suffix: "MMDH",
        accent: "depense",
        sublabel: "62 % fonct. · 38 % invest.",
      },
      {
        label: "Emprunts",
        value: "106,32",
        suffix: "MMDH",
        accent: "emprunt",
        sublabel: "20,2 % du budget",
      },
      {
        label: "Ministères",
        value: "39",
        suffix: "",
        accent: "primary",
        sublabel: "5 secteurs",
      },
    ],
  },

  recettes: {
    title: "D'où vient l'argent — Les recettes 2026",
    lead:
      "Sur chaque 100 DH du Budget Général, 80 DH proviennent de l'impôt " +
      "et 20 DH de l'emprunt. La fiscalité directe et indirecte se partagent " +
      "63 DH à parts presque égales.",
    paragraphs: [
      "Les impôts directs (IR + IS, 165,69 MMDH) progressent de +17,7 %, " +
        "traduisant la vigueur des bénéfices d'entreprise. Les impôts indirects " +
        "(TVA + TIC, 167,89 MMDH) augmentent de +15,0 %, signe d'une " +
        "consommation toujours dynamique.",
      "Les droits de douane reculent en revanche de 13,6 %, sous l'effet du " +
        "démantèlement tarifaire et des accords commerciaux. Les recettes " +
        "non fiscales (45,2 MMDH) incluent 27,5 MMDH de produits des monopoles " +
        "et participations, en hausse de 22 %.",
      "L'emprunt — 106,32 MMDH — vient combler l'écart entre dépenses et " +
        "recettes ordinaires. Il représente une dette à venir, supportée par " +
        "les contribuables des prochaines années.",
    ],
  },

  depenses: {
    title: "Où va l'argent — Les dépenses 2026",
    lead:
      "Les 39 ministères se partagent 563 MMDH (fonctionnement + investissement). " +
      "L'Éducation, la Défense et la Santé représentent à elles seules près de " +
      "40 % de l'enveloppe ministérielle.",
    paragraphs: [
      "Le secteur social (33,4 %) place l'éducation et la santé au cœur des " +
        "priorités. L'Éducation Nationale (104,4 MMDH) est de très loin le " +
        "premier poste, suivi de la Santé (55,0 MMDH).",
      "La Souveraineté (28,0 %) capte 158 MMDH, dont 68,3 MMDH pour la " +
        "Défense Nationale et 54,9 MMDH pour l'Intérieur.",
      "Les ministères économiques (25,0 %) concentrent 141 MMDH, dont " +
        "89,5 MMDH portés par les Charges Communes des Finances. Les " +
        "Infrastructures (12,7 %) font la part belle à l'Équipement et l'Eau " +
        "(60,6 MMDH).",
    ],
  },

  methodologie: {
    title: "Méthodologie & sources",
    lead:
      "Toutes les figures de ce dashboard sont produites par un pipeline " +
      "Python reproductible (10 étapes), à partir des PDF officiels. Aucune " +
      "donnée saisie à la main : les invariants du Budget sont vérifiés à " +
      "chaque étape.",
    sources: [
      {
        label: "Note de présentation PLF 2026 (MEF, version FR)",
        ref: "Pages 29 (recettes) — 163 et 164 (dépenses ministérielles)",
      },
      {
        label: "Bulletin de la Cour des Comptes — BCPLF2026",
        ref: "p. 14 — invariants 421,33 et 527,65 MMDH",
      },
      {
        label: "SLF-23 (Loi de Finances 2024 et 2025)",
        ref: "Comparatif historique fonctionnement / investissement / dette",
      },
    ],
    pipeline: [
      "Extraction PDF par pages ciblées via pdfplumber (01_extract.py)",
      "Nettoyage, normalisation des libellés et taxonomie sectorielle figée (02_clean.py)",
      "Modélisation Sankey + Treemap, schema_version 1.0 (03_model.py)",
      "Figures Plotly Sankey (04_sankey.py) et Treemap (05_treemap.py)",
      "Dashboard React Vite + react-plotly.js (cette interface)",
    ],
    invariants: [
      {
        label: "Σ recettes ordinaires PLF 2026",
        value: "421,33 MMDH",
        check: "Tolérance ±0,5 MMDH",
      },
      {
        label: "Total dépenses Budget Général",
        value: "527,65 MMDH",
        check: "Ancrage BCPLF2026 p.14",
      },
      {
        label: "Ministères distincts (après fusion)",
        value: "39",
        check: "Normalisation MAJ + sans accents, jointure simple+detail",
      },
      {
        label: "Conservation Sankey",
        value: "Δ < 0,1 MMDH",
        check: "Σ entrées Budget ≈ Σ sorties Budget",
      },
      {
        label: "Conservation Treemap",
        value: "Σ feuilles = racine",
        check: "branchvalues=\"total\"",
      },
    ],
    taxonomie: [
      ["Social",       "Éducation, Santé, Solidarité, Jeunesse-Culture, Inclusion économique"],
      ["Souveraineté", "Défense, Intérieur, Justice, Affaires Étrangères, Habous, Cour Royale, Chambres"],
      ["Économique",   "Économie/Finances, Industrie, Commerce, Tourisme, Agriculture, Pêche"],
      ["Infra",        "Équipement-Eau, Transport, Aménagement-Habitat, Transitions énergétique et numérique"],
      ["Autre",        "SGG, HCP, Conseils consultatifs, Instances de contrôle, Dépenses Imprévues"],
    ],
  },
};
