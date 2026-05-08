import KPICard from '../components/charts/KPICard.jsx';
import SankeyChart from '../components/charts/SankeyChart.jsx';
import { narratives } from '../data/narratives.js';

export default function Overview() {
  const n = narratives.overview;
  return (
    <div className="space-y-8 max-w-[1400px]">
      <header>
        <h1 className="text-3xl font-bold text-ink">{n.title}</h1>
        <p className="narrative-lead mt-2 max-w-prose">{n.lead}</p>
      </header>

      <section
        aria-label="Indicateurs clés"
        className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4"
      >
        {n.kpis.map((k) => (
          <KPICard key={k.label} {...k} />
        ))}
      </section>

      <section aria-label="Flux Recettes → Budget → Dépenses" className="space-y-3">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-semibold text-ink">Flux du Budget Général</h2>
          <span className="pill">Sankey · ε ≤ 0,1 MMDH</span>
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
