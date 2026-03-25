type StatCardProps = {
  label: string;
  value: string | number;
  accent: string;
};

export function StatCard({ label, value, accent }: StatCardProps) {
  return (
    <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-xl p-5 shadow-[var(--card-shadow)] hover:shadow-[var(--card-shadow-hover)] transition-shadow">
      <p className="text-[var(--muted)] text-xs font-medium mb-3">{label}</p>
      <p className="text-2xl font-semibold text-[var(--foreground)] tracking-tight">{value}</p>
      <div className={`mt-3 inline-block px-2 py-0.5 rounded text-[10px] font-medium ${accent}`}>
        {typeof value === "number" ? (value === 0 ? "aucun" : `${value} total`) : value}
      </div>
    </div>
  );
}
