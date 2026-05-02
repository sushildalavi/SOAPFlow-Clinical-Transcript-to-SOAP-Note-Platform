import { useState } from "react";
import {
  CheckCircle2,
  Download,
  Copy,
  CheckCheck,
  FileJson,
  AlignLeft,
  Layers,
  Printer,
  AlertTriangle,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { SOAPNoteDisplay } from "@/components/soap/SOAPSectionCard";
import { SOAPSkeleton } from "@/components/soap/SOAPSkeleton";
import { WarningPanel } from "@/components/soap/WarningPanel";
import { MetadataPanel } from "@/components/soap/MetadataPanel";
import { EvaluationPanel } from "@/components/evaluation/EvaluationPanel";
import { copyToClipboard, exportAsJSON, exportAsText, printSOAPNote } from "@/lib/utils";
import type { GenerateResponse } from "@/types";

interface OutputPanelProps {
  isLoading: boolean;
  result: GenerateResponse | null;
  error: string | null;
  transcript?: string;
  onRetry?: () => void;
}

function friendlyError(raw: string): string {
  const lower = raw.toLowerCase();
  if (lower.includes("failed to fetch") || lower.includes("network")) {
    return "Could not reach the API. Check that the backend is running on port 8000.";
  }
  if (lower.includes("timeout")) {
    return "The request timed out. Try again or shorten the transcript.";
  }
  if (lower.includes("rate limit") || lower.includes("429")) {
    return "Rate limit exceeded. Wait a moment and try again.";
  }
  if (lower.includes("api key") || lower.includes("unauthorized") || lower.includes("401")) {
    return "API key issue. Check that OPENAI_API_KEY or ANTHROPIC_API_KEY is set.";
  }
  return raw;
}

export function OutputPanel({ isLoading, result, error, transcript = "", onRetry }: OutputPanelProps) {
  const [copiedJson, setCopiedJson] = useState(false);

  const handleCopyJson = async () => {
    if (!result?.raw_json) return;
    const success = await copyToClipboard(JSON.stringify(result.raw_json, null, 2));
    if (success) {
      setCopiedJson(true);
      setTimeout(() => setCopiedJson(false), 2000);
    }
  };

  const handleExportJSON = () => {
    if (!result?.raw_json) return;
    exportAsJSON(
      { soap_note: result.raw_json, metadata: result.metadata, warnings: result.warnings },
      "soap-note.json"
    );
  };

  const handleExportText = () => {
    if (!result?.soap_note) return;
    exportAsText(result.soap_note);
  };

  const handlePrint = () => {
    if (!result?.soap_note) return;
    printSOAPNote(result.soap_note, result.metadata);
  };

  // Empty state
  if (!isLoading && !result && !error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[360px] rounded-xl border-2 border-dashed border-border bg-secondary/30 p-8 animate-fade-in">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-secondary mb-4">
          <Layers className="h-7 w-7 text-muted-foreground" aria-hidden="true" />
        </div>
        <h3 className="text-sm font-semibold text-foreground mb-1">No note generated yet</h3>
        <p className="text-xs text-muted-foreground text-center max-w-[240px] leading-relaxed">
          Paste a transcript and click <span className="font-medium text-foreground">Generate SOAP Note</span> to see the structured output here.
        </p>
      </div>
    );
  }

  // Error state
  if (error && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] rounded-xl border border-destructive/30 bg-destructive/5 p-8 animate-fade-in">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 mb-4">
          <AlertTriangle className="h-6 w-6 text-destructive" aria-hidden="true" />
        </div>
        <h3 className="text-sm font-semibold text-destructive mb-1">Generation failed</h3>
        <p className="text-xs text-destructive/80 text-center max-w-[320px] mb-4 leading-relaxed">
          {friendlyError(error)}
        </p>
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry} className="gap-1.5">
            <RotateCcw className="h-3.5 w-3.5" />
            Try again
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <CheckCircle2 className="h-4 w-4 text-emerald-600" aria-hidden="true" />
          <h2 className="text-sm font-semibold text-foreground">SOAP Note</h2>
          {result && (
            <Badge variant="success" className="text-[10px]">
              Generated
            </Badge>
          )}
        </div>
        {result && (
          <div className="flex flex-wrap items-center gap-1 shrink-0">
            <Button
              variant="outline"
              size="xs"
              onClick={handlePrint}
              aria-label="Print or export as PDF"
              title="Print / Export as PDF"
            >
              <Printer className="h-3 w-3" />
              <span className="hidden sm:inline">Print</span>
            </Button>
            <Button
              variant="outline"
              size="xs"
              onClick={handleExportText}
              aria-label="Export as text file"
              title="Export as .txt"
            >
              <AlignLeft className="h-3 w-3" />
              <span className="hidden sm:inline">Text</span>
            </Button>
            <Button
              variant="outline"
              size="xs"
              onClick={handleExportJSON}
              aria-label="Export as JSON file"
              title="Export as JSON"
            >
              <Download className="h-3 w-3" />
              <span className="hidden sm:inline">JSON</span>
            </Button>
          </div>
        )}
      </div>

      {/* Loading skeleton */}
      {isLoading && <SOAPSkeleton />}

      {/* Result */}
      {result && (
        <Tabs defaultValue="formatted" className="w-full">
          <TabsList className="mb-3 h-8">
            <TabsTrigger value="formatted" className="text-xs h-6">
              <AlignLeft className="h-3 w-3 mr-1" />
              Formatted
            </TabsTrigger>
            <TabsTrigger value="json" className="text-xs h-6">
              <FileJson className="h-3 w-3 mr-1" />
              Raw JSON
            </TabsTrigger>
          </TabsList>

          <TabsContent value="formatted" className="mt-0 space-y-3">
            <MetadataPanel metadata={result.metadata} />
            {result.warnings.length > 0 && (
              <WarningPanel warnings={result.warnings} />
            )}
            <SOAPNoteDisplay note={result.soap_note} />
            <EvaluationPanel
              generatedNote={result.soap_note}
              transcript={transcript}
            />
          </TabsContent>

          <TabsContent value="json" className="mt-0">
            <div className="relative rounded-xl border border-border bg-[#0f1117] overflow-hidden shadow-sm">
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10">
                <span className="text-xs text-white/50 font-mono">soap-note.json</span>
                <Button
                  variant="ghost"
                  size="xs"
                  onClick={handleCopyJson}
                  className="text-white/60 hover:text-white hover:bg-white/10"
                  aria-label="Copy JSON to clipboard"
                >
                  {copiedJson ? (
                    <><CheckCheck className="h-3 w-3" /> Copied</>
                  ) : (
                    <><Copy className="h-3 w-3" /> Copy</>
                  )}
                </Button>
              </div>
              <pre className="overflow-auto p-4 text-xs text-emerald-400 font-mono leading-relaxed max-h-[480px] scrollbar-thin">
                {JSON.stringify(result.raw_json, null, 2)}
              </pre>
            </div>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
