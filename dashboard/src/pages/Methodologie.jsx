import { narratives } from '../data/narratives.js';

export default function Methodologie() {
  const n = narratives.methodologie;
  return (
    <div className="space-y-10 max-w-[1100px]">
      <header>
        <h1 className="text-3xl font-bold text-ink">{n.title}</h1>
        <p className="narrative-lead mt-2 max-w-prose">{n.lead}</p>
      </header>

      <section aria-label="Sources">
        <h2 className="text-xl font-semibold text-ink mb-3">Sources</h2>
        <ul className="space-y-2">
          {n.sources.map((s) => (
            <li key={s.label} className="card p-4 flex flex-col">
              <span className="font-medium text-ink">{s.label}</span>
              <span className="text-sm text-muted mt-0.5">{s.ref}</span>
            </li>
          ))}
        </ul>
      </section>

      <section aria-label="Pipeline">
        <h2 className="text-xl font-semibold text-ink mb-3">Pipeline reproductible</h2>
        <ol className="space-y-2 list-decimal list-inside">
          {n.pipeline.map((step, i) => (
            <li key={i} className="text-ink">
              <span className="text-sm">{step}</span>
            </li>
          ))}
        </ol>
      </section>

      <section aria-label="Invariants">
        <h2 className="text-xl font-semibold text-ink mb-3">Invariants vérifiés</h2>
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-[color:var(--color-surface-alt)] text-muted">
              <tr>
                <th className="text-left px-4 py-2 font-medium">Indicateur</th>
                <th className="text-left px-4 py-2 font-medium">Valeur</th>
                <th className="text-left px-4 py-2 font-medium">Contrôle</th>
              </tr>
            </thead>
            <tbody>
              {n.invariants.map((row) => (
                <tr key={row.label} className="border-t border-[color:var(--color-soft-border)]">
                  <td className="px-4 py-2.5 text-ink">{row.label}</td>
                  <td className="px-4 py-2.5 font-mono text-primary">{row.value}</td>
                  <td className="px-4 py-2.5 text-muted">{row.check}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section aria-label="Taxonomie sectorielle">
        <h2 className="text-xl font-semibold text-ink mb-3">Taxonomie sectorielle (figée)</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          {n.taxonomie.map(([secteur, content]) => (
            <div key={secteur} className="card p-4">
              <div className="font-semibold text-ink">{secteur}</div>
              <div className="text-sm text-muted mt-1">{content}</div>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted mt-3 max-w-prose">
          La taxonomie est appliquée par <code className="font-mono">scripts/02_clean.py</code> via une
          liste de mots-clés, complétée d'overrides exacts pour les institutions
          ambiguës. Le matching se fait après normalisation (MAJ, sans accents,
          ponctuation→espace) et par limites de mot pour éviter les collisions
          (ex. <code>CULTURE</code> ne doit pas matcher <code>AGRICULTURE</code>).
        </p>
      </section>
    </div>
  );
}
