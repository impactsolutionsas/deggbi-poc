"use client";

import { useState, useRef } from "react";
import { ScoreRing } from "@/components/score-ring";
import { VerdictBadge } from "@/components/verdict-badge";

// Proxy via Next.js API route — pas de CORS
const API_URL = "";

type AnalysisResult = {
  id: string;
  content_type: string;
  score_truthscan: number;
  score_deepshield: number;
  score_final: number;
  verdict: string;
  report: string;
  analysis_time_ms: number;
  truthscan_details: Record<string, unknown>;
  deepshield_details: Record<string, unknown>;
};

export default function AnalyzePage() {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("fr");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    if (!text && !file) return;
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    if (text) formData.append("text", text);
    if (file) formData.append("file", file);
    formData.append("language", language);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 120000);

    try {
      const resp = await fetch(`/api/analyze`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });
      clearTimeout(timeout);
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(err.detail || `Erreur serveur (${resp.status})`);
      }
      const data: AnalysisResult = await resp.json();
      setResult(data);
    } catch (e: unknown) {
      clearTimeout(timeout);
      if (e instanceof DOMException && e.name === "AbortError") {
        setError("Timeout — l'analyse a pris trop de temps (>2min)");
      } else if (e instanceof TypeError && (e.message === "Failed to fetch" || e.message.includes("NetworkError"))) {
        setError("Impossible de joindre le backend. Vérifiez que FastAPI tourne sur le port 8000.");
      } else {
        setError(e instanceof Error ? e.message : "Erreur inconnue");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) setFile(dropped);
  };

  const clearAll = () => {
    setText("");
    setFile(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-[var(--foreground)] tracking-tight">
          Analyser un contenu
        </h1>
        <p className="text-[var(--muted)] text-sm mt-0.5">
          Collez un message ou uploadez un fichier (image, audio, vidéo) pour lancer l&apos;analyse
        </p>
      </div>

      {/* Input zone */}
      <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-xl p-5 shadow-[var(--card-shadow)] space-y-4">
        {/* Text input */}
        <div>
          <label className="text-xs font-medium text-[var(--muted)] uppercase tracking-wider block mb-2">
            Message / Texte
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Collez un message suspect, un SMS, un texte viral..."
            rows={4}
            className="w-full bg-[var(--surface)] border border-[var(--card-border)] rounded-lg px-4 py-3 text-sm text-[var(--foreground)] placeholder:text-[var(--muted-light)] focus:outline-none focus:ring-2 focus:ring-[var(--accent-blue)]/30 focus:border-[var(--accent-blue)] resize-none transition-all"
          />
        </div>

        {/* File upload */}
        <div>
          <label className="text-xs font-medium text-[var(--muted)] uppercase tracking-wider block mb-2">
            Fichier (image, audio ou vidéo)
          </label>
          <div
            onDrop={handleFileDrop}
            onDragOver={(e) => e.preventDefault()}
            className="border-2 border-dashed border-[var(--card-border)] rounded-lg p-6 text-center hover:border-[var(--accent-blue)]/40 transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*,audio/*,video/*"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="hidden"
            />
            {file ? (
              <div className="space-y-1">
                <p className="text-sm text-[var(--foreground)] font-medium">{file.name}</p>
                <p className="text-xs text-[var(--muted-light)]">
                  {(file.size / 1024).toFixed(0)} Ko — {file.type}
                </p>
              </div>
            ) : (
              <div className="space-y-1">
                <p className="text-sm text-[var(--muted)]">
                  Glissez un fichier ici ou cliquez pour sélectionner
                </p>
                <p className="text-xs text-[var(--muted-light)]">
                  JPG, PNG, MP3, WAV, MP4, MOV...
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Language + Submit */}
        <div className="flex items-center gap-3">
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-[var(--surface)] border border-[var(--card-border)] rounded-lg px-3 py-2 text-sm text-[var(--foreground)] focus:outline-none"
          >
            <option value="fr">Français</option>
            <option value="en">English</option>
            <option value="wo">Wolof</option>
          </select>

          <button
            onClick={handleSubmit}
            disabled={loading || (!text && !file)}
            className="flex-1 bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-medium text-sm py-2.5 px-5 rounded-lg hover:from-emerald-600 hover:to-teal-700 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Analyse en cours...
              </span>
            ) : (
              "Analyser"
            )}
          </button>

          {(text || file || result) && (
            <button
              onClick={clearAll}
              className="text-sm text-[var(--muted)] hover:text-[var(--foreground)] px-3 py-2 rounded-lg hover:bg-[var(--surface)] transition-all"
            >
              Effacer
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Result */}
      {result && (
        <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-xl shadow-[var(--card-shadow)] overflow-hidden">
          {/* Header */}
          <div className="p-5 flex items-start justify-between">
            <div className="space-y-2">
              <VerdictBadge verdict={result.verdict} />
              <p className="text-xs text-[var(--muted-light)]">
                {result.content_type} — {(result.analysis_time_ms / 1000).toFixed(1)}s
              </p>
            </div>
            <ScoreRing score={result.score_final} size={72} />
          </div>

          {/* Scores */}
          <div className="grid grid-cols-3 gap-3 px-5">
            <ScoreBlock label="Score Final" value={result.score_final} />
            <ScoreBlock label="TruthScan" value={result.score_truthscan} />
            <ScoreBlock label="DeepShield" value={result.score_deepshield} />
          </div>

          {/* Report */}
          <div className="p-5">
            <h3 className="text-xs font-semibold text-[var(--muted)] uppercase tracking-wider mb-2">
              Rapport
            </h3>
            <pre className="bg-[var(--surface)] rounded-lg p-4 text-sm text-[var(--foreground)] whitespace-pre-wrap font-sans leading-relaxed">
              {result.report}
            </pre>
          </div>
        </div>
      )}
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
