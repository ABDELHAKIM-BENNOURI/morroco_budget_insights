const ACCENTS = {
  primary: { bar: 'bg-primary',  ring: 'ring-primary/20'  },
  recette: { bar: 'bg-recette',  ring: 'ring-recette/20'  },
  depense: { bar: 'bg-depense',  ring: 'ring-depense/20'  },
  emprunt: { bar: 'bg-emprunt',  ring: 'ring-emprunt/20'  },
};

export default function KPICard({
  label,
  value,
  suffix = 'MMDH',
  accent = 'primary',
  sublabel = null,
}) {
  const a = ACCENTS[accent] || ACCENTS.primary;

  return (
    <div className={`card overflow-hidden flex ring-1 ring-black/[0.03] ${a.ring}`}>
      <div className={`w-1.5 ${a.bar}`} aria-hidden="true" />
      <div className="flex-1 p-5">
        <div className="text-xs uppercase tracking-wider text-muted font-medium">
          {label}
        </div>
        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-3xl font-bold text-ink leading-none">{value}</span>
          {suffix && (
            <span className="text-sm text-muted font-medium">{suffix}</span>
          )}
        </div>
        {sublabel && (
          <div className="mt-2 text-sm text-muted">{sublabel}</div>
        )}
      </div>
    </div>
  );
}
