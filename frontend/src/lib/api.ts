import type {
  GenerateResponse,
  HealthResponse,
  DemoTranscriptResponse,
  DemoListItem,
  GenerationMode,
  SOAPNote,
  NoteRecord,
  NoteListResponse,
  SaveNoteRequest,
  StatsResponse,
} from "@/types";

const DEFAULT_LOCAL_API_ORIGIN = "http://localhost:8000";
const API_ORIGIN = normalizeOrigin(import.meta.env.VITE_API_ORIGIN);
const API_BASE_PATH = normalizeBasePath(import.meta.env.VITE_API_BASE_PATH ?? "/api/v1");

function normalizeOrigin(value?: string): string {
  return value?.trim().replace(/\/+$/, "") ?? "";
}

function normalizeBasePath(value: string): string {
  const trimmed = value.trim().replace(/\/+$/, "");
  return trimmed.startsWith("/") ? trimmed : `/${trimmed}`;
}

function resolveApiUrl(endpoint: string): string {
  const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  return `${API_ORIGIN}${API_BASE_PATH}${normalizedEndpoint}`;
}

function resolveDocsUrl(): string {
  if (API_ORIGIN) {
    return `${API_ORIGIN}/docs`;
  }
  if (typeof window === "undefined") {
    return `${DEFAULT_LOCAL_API_ORIGIN}/docs`;
  }

  const { hostname, protocol, origin } = window.location;
  if (hostname === "localhost" || hostname === "127.0.0.1") {
    return `${protocol}//${hostname}:8000/docs`;
  }

  return `${origin}/docs`;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers);
  const hasBody = options.body !== undefined;
  if (hasBody && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(resolveApiUrl(endpoint), {
    ...options,
    headers,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Request failed with status ${response.status}`
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json().catch(() => undefined as T);
}

export const api = {
  docsUrl(): string {
    return resolveDocsUrl();
  },

  url(endpoint: string): string {
    return resolveApiUrl(endpoint);
  },

  health(): Promise<HealthResponse> {
    return request<HealthResponse>("/health");
  },

  generate(
    transcript: string,
    mode?: GenerationMode,
    signal?: AbortSignal
  ): Promise<GenerateResponse> {
    return request<GenerateResponse>("/generate", {
      method: "POST",
      signal,
      body: JSON.stringify({
        transcript,
        include_raw_json: true,
        mode: mode ?? null,
      }),
    });
  },

  getDemoTranscript(index: number = 0): Promise<DemoTranscriptResponse> {
    return request<DemoTranscriptResponse>(`/demo-transcript?index=${index}`);
  },

  listDemoTranscripts(): Promise<DemoListItem[]> {
    return request<DemoListItem[]>("/demo-transcripts/list");
  },

  // ─── History ──────────────────────────────────────────────────────────────

  listHistory(limit = 50, offset = 0): Promise<NoteListResponse> {
    return request<NoteListResponse>(`/history?limit=${limit}&offset=${offset}`);
  },

  saveNote(payload: SaveNoteRequest): Promise<NoteRecord> {
    return request<NoteRecord>("/history", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getNote(id: number): Promise<NoteRecord> {
    return request<NoteRecord>(`/history/${id}`);
  },

  deleteNote(id: number): Promise<void> {
    return request<void>(`/history/${id}`, { method: "DELETE" });
  },

  clearHistory(): Promise<void> {
    return request<void>("/history", { method: "DELETE" });
  },

  // ─── Evaluation ───────────────────────────────────────────────────────────

  evaluate(
    transcript: string,
    generatedNote: SOAPNote,
    referenceNote?: SOAPNote
  ): Promise<unknown> {
    return request<unknown>("/evaluate", {
      method: "POST",
      body: JSON.stringify({
        transcript,
        generated_note: generatedNote,
        reference_note: referenceNote ?? null,
      }),
    });
  },

  // ─── Stats ────────────────────────────────────────────────────────────────

  getStats(): Promise<StatsResponse> {
    return request<StatsResponse>("/stats");
  },
};
