import { useState } from "react";
import { Copy, CheckCheck } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { cn, copyToClipboard } from "@/lib/utils";

interface SOAPSectionConfig {
  key: "subjective" | "objective" | "assessment" | "plan";
  label: string;
  letter: string;
  description: string;
  accentClass: string;
  letterBg: string;
  letterText: string;
}

const SECTION_CONFIG: SOAPSectionConfig[] = [
  {
    key: "subjective",
    label: "Subjective",
    letter: "S",
    description: "Patient-reported symptoms and history",
    accentClass: "border-l-violet-400",
    letterBg: "bg-violet-50",
    letterText: "text-violet-700",
  },
  {
    key: "objective",
    label: "Objective",
    letter: "O",
    description: "Clinical findings and measurable data",
    accentClass: "border-l-sky-400",
    letterBg: "bg-sky-50",
    letterText: "text-sky-700",
  },
  {
    key: "assessment",
    label: "Assessment",
    letter: "A",
    description: "Diagnosis and clinical impression",
    accentClass: "border-l-amber-400",
    letterBg: "bg-amber-50",
    letterText: "text-amber-700",
  },
  {
    key: "plan",
    label: "Plan",
    letter: "P",
    description: "Treatment and follow-up plan",
    accentClass: "border-l-emerald-400",
    letterBg: "bg-emerald-50",
    letterText: "text-emerald-700",
  },
];

interface SOAPSectionCardProps {
  sectionKey: "subjective" | "objective" | "assessment" | "plan";
  content: string;
  index?: number;
}

export function SOAPSectionCard({ sectionKey, content, index = 0 }: SOAPSectionCardProps) {
  const [copied, setCopied] = useState(false);
  const config = SECTION_CONFIG.find((c) => c.key === sectionKey)!;
  const isEmpty = !content || content === "Not documented.";

  const handleCopy = async () => {
    const success = await copyToClipboard(content);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <Card
      className={cn(
        "group border-l-4 transition-all duration-200 hover:shadow-md hover:-translate-y-px animate-slide-up",
        config.accentClass
      )}
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <CardHeader className="pb-3 pt-5 px-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-sm font-bold",
                config.letterBg,
                config.letterText
              )}
              aria-hidden="true"
            >
              {config.letter}
            </div>
            <div>
              <h3 className="text-sm font-semibold text-foreground">{config.label}</h3>
              <p className="text-xs text-muted-foreground">{config.description}</p>
            </div>
          </div>
          {!isEmpty && (
            <Button
              variant="ghost"
              size="icon-sm"
              className="shrink-0 text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity"
              onClick={handleCopy}
              aria-label={`Copy ${config.label} section to clipboard`}
              title="Copy to clipboard"
            >
              {copied ? (
                <CheckCheck className="h-3.5 w-3.5 text-emerald-600" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="px-5 pb-5">
        {isEmpty ? (
          <p className="text-sm text-muted-foreground italic">Not documented.</p>
        ) : (
          <p className="text-sm text-foreground leading-relaxed whitespace-pre-line">{content}</p>
        )}
      </CardContent>
    </Card>
  );
}

interface SOAPNoteDisplayProps {
  note: {
    subjective: string;
    objective: string;
    assessment: string;
    plan: string;
  };
}

export function SOAPNoteDisplay({ note }: SOAPNoteDisplayProps) {
  return (
    <div className="grid gap-3">
      {SECTION_CONFIG.map((config, i) => (
        <SOAPSectionCard
          key={config.key}
          sectionKey={config.key}
          content={note[config.key]}
          index={i}
        />
      ))}
    </div>
  );
}
