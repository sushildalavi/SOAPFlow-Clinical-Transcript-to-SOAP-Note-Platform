import { useState, useCallback } from "react";
import {
  Sparkles,
  Trash2,
  FlaskConical,
  ChevronDown,
  FileText,
  Loader2,
  BrainCircuit,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { cn, countWords } from "@/lib/utils";
import { api } from "@/lib/api";
import type { DemoListItem, GenerationMode } from "@/types";

interface TranscriptInputProps {
  transcript: string;
  onTranscriptChange: (value: string) => void;
  onGenerate: (transcript: string, mode?: GenerationMode) => void;
  isLoading: boolean;
}

const MODEL_OPTIONS: { value: GenerationMode; label: string; description: string; color: string }[] = [
  { value: "demo", label: "Demo Mode", description: "Rule-based, no API key needed", color: "text-slate-600" },
  { value: "openai", label: "OpenAI GPT-4o", description: "Best quality", color: "text-emerald-600" },
  { value: "anthropic", label: "Claude claude-opus-4-6", description: "High quality", color: "text-purple-600" },
];

export function TranscriptInput({
  transcript,
  onTranscriptChange,
  onGenerate,
  isLoading,
}: TranscriptInputProps) {
  const [demoList, setDemoList] = useState<DemoListItem[]>([]);
  const [showDemoMenu, setShowDemoMenu] = useState(false);
  const [showModelMenu, setShowModelMenu] = useState(false);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [selectedMode, setSelectedMode] = useState<GenerationMode | null>(null);

  const wordCount = countWords(transcript);
  const charCount = transcript.length;
  const canGenerate = transcript.trim().length >= 50 && !isLoading;

  const selectedModelOption = MODEL_OPTIONS.find((m) => m.value === selectedMode);

  const handleLoadDemoMenu = async () => {
    if (demoList.length === 0) {
      try {
        const list = await api.listDemoTranscripts();
        setDemoList(list);
      } catch {
        // fallback
      }
    }
    setShowDemoMenu((v) => !v);
    setShowModelMenu(false);
  };

  const handleLoadDemo = useCallback(
    async (index: number) => {
      setLoadingDemo(true);
      setShowDemoMenu(false);
      try {
        const demo = await api.getDemoTranscript(index);
        onTranscriptChange(demo.transcript);
      } catch {
        // ignore
      } finally {
        setLoadingDemo(false);
      }
    },
    [onTranscriptChange]
  );

  const handleClear = () => {
    onTranscriptChange("");
  };

  const handleGenerate = () => {
    onGenerate(transcript, selectedMode ?? undefined);
    setShowDemoMenu(false);
    setShowModelMenu(false);
  };

  return (
    <div className="flex flex-col gap-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <h2 className="text-sm font-semibold text-foreground">Transcript Input</h2>
          {transcript && (
            <Badge variant="outline" className="text-[10px]">
              {wordCount} words · {charCount} chars
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          {/* Model selector */}
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              onClick={() => { setShowModelMenu((v) => !v); setShowDemoMenu(false); }}
              className="h-7 text-xs gap-1"
              title="Select AI model"
            >
              <BrainCircuit className="h-3 w-3" />
              <span className="hidden sm:inline">{selectedModelOption?.label ?? "Auto"}</span>
              <ChevronDown className="h-2.5 w-2.5" />
            </Button>
            {showModelMenu && (
              <div className="absolute right-0 top-full mt-1 z-50 w-56 rounded-xl border border-border bg-white shadow-lg py-1">
                <div className="px-3 py-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  Generation Mode
                </div>
                <button
                  onClick={() => { setSelectedMode(null); setShowModelMenu(false); }}
                  className="w-full text-left px-3 py-2 hover:bg-secondary transition-colors flex items-center justify-between"
                >
                  <div>
                    <div className="text-xs font-medium text-foreground">Auto (Server Default)</div>
                    <div className="text-[11px] text-muted-foreground">Uses server configuration</div>
                  </div>
                  {selectedMode === null && <Check className="h-3.5 w-3.5 text-[hsl(199,89%,40%)]" />}
                </button>
                {MODEL_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => { setSelectedMode(opt.value); setShowModelMenu(false); }}
                    className="w-full text-left px-3 py-2 hover:bg-secondary transition-colors flex items-center justify-between"
                  >
                    <div>
                      <div className={cn("text-xs font-medium", opt.color)}>{opt.label}</div>
                      <div className="text-[11px] text-muted-foreground">{opt.description}</div>
                    </div>
                    {selectedMode === opt.value && <Check className="h-3.5 w-3.5 text-[hsl(199,89%,40%)]" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Demo loader */}
          <div className="relative">
            <Button
              variant="outline"
              size="sm"
              onClick={handleLoadDemoMenu}
              disabled={loadingDemo}
              className="h-7 text-xs gap-1"
            >
              {loadingDemo ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <FlaskConical className="h-3 w-3" />
              )}
              Demo
              <ChevronDown className="h-2.5 w-2.5" />
            </Button>
            {showDemoMenu && (
              <div className="absolute right-0 top-full mt-1 z-50 w-72 rounded-xl border border-border bg-white shadow-lg py-1">
                <div className="px-3 py-1.5 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                  Sample Transcripts
                </div>
                {demoList.length === 0 ? (
                  <div className="px-3 py-2 text-xs text-muted-foreground">Loading demos...</div>
                ) : (
                  demoList.map((item) => (
                    <button
                      key={item.index}
                      onClick={() => handleLoadDemo(item.index)}
                      className="w-full text-left px-3 py-2.5 hover:bg-secondary transition-colors"
                    >
                      <div className="text-xs font-semibold text-foreground">{item.title}</div>
                      <div className="text-[11px] text-muted-foreground mt-0.5 line-clamp-1">
                        {item.description}
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>

          {/* Clear */}
          {transcript && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleClear}
              className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive"
              title="Clear transcript"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>

      {/* Active mode indicator */}
      {selectedMode && (
        <div className={cn(
          "flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1 rounded-lg w-fit",
          selectedMode === "openai" && "bg-emerald-50 text-emerald-700",
          selectedMode === "anthropic" && "bg-purple-50 text-purple-700",
          selectedMode === "demo" && "bg-slate-100 text-slate-600",
        )}>
          <BrainCircuit className="h-3 w-3" />
          Using: {MODEL_OPTIONS.find((m) => m.value === selectedMode)?.label}
          <button
            onClick={() => setSelectedMode(null)}
            className="ml-1 opacity-60 hover:opacity-100"
          >
            ×
          </button>
        </div>
      )}

      {/* Textarea */}
      <div
        className="relative"
        onClick={() => { setShowDemoMenu(false); setShowModelMenu(false); }}
      >
        <Textarea
          value={transcript}
          onChange={(e) => onTranscriptChange(e.target.value)}
          placeholder={`Paste your doctor-patient conversation here...\n\nExample:\nDoctor: What brings you in today?\nPatient: I've had a headache for 3 days...\n\nOr click "Demo" to load a sample transcript.`}
          className={cn(
            "min-h-[280px] resize-none font-mono text-xs leading-relaxed bg-white",
            "placeholder:font-sans placeholder:text-sm placeholder:leading-normal",
            transcript.length > 0 && "border-[hsl(199,89%,40%)]/30"
          )}
        />
        {/* Char limit indicator */}
        {transcript.length > 15000 && (
          <div className="absolute bottom-3 right-3">
            <Badge
              variant={transcript.length > 19000 ? "destructive" : "warning"}
              className="text-[10px]"
            >
              {transcript.length}/20000
            </Badge>
          </div>
        )}
      </div>

      {/* Generate button */}
      <Button
        onClick={handleGenerate}
        disabled={!canGenerate}
        size="lg"
        className={cn(
          "w-full font-semibold gap-2 transition-all",
          canGenerate && "shadow-md shadow-[hsl(199,89%,40%)]/20"
        )}
      >
        {isLoading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Generating SOAP Note...
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4" />
            Generate SOAP Note
            {selectedMode && <span className="text-xs font-normal opacity-75">· {selectedMode}</span>}
          </>
        )}
      </Button>

      {!transcript && (
        <p className="text-xs text-center text-muted-foreground">
          Minimum 50 characters required · Supports any conversation format
        </p>
      )}
    </div>
  );
}
