import SankeyChart from '../components/charts/SankeyChart.jsx';
import KPICard from '../components/charts/KPICard.jsx';
import { narratives } from '../data/narratives.js';

const KPIS = [
  { label: "Impôts directs",     value: "165,69", accent: "recette", sublabel: "+17,7 % vs LF 2025" },
  { label: "Impôts indirects",   value: "167,89", accent: "recette", sublabel: "+15,0 % vs LF 2025" },
  { label: "Recettes non fisc.", value: "45,24",  accent: "recette", sublabel: "+15,6 % vs LF 2025" },
  { label: "Emprunts",           value: "106,32", accent: "emprunt", sublabel: "Déficit 2026" },
];

export default function Recettes() {
  const n = narratives.recettes;
  return (
    <div className="space-y-8 max-w-[1400px]">
      <header>
        <h1 className="text-3xl font-bold text-ink">{n.title}</h1>
        <p className="narrative-lead mt-2 max-w-prose">{n.lead}</p>
      </header>

      <section
        aria-label="Recettes par grande masse"
        className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4"
      >
        {KPIS.map((k) => (
          <KPICard key={k.label} {...k} />
        ))}
      </section>

      <section aria-label="Sankey des recettes" className="space-y-3">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-semibold text-ink">Sources de financement</h2>
          <span className="pill">Recettes &lt; 2 % regroupées</span>
        </div>
        <SankeyChart />
      </section>

      <section className="narrative max-w-prose">
        {n.paragraphs.map((p, i) => (
          <p key={i}>{p}</p>
        ))}
      </section>
    </div>
  );
}
