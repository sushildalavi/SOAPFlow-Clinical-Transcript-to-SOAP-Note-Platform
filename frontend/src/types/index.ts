export type WarningSeverity = "info" | "warning" | "error";

export interface ValidationWarning {
  code: string;
  message: string;
  severity: WarningSeverity;
  field?: string | null;
}

export interface SOAPNote {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
}

export interface GenerationMetadata {
  model: string;
  mode: string;
  transcript_word_count: number;
  transcript_char_count: number;
  note_word_count: number;
  processing_time_ms: number;
  sections_populated: number;
}

export interface GenerateResponse {
  success: boolean;
  soap_note: SOAPNote;
  warnings: ValidationWarning[];
  metadata: GenerationMetadata;
  raw_json?: Record<string, string> | null;
}

export interface HealthResponse {
  status: string;
  version: string;
  generation_mode: string;
  openai_configured: boolean;
  anthropic_configured: boolean;
}

export interface DemoTranscriptResponse {
  transcript: string;
  title: string;
  description: string;
  expected_chief_complaint: string;
}

export interface DemoListItem {
  index: number;
  title: string;
  description: string;
}

export type GenerationMode = "openai" | "anthropic" | "demo";

export type AppState = "idle" | "loading" | "success" | "error";

// ─── History ────────────────────────────────────────────────────────────────

export interface NoteMetadata {
  model: string;
  mode: string;
  processing_time_ms?: number | null;
  transcript_word_count?: number | null;
  note_word_count?: number | null;
  sections_populated?: number | null;
}

export interface NoteRecord {
  id: number;
  title: string;
  transcript: string;
  soap_note: SOAPNote;
  metadata: NoteMetadata;
  warnings: ValidationWarning[];
  created_at: string | null;
}

export interface NoteListResponse {
  success: boolean;
  total: number;
  notes: NoteRecord[];
}

export interface SaveNoteRequest {
  transcript: string;
  soap_note: SOAPNote;
  metadata?: Partial<NoteMetadata>;
  warnings?: ValidationWarning[];
  title?: string;
}

// ─── Stats ──────────────────────────────────────────────────────────────────

export interface StatsResponse {
  total_notes_saved: number;
  by_generation_mode: Record<string, number>;
  avg_processing_time_ms: number | null;
  avg_sections_populated: number | null;
  latest_note_at: string | null;
  server: HealthResponse;
}
