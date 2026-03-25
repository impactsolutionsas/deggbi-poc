import { supabase, type Analysis } from "@/lib/supabase";
import { VerdictBadge } from "@/components/verdict-badge";
import { ScoreRing } from "@/components/score-ring";
import { notFound } from "next/navigation";
import Link from "next/link";

export const revalidate = 30;

async function getAnalysis(id: string): Promise<Analysis | null> {
  const { data } = await supabase
    .from("analyses")
    .select("*")
    .eq("id", id)
    .single();
  return data;
}

export default async function AnalysisDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const analysis = await getAnalysis(params.id);
  if (!analysis) notFound();

  const date = new Date(analysis.created_at).toLocaleString("fr-FR", {
    dateStyle: "long",
    timeStyle: "short",
  });

  return (
    <div className="space-y-6 max-w-3xl">
      <Link href="/analyses" className="text-sm text-[var(--accent-blue)] hover:underline">
        Retour aux analyses
      </Link>

      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-xl p-6 shadow-[var(--card-shadow)] space-y-6">
        <div className="flex items-start justify-between">
          <div>
            <VerdictBadge verdict={analysis.verdict} />
            <p className="text-xs text-[var(--muted-light)] mt-2">{date}</p>
          </div>
          <ScoreRing score={analysis.score_final} size={72} />
        </div>

        <div className="grid grid-cols-3 gap-3">
          <ScoreBlock label="Score Final" value={analysis.score_final} />
          <ScoreBlock label="TruthScan" value={analysis.score_truthscan} />
          <ScoreBlock label="DeepShield" value={analysis.score_deepshield} />
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <InfoBlock label="Type" value={analysis.content_type} />
          <InfoBlock label="Canal" value={analysis.channel} />
          <InfoBlock label="Langue" value={analysis.language} />
          <InfoBlock
            label="Temps d'analyse"
            value={analysis.analysis_time_ms ? `${(analysis.analysis_time_ms / 1000).toFixed(1)}s` : "—"}
          />
          {analysis.sender_id && (
            <InfoBlock label="Expéditeur" value={`${analysis.sender_id.slice(0, 6)}***`} />
          )}
        </div>

        {analysis.report_text && (
          <div>
            <h3 className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider mb-2">Rapport</h3>
            <pre className="bg-[var(--surface)] rounded-lg p-4 text-sm text-[var(--foreground)] whitespace-pre-wrap font-sans leading-relaxed">
              {analysis.report_text}
            </pre>
          </div>
        )}

        {analysis.media_url && (
          <div>
            <h3 className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider mb-2">Média</h3>
            {analysis.content_type === "image" ? (
              <img
                src={analysis.media_url}
                alt="Média analysé"
                className="rounded-lg max-h-64 object-contain border border-[var(--card-border)]"
              />
            ) : (
              <a
                href={analysis.media_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-[var(--accent-blue)] hover:underline text-sm"
              >
                Télécharger le média
              </a>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function ScoreBlock({ label, value }: { label: string; value: number }) {
  const color =
    value <= 30 ? "text-emerald-600" :
    value <= 60 ? "text-amber-600" :
    value <= 85 ? "text-red-600" :
    "text-red-700";
  return (
    <div className="bg-[var(--surface)] rounded-lg p-3 text-center">
      <p className="text-[10px] text-[var(--muted-light)] uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-xl font-semibold ${color}`}>{value}</p>
    </div>
  );
}

function InfoBlock({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] text-[var(--muted-light)] uppercase tracking-wider">{label}</p>
      <p className="text-sm text-[var(--foreground)] capitalize mt-0.5">{value}</p>
    </div>
  );
}
