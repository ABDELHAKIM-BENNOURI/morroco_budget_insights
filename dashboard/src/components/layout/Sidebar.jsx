import { NavLink } from 'react-router-dom';

const NAV = [
  { to: '/',             label: "Vue d'ensemble", end: true,  hint: 'KPI + flux' },
  { to: '/recettes',     label: 'Recettes',       end: false, hint: "D'où vient l'argent" },
  { to: '/depenses',     label: 'Dépenses',       end: false, hint: 'Où va l’argent' },
  { to: '/methodologie', label: 'Méthodologie',   end: false, hint: 'Sources & invariants' },
];

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 bg-white border-r border-[color:var(--color-soft-border)] flex flex-col">
      <nav className="flex-1 p-4 space-y-1">
        {NAV.map(({ to, label, end, hint }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              [
                'block px-3 py-2 rounded-md text-sm transition-colors',
                isActive
                  ? 'bg-primary text-white shadow-sm'
                  : 'text-ink hover:bg-[color:var(--color-surface-alt)]',
              ].join(' ')
            }
          >
            {({ isActive }) => (
              <span className="flex flex-col">
                <span className="font-medium">{label}</span>
                <span
                  className={`text-[11px] ${
                    isActive ? 'text-white/80' : 'text-muted'
                  }`}
                >
                  {hint}
                </span>
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-[color:var(--color-soft-border)]">
        <div className="text-[11px] text-muted leading-snug">
          <div className="font-medium text-ink">by Abdelhakim Bennouri</div>
          <div className="mt-0.5">PLF 2026 · Maroc</div>
        </div>
      </div>
    </aside>
  );
}
