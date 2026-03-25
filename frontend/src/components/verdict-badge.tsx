const VERDICT_CONFIG: Record<string, { bg: string; text: string; label: string }> = {
  "CONTENU FIABLE": { bg: "bg-emerald-50", text: "text-emerald-700", label: "Fiable" },
  "CONTENU DOUTEUX": { bg: "bg-amber-50", text: "text-amber-700", label: "Douteux" },
  "PROBABLEMENT FAUX": { bg: "bg-red-50", text: "text-red-600", label: "Prob. faux" },
  "DEEPFAKE CONFIRMÉ": { bg: "bg-red-100", text: "text-red-700", label: "Deepfake" },
  "ARNAQUE CONFIRMÉE": { bg: "bg-violet-50", text: "text-violet-700", label: "Arnaque" },
};

export function VerdictBadge({ verdict }: { verdict: string }) {
  const config = VERDICT_CONFIG[verdict] || { bg: "bg-slate-100", text: "text-slate-500", label: verdict };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold tracking-wide uppercase ${config.bg} ${config.text}`}>
      {config.label}
    </span>
  );
}
