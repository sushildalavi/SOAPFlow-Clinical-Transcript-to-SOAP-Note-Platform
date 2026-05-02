import { useState } from "react";
import {
  BarChart2,
  ChevronDown,
  ChevronUp,
  Loader2,
  AlertCircle,
  CheckCircle2,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import type { SOAPNote } from "@/types";

interface EvaluationPanelProps {
  generatedNote: SOAPNote | null;
  transcript: string;
}

interface EvaluationResult {
  success: boolean;
  scores: {
    rouge_1?: number | null;
    rouge_2?: number | null;
    rouge_l?: number | null;
    bleu?: number | null;
    section_scores?: Record<string, number | null> | null;
  };
  summary: string;
}

function ScoreBar({ label, value }: { label: string; value: number | null | undefined }) {
  if (value === null || value === undefined) return null;
  const pct = Math.round(value * 100);
  const color =
    pct >= 70 ? "bg-emerald-500" : pct >= 40 ? "bg-amber-400" : "bg-rose-400";
  const textColor =
    pct >= 70 ? "text-emerald-700" : pct >= 40 ? "text-amber-700" : "text-rose-700";

  return (
    <div className="flex items-center gap-3">
      <span className="w-24 text-xs text-muted-foreground shrink-0">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-secondary overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-500", color)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={cn("text-xs font-semibold w-10 text-right", textColor)}>
        {(value * 100).toFixed(1)}%
      </span>
    </div>
  );
}

export function EvaluationPanel({ generatedNote, transcript }: EvaluationPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [referenceText, setReferenceText] = useState("");
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [evalResult, setEvalResult] = useState<EvaluationResult | null>(null);
  const [evalError, setEvalError] = useState<string | null>(null);

  const handleEvaluate = async () => {
    if (!generatedNote) return;
    setIsEvaluating(true);
    setEvalError(null);
    setEvalResult(null);
    try {
      let referenceNote: SOAPNote | undefined;
      if (referenceText.trim()) {
        // Parse reference text as sections if possible
        referenceNote = undefined; // user provides JSON or we skip
        try {
          referenceNote = JSON.parse(referenceText) as SOAPNote;
        } catch {
          // Try to parse plain text as a note
          referenceNote = undefined;
        }
      }

      const result = await api.evaluate(
        transcript,
        generatedNote,
        referenceNote
      );
      setEvalResult(result as EvaluationResult);
    } catch (err) {
      setEvalError(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      setIsEvaluating(false);
    }
  };

  if (!generatedNote) return null;

  const heuristicScore = evalResult?.scores?.section_scores?.heuristic_completeness;
  const hasReferenceScores = evalResult?.scores?.rouge_l !== undefined && evalResult?.scores?.rouge_l !== null;

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden">
      <button
        onClick={() => setIsOpen((v) => !v)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-secondary/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <BarChart2 className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-semibold text-foreground">Quality Evaluation</span>
          {evalResult && (
            <Badge variant="success" className="text-[10px]">
              Scored
            </Badge>
          )}
        </div>
        {isOpen ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      {isOpen && (
        <div className="px-4 pb-4 space-y-4 border-t border-border animate-fade-in">
          {/* Info banner */}
          <Alert variant="info" className="mt-3 py-2.5 px-3 [&>svg]:left-3 [&>svg]:top-3 [&>svg~*]:pl-6">
            <Info className="h-3.5 w-3.5" />
            <AlertDescription className="text-[11px] leading-relaxed">
              Optionally paste a reference SOAP note (JSON) to get ROUGE / BLEU scores.
              Without a reference, a heuristic completeness score is computed.
            </AlertDescription>
          </Alert>

          {/* Reference note input */}
          <div>
            <label
              htmlFor="reference-note-input"
              className="text-xs font-medium text-foreground block mb-1.5"
            >
              Reference Note{" "}
              <span className="text-muted-foreground font-normal">(optional — JSON format)</span>
            </label>
            <Textarea
              id="reference-note-input"
              value={referenceText}
              onChange={(e) => setReferenceText(e.target.value)}
              placeholder={`{"subjective": "...", "objective": "...", "assessment": "...", "plan": "..."}`}
              className="font-mono text-xs min-h-[80px] resize-none bg-white"
            />
          </div>

          <Button
            onClick={handleEvaluate}
            disabled={isEvaluating || !generatedNote}
            size="sm"
            variant="outline"
            className="w-full gap-2"
            aria-label="Run quality evaluation"
          >
            {isEvaluating ? (
              <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Evaluating…</>
            ) : (
              <><BarChart2 className="h-3.5 w-3.5" /> Run Evaluation</>
            )}
          </Button>

          {/* Error */}
          {evalError && (
            <Alert variant="destructive" className="py-2.5 px-3 [&>svg]:left-3 [&>svg]:top-3 [&>svg~*]:pl-6">
              <AlertCircle className="h-3.5 w-3.5" />
              <AlertDescription className="text-xs">{evalError}</AlertDescription>
            </Alert>
          )}

          {/* Results */}
          {evalResult && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                <p className="text-xs text-muted-foreground">{evalResult.summary}</p>
              </div>

              {hasReferenceScores ? (
                <div className="space-y-2.5 p-3 rounded-lg bg-secondary/30">
                  <p className="text-[11px] font-semibold text-foreground uppercase tracking-wider">
                    ROUGE Scores
                  </p>
                  <ScoreBar label="ROUGE-1" value={evalResult.scores.rouge_1} />
                  <ScoreBar label="ROUGE-2" value={evalResult.scores.rouge_2} />
                  <ScoreBar label="ROUGE-L" value={evalResult.scores.rouge_l} />
                  {evalResult.scores.bleu !== null && evalResult.scores.bleu !== undefined && (
                    <ScoreBar label="BLEU" value={evalResult.scores.bleu} />
                  )}
                  {evalResult.scores.section_scores && (
                    <>
                      <p className="text-[11px] font-semibold text-foreground uppercase tracking-wider mt-2">
                        Section-Level ROUGE-L
                      </p>
                      {Object.entries(evalResult.scores.section_scores).map(([section, score]) => (
                        <ScoreBar key={section} label={section} value={score} />
                      ))}
                    </>
                  )}
                </div>
              ) : (
                heuristicScore !== undefined && heuristicScore !== null && (
                  <div className="p-3 rounded-lg bg-secondary/30 space-y-2">
                    <p className="text-[11px] font-semibold text-foreground uppercase tracking-wider">
                      Heuristic Completeness
                    </p>
                    <ScoreBar label="Completeness" value={heuristicScore} />
                  </div>
                )
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
