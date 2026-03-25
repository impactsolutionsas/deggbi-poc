import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export type Analysis = {
  id: string;
  content_type: string;
  channel: string;
  sender_id: string | null;
  score_truthscan: number;
  score_deepshield: number;
  score_final: number;
  verdict: string;
  report_text: string | null;
  analysis_time_ms: number | null;
  language: string;
  media_url: string | null;
  created_at: string;
};

export type DashboardStats = {
  total_analyses: number;
  deepfakes_detected: number;
  arnaques_detected: number;
  contenus_fiables: number;
  avg_time_ms: number;
  unique_users: number;
};
