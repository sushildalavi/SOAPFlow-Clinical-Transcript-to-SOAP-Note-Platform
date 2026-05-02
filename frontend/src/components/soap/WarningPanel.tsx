import { AlertTriangle, Info, XCircle, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import type { ValidationWarning } from "@/types";

const severityConfig = {
  error: {
    icon: XCircle,
    containerClass: "border-red-200 bg-red-50",
    iconClass: "text-red-600",
    textClass: "text-red-800",
    badgeClass: "bg-red-100 text-red-700 border-red-200",
    label: "Error",
  },
  warning: {
    icon: AlertTriangle,
    containerClass: "border-amber-200 bg-amber-50",
    iconClass: "text-amber-600",
    textClass: "text-amber-800",
    badgeClass: "bg-amber-100 text-amber-700 border-amber-200",
    label: "Warning",
  },
  info: {
    icon: Info,
    containerClass: "border-sky-200 bg-sky-50",
    iconClass: "text-sky-600",
    textClass: "text-sky-800",
    badgeClass: "bg-sky-100 text-sky-700 border-sky-200",
    label: "Info",
  },
};

interface WarningPanelProps {
  warnings: ValidationWarning[];
}

export function WarningPanel({ warnings }: WarningPanelProps) {
  const [expanded, setExpanded] = useState(true);

  if (warnings.length === 0) return null;

  const errors = warnings.filter((w) => w.severity === "error");
  const warnCount = warnings.filter((w) => w.severity === "warning").length;
  const infoCount = warnings.filter((w) => w.severity === "info").length;

  const headerClass =
    errors.length > 0
      ? "border-red-200 bg-red-50"
      : warnCount > 0
      ? "border-amber-200 bg-amber-50"
      : "border-sky-200 bg-sky-50";

  const headerTextClass =
    errors.length > 0
      ? "text-red-800"
      : warnCount > 0
      ? "text-amber-800"
      : "text-sky-800";

  return (
    <div className="rounded-xl border overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded((v) => !v)}
        className={cn(
          "w-full flex items-center justify-between px-4 py-3 transition-colors hover:brightness-95",
          headerClass
        )}
      >
        <div className="flex items-center gap-2">
          <AlertTriangle className={cn("h-4 w-4", headerTextClass)} />
          <span className={cn("text-sm font-semibold", headerTextClass)}>
            {warnings.length} Validation Notice{warnings.length !== 1 ? "s" : ""}
          </span>
          <div className="flex items-center gap-1 ml-1">
            {errors.length > 0 && (
              <span className="inline-flex items-center rounded-full border border-red-200 bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-700">
                {errors.length} error{errors.length !== 1 ? "s" : ""}
              </span>
            )}
            {warnCount > 0 && (
              <span className="inline-flex items-center rounded-full border border-amber-200 bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700">
                {warnCount} warning{warnCount !== 1 ? "s" : ""}
              </span>
            )}
            {infoCount > 0 && (
              <span className="inline-flex items-center rounded-full border border-sky-200 bg-sky-100 px-2 py-0.5 text-xs font-semibold text-sky-700">
                {infoCount} info
              </span>
            )}
          </div>
        </div>
        {expanded ? (
          <ChevronUp className={cn("h-4 w-4", headerTextClass)} />
        ) : (
          <ChevronDown className={cn("h-4 w-4", headerTextClass)} />
        )}
      </button>

      {/* Warning list */}
      {expanded && (
        <div className="divide-y divide-border bg-white">
          {warnings.map((warning, index) => {
            const config = severityConfig[warning.severity];
            const Icon = config.icon;
            return (
              <div key={index} className="flex items-start gap-3 px-4 py-3">
                <Icon className={cn("h-4 w-4 mt-0.5 shrink-0", config.iconClass)} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full border px-1.5 py-0 text-[10px] font-bold uppercase tracking-wider",
                        config.badgeClass
                      )}
                    >
                      {config.label}
                    </span>
                    {warning.field && (
                      <span className="text-[10px] text-muted-foreground font-mono uppercase">
                        {warning.field}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-foreground">{warning.message}</p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
