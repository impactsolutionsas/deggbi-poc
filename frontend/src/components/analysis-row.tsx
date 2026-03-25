import Link from "next/link";
import { Analysis } from "@/lib/supabase";
import { VerdictBadge } from "./verdict-badge";
import { ScoreRing } from "./score-ring";

const CHANNEL_LABELS: Record<string, string> = {
  whatsapp: "WhatsApp",
  telegram: "Telegram",
  api: "API",
  web: "Web",
};

const TYPE_LABELS: Record<string, string> = {
  text: "Texte",
  image: "Image",
  audio: "Audio",
  video: "Vidéo",
};

export function AnalysisRow({ analysis }: { analysis: Analysis }) {
  const date = new Date(analysis.created_at);
  const timeAgo = formatTimeAgo(date);

  return (
    <Link
      href={`/analyses/${analysis.id}`}
      className="flex items-center gap-4 p-4 bg-[var(--card)] border border-[var(--card-border)] rounded-xl shadow-[var(--card-shadow)] hover:shadow-[var(--card-shadow-hover)] transition-all group"
    >
      <ScoreRing score={analysis.score_final} size={44} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-medium text-[var(--muted)] bg-[var(--surface)] px-2 py-0.5 rounded">
            {TYPE_LABELS[analysis.content_type] || analysis.content_type}
          </span>
          <span className="text-xs text-[var(--muted-light)]">via {CHANNEL_LABELS[analysis.channel] || analysis.channel}</span>
          <VerdictBadge verdict={analysis.verdict} />
        </div>
        <p className="text-xs text-[var(--muted-light)]">
          {analysis.sender_id ? `${analysis.sender_id.slice(0, 6)}***` : "API"} — {timeAgo}
          {analysis.analysis_time_ms && ` — ${(analysis.analysis_time_ms / 1000).toFixed(1)}s`}
        </p>
      </div>
      <div className="text-right hidden sm:block opacity-60 group-hover:opacity-100 transition-opacity">
        <p className="text-[11px] text-[var(--muted-light)]">TS {analysis.score_truthscan}</p>
        <p className="text-[11px] text-[var(--muted-light)]">DS {analysis.score_deepshield}</p>
      </div>
    </Link>
  );
}

function formatTimeAgo(date: Date): string {
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000);
  if (seconds < 60) return "à l'instant";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `il y a ${minutes}min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `il y a ${hours}h`;
  const days = Math.floor(hours / 24);
  return `il y a ${days}j`;
}
