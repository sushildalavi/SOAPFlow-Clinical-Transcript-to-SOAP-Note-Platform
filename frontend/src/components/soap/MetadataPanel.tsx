import { Clock, FileText, Cpu, CheckCircle2, Layers } from "lucide-react";
import { cn, formatProcessingTime } from "@/lib/utils";
import type { GenerationMetadata } from "@/types";

const MODE_LABELS: Record<string, { label: string; className: string }> = {
  "openai": { label: "OpenAI GPT-4o", className: "bg-emerald-50 text-emerald-700 border-emerald-200" },
  "anthropic": { label: "Anthropic Claude", className: "bg-violet-50 text-violet-700 border-violet-200" },
  "demo": { label: "Demo Mode", className: "bg-amber-50 text-amber-700 border-amber-200" },
  "demo-rule-based": { label: "Demo Mode", className: "bg-amber-50 text-amber-700 border-amber-200" },
};

interface MetadataPanelProps {
  metadata: GenerationMetadata;
}

export function MetadataPanel({ metadata }: MetadataPanelProps) {
  const modeInfo = MODE_LABELS[metadata.mode] ?? MODE_LABELS[metadata.model] ?? {
    label: metadata.mode,
    className: "bg-secondary text-muted-foreground border-border",
  };

  const stats = [
    {
      icon: FileText,
      label: "Input",
      value: `${metadata.transcript_word_count.toLocaleString()} words`,
    },
    {
      icon: Layers,
      label: "Output",
      value: `${metadata.note_word_count.toLocaleString()} words`,
    },
    {
      icon: CheckCircle2,
      label: "Sections",
      value: `${metadata.sections_populated} / 4`,
      valueClass: metadata.sections_populated === 4 ? "text-emerald-600" : "text-amber-600",
    },
    {
      icon: Clock,
      label: "Time",
      value: formatProcessingTime(metadata.processing_time_ms),
    },
  ];

  return (
    <div className="rounded-xl border border-border bg-card px-4 py-3">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
        {/* Mode badge */}
        <div className="flex items-center gap-2">
          <Cpu className="h-3.5 w-3.5 text-muted-foreground" />
          <span
            className={cn(
              "inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-semibold",
              modeInfo.className
            )}
          >
            {modeInfo.label}
          </span>
        </div>

        <div className="h-4 w-px bg-border hidden sm:block" />

        {/* Stats */}
        {stats.map((stat, i) => {
          const Icon = stat.icon;
          return (
            <div key={i} className="flex items-center gap-1.5">
              <Icon className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">{stat.label}:</span>
              <span className={cn("text-xs font-semibold text-foreground", stat.valueClass)}>
                {stat.value}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
