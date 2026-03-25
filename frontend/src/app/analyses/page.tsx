import { supabase, type Analysis } from "@/lib/supabase";
import { AnalysisRow } from "@/components/analysis-row";

export const revalidate = 15;

async function getAllAnalyses(): Promise<Analysis[]> {
  const { data } = await supabase
    .from("analyses")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(100);
  return data || [];
}

export default async function AnalysesPage() {
  const analyses = await getAllAnalyses();

  const stats = {
    total: analyses.length,
    deepfakes: analyses.filter((a) => a.verdict.includes("DEEPFAKE")).length,
    arnaques: analyses.filter((a) => a.verdict.includes("ARNAQUE")).length,
    fiables: analyses.filter((a) => a.verdict === "CONTENU FIABLE").length,
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[var(--foreground)] tracking-tight">Analyses</h1>
        <p className="text-[var(--muted)] text-sm mt-0.5">
          {stats.total} analyses — {stats.deepfakes} deepfakes — {stats.arnaques} arnaques — {stats.fiables} fiables
        </p>
      </div>

      <div className="space-y-2">
        {analyses.length === 0 ? (
          <div className="bg-[var(--card)] rounded-xl border border-[var(--card-border)] py-12 text-center">
            <p className="text-[var(--muted-light)] text-sm">Aucune analyse enregistrée</p>
          </div>
        ) : (
          analyses.map((a) => <AnalysisRow key={a.id} analysis={a} />)
        )}
      </div>
    </div>
  );
}
