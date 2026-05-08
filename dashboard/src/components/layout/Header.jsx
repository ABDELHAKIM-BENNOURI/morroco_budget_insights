import { Link } from 'react-router-dom';

export default function Header() {
  return (
    <header className="bg-white border-b border-[color:var(--color-soft-border)] sticky top-0 z-20">
      <div className="px-6 py-4 flex items-center justify-between gap-4">
        <Link to="/" className="flex items-baseline gap-3 group">
          <span className="text-xl font-extrabold text-primary tracking-tight group-hover:opacity-90">
            PLF 2026
          </span>
          <span className="text-sm text-muted">Budget Insight Maroc</span>
        </Link>

        <div className="hidden sm:flex items-center gap-3 text-xs text-muted">
          <span className="pill font-mono">v1.0</span>
          <span>Données BCPLF2026 · Note de présentation MEF</span>
        </div>
      </div>
    </header>
  );
}
