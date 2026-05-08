import TreemapChart from '../components/charts/TreemapChart.jsx';
import KPICard from '../components/charts/KPICard.jsx';
import { narratives } from '../data/narratives.js';

const SECTEURS = [
  { label: "Social",       value: "33,4", suffix: "% — 188,0 MMDH", accent: "primary" },
  { label: "Souveraineté", value: "28,0", suffix: "% — 157,8 MMDH", accent: "emprunt" },
  { label: "Économique",   value: "25,0", suffix: "% — 141,0 MMDH", accent: "recette" },
  { label: "Infra",        value: "12,7", suffix: "% —  71,5 MMDH", accent: "depense" },
];

export default function Depenses() {
  const n = narratives.depenses;
  return (
    <div className="space-y-8 max-w-[1400px]">
      <header>
        <h1 className="text-3xl font-bold text-ink">{n.title}</h1>
        <p className="narrative-lead mt-2 max-w-prose">{n.lead}</p>
      </header>

      <section
        aria-label="Répartition par secteur"
        className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4"
      >
        {SECTEURS.map((k) => (
          <KPICard key={k.label} {...k} />
        ))}
      </section>

      <section aria-label="Treemap des dépenses" className="space-y-3">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-semibold text-ink">Arbre des dépenses publiques</h2>
          <span className="pill">39 ministères · 5 secteurs</span>
        </div>
        <TreemapChart />
      </section>

      <section className="narrative max-w-prose">
        {n.paragraphs.map((p, i) => (
          <p key={i}>{p}</p>
        ))}
      </section>
    </div>
  );
}
