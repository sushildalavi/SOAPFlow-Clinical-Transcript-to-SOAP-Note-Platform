import { useState, useEffect, useCallback } from "react";
import {
  Activity,
  AlertCircle,
  Wifi,
  Save,
  Loader2,
  ClipboardList,
  Sparkles,
  ShieldCheck,
} from "lucide-react";
import { Navbar } from "@/components/layout/Navbar";
import { TranscriptInput } from "@/components/soap/TranscriptInput";
import { OutputPanel } from "@/components/soap/OutputPanel";
import { HistoryPanel } from "@/components/history/HistoryPanel";
import { SettingsPanel } from "@/components/settings/SettingsPanel";
import { ToastContainer } from "@/components/shared/ToastContainer";
import { useGenerate } from "@/hooks/useGenerate";
import { useHistory } from "@/hooks/useHistory";
import { useToast } from "@/hooks/useToast";
import { api } from "@/lib/api";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { HealthResponse, NoteRecord, GenerationMode } from "@/types";

const FEATURE_CARDS = [
  {
    icon: ClipboardList,
    title: "SOAP Format",
    description:
      "Subjective, Objective, Assessment, Plan — the universal standard for clinical documentation.",
  },
  {
    icon: Sparkles,
    title: "AI-Powered",
    description:
      "Supports OpenAI GPT-4o and Anthropic Claude, with a built-in deterministic fallback for offline use.",
  },
  {
    icon: ShieldCheck,
    title: "Smart Validation",
    description:
      "Automatic quality checks flag missing sections, sparse content, and clinical inconsistencies.",
  },
] as const;

export default function App() {
  const [transcript, setTranscript] = useState("");
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  const { state, result, error, generate, reset } = useGenerate();
  const historyState = useHistory();
  const { toasts, toast, dismiss } = useToast();

  const isLoading = state === "loading";

  useEffect(() => {
    api.health()
      .then((h) => {
        setHealth(h);
        setBackendOnline(true);
      })
      .catch(() => {
        setBackendOnline(false);
      });
  }, []);

  const handleGenerate = useCallback(
    async (text: string, mode?: GenerationMode) => {
      reset();
      try {
        const result = await generate(text, mode);
        if (result) {
          const errorCount = result.warnings.filter((w) => w.severity === "error").length;
          const warnCount = result.warnings.filter((w) => w.severity === "warning").length;
          if (errorCount > 0) {
            toast({
              variant: "warning",
              title: "Note generated with issues",
              description: `${errorCount} error${errorCount !== 1 ? "s" : ""} detected. Please review.`,
            });
          } else {
            toast({
              variant: "success",
              title: "SOAP note generated",
              description: warnCount > 0
                ? `${warnCount} warning${warnCount !== 1 ? "s" : ""} to review.`
                : "All sections populated successfully.",
            });
          }
        }
      } catch (err) {
        toast({
          variant: "destructive",
          title: "Generation failed",
          description: err instanceof Error ? err.message : "Unknown error",
        });
      }
    },
    [generate, reset, toast]
  );

  const handleSaveNote = async () => {
    if (!result || !transcript) return;
    const saved = await historyState.saveCurrentNote(transcript, result);
    if (saved) {
      toast({ variant: "success", title: "Saved to history", description: saved.title });
    } else {
      toast({ variant: "destructive", title: "Save failed", description: "Could not save note to history." });
    }
  };

  const handleLoadFromHistory = (note: NoteRecord) => {
    setTranscript(note.transcript);
    reset();
    toast({ variant: "success", title: "Note loaded", description: note.title });
  };

  const isOfflinePreview =
    health !== null && !health.openai_configured && !health.anthropic_configured;

  return (
    <div className="min-h-screen bg-background">
      <Navbar
        onToggleHistory={() => setHistoryOpen((v) => !v)}
        onToggleSettings={() => setSettingsOpen((v) => !v)}
        historyCount={historyState.total}
      />

      {/* History panel */}
      <HistoryPanel
        isOpen={historyOpen}
        onClose={() => setHistoryOpen(false)}
        historyState={historyState}
        onLoadNote={handleLoadFromHistory}
      />

      {/* Settings panel */}
      <SettingsPanel isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />

      {/* Backend offline banner */}
      {backendOnline === false && (
        <div className="border-b border-amber-200 bg-amber-50">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-2.5 flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-amber-600 shrink-0" aria-hidden="true" />
            <p className="text-xs text-amber-900">
              <span className="font-semibold">Backend offline.</span>{" "}
              Start the API server:{" "}
              <code className="font-mono bg-amber-100 px-1.5 py-0.5 rounded text-amber-900">
                cd backend && uvicorn app.main:app --reload
              </code>
            </p>
          </div>
        </div>
      )}

      {/* Hero */}
      <div className="border-b border-border bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className="inline-flex items-center gap-1.5 rounded-full bg-primary-soft px-2.5 py-1 text-xs font-semibold text-primary-strong">
                  <Activity className="h-3 w-3" aria-hidden="true" />
                  AI Clinical Documentation
                </span>
                {backendOnline === true && health && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                    <Wifi className="h-3 w-3" aria-hidden="true" />
                    API Online · {health.generation_mode} mode
                  </span>
                )}
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold text-foreground tracking-tight text-balance">
                Transcript → SOAP Note
              </h1>
              <p className="mt-1.5 text-sm text-muted-foreground max-w-lg">
                Paste a raw doctor-patient conversation to generate a structured, clinically
                formatted SOAP note with automated validation and quality checks.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2 shrink-0">
              {health && (
                <>
                  {health.openai_configured && <Badge variant="success">OpenAI Ready</Badge>}
                  {health.anthropic_configured && <Badge variant="teal">Anthropic Ready</Badge>}
                  {isOfflinePreview && (
                    <Badge variant="warning" title="No API key configured — using deterministic rule-based generation">
                      Offline Preview
                    </Badge>
                  )}
                </>
              )}
              {state === "success" && result && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSaveNote}
                  disabled={historyState.isSaving}
                  className="gap-1.5"
                  aria-label="Save generated note to history"
                >
                  {historyState.isSaving ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Save className="h-3.5 w-3.5" />
                  )}
                  Save to History
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main layout */}
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {error && state === "error" && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
          <TranscriptInput
            transcript={transcript}
            onTranscriptChange={setTranscript}
            onGenerate={handleGenerate}
            isLoading={isLoading}
          />
          <OutputPanel
            isLoading={isLoading}
            result={result}
            error={error}
            transcript={transcript}
            onRetry={() => handleGenerate(transcript)}
          />
        </div>

        {/* Feature cards */}
        <div className="mt-10 pt-6 border-t border-border">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {FEATURE_CARDS.map((item, i) => {
              const Icon = item.icon;
              return (
                <div
                  key={i}
                  className="rounded-xl border border-border bg-card p-4 transition-all duration-200 hover:border-primary/30 hover:shadow-sm animate-fade-in"
                  style={{ animationDelay: `${i * 60}ms` }}
                >
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-soft text-primary-strong mb-3">
                    <Icon className="h-4 w-4" aria-hidden="true" />
                  </div>
                  <h3 className="text-sm font-semibold text-foreground mb-1">{item.title}</h3>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    {item.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </main>

      <ToastContainer toasts={toasts} dismiss={dismiss} />
    </div>
  );
}
