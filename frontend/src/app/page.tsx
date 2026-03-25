import { supabase, type DashboardStats, type Analysis } from "@/lib/supabase";
import { StatCard } from "@/components/stat-card";
import { AnalysisRow } from "@/components/analysis-row";

export const revalidate = 30;

async function getStats(): Promise<DashboardStats> {
  const { data } = await supabase
    .from("dashboard_stats")
    .select("*")
    .single();
  return data || {
    total_analyses: 0, deepfakes_detected: 0, arnaques_detected: 0,
    contenus_fiables: 0, avg_time_ms: 0, unique_users: 0,
  };
}

async function getRecentAnalyses(): Promise<Analysis[]> {
  const { data } = await supabase
    .from("analyses")
    .select("*")
    .order("created_at", { ascending: false })
    .limit(5);
  return data || [];
}

export default async function DashboardPage() {
  const [stats, recent] = await Promise.all([getStats(), getRecentAnalyses()]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold text-[var(--foreground)] tracking-tight">Dashboard</h1>
        <p className="text-[var(--muted)] text-sm mt-0.5">Vue d&apos;ensemble des 30 derniers jours</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Analyses totales" value={stats.total_analyses} accent="bg-slate-100 text-slate-600" />
        <StatCard label="Deepfakes détectés" value={stats.deepfakes_detected} accent="bg-red-50 text-red-600" />
        <StatCard label="Arnaques détectées" value={stats.arnaques_detected} accent="bg-amber-50 text-amber-600" />
        <StatCard label="Contenus fiables" value={stats.contenus_fiables} accent="bg-emerald-50 text-emerald-600" />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          label="Temps moyen"
          value={stats.avg_time_ms ? `${(stats.avg_time_ms / 1000).toFixed(1)}s` : "—"}
          accent="bg-blue-50 text-blue-600"
        />
        <StatCard label="Utilisateurs uniques" value={stats.unique_users} accent="bg-violet-50 text-violet-600" />
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-[var(--foreground)]">Analyses récentes</h2>
          <a href="/analyses" className="text-sm text-[var(--accent-blue)] hover:underline">Voir tout</a>
        </div>
        <div className="space-y-2">
          {recent.length === 0 ? (
            <div className="bg-[var(--card)] rounded-xl border border-[var(--card-border)] py-12 text-center">
              <p className="text-[var(--muted-light)] text-sm">Aucune analyse pour le moment</p>
            </div>
          ) : (
            recent.map((a) => <AnalysisRow key={a.id} analysis={a} />)
          )}
        </div>
      </div>
    </div>
  );
}
