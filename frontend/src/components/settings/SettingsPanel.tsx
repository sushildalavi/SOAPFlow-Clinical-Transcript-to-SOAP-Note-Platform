import { useEffect, useReducer } from "react";
import {
  Settings,
  X,
  Server,
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  BarChart2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import type { HealthResponse, StatsResponse } from "@/types";

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="rounded-lg bg-secondary/50 p-3">
      <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium mb-1">{label}</p>
      <p className="text-lg font-bold text-foreground">{value}</p>
      {sub && <p className="text-[11px] text-muted-foreground mt-0.5">{sub}</p>}
    </div>
  );
}

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const docsUrl = api.docsUrl();
  const [{ health, stats, loading, backendError }, dispatch] = useReducer(
    (
      state: {
        health: HealthResponse | null;
        stats: StatsResponse | null;
        loading: boolean;
        backendError: string | null;
      },
      action:
        | { type: "load_started" }
        | {
            type: "load_finished";
            health: HealthResponse | null;
            stats: StatsResponse | null;
          }
    ) => {
      if (action.type === "load_started") {
        return {
          ...state,
          loading: true,
          backendError: null,
        };
      }

      return {
        health: action.health,
        stats: action.stats,
        loading: false,
        backendError: action.health ? null : "Cannot reach backend API",
      };
    },
    {
      health: null,
      stats: null,
      loading: false,
      backendError: null,
    }
  );

  useEffect(() => {
    if (!isOpen) return;
    let cancelled = false;
    dispatch({ type: "load_started" });

    Promise.all([
      api.health().catch(() => null),
      api.getStats().catch(() => null),
    ]).then(([h, s]) => {
      if (cancelled) return;
      dispatch({
        type: "load_finished",
        health: h,
        stats: s,
      });
    });

    return () => {
      cancelled = true;
    };
  }, [isOpen]);

  const getModeColor = (mode: string): "success" | "teal" | "warning" => {
    if (mode === "openai") return "success";
    if (mode === "anthropic") return "teal";
    return "warning";
  };

  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm" onClick={onClose} />
      )}

      <div
        className={cn(
          "fixed right-0 top-0 z-50 h-full w-full max-w-sm bg-white shadow-2xl",
          "flex flex-col border-l border-border",
          "transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-secondary/30">
          <div className="flex items-center gap-2">
            <Settings className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            <span className="text-sm font-semibold text-foreground">System Status</span>
          </div>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onClose}
            aria-label="Close system status panel"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
          {loading ? (
            <div className="space-y-4" role="status" aria-label="Loading system status">
              <div className="rounded-xl border border-border overflow-hidden">
                <div className="px-3 py-2 bg-secondary/30 border-b border-border">
                  <Skeleton className="h-3 w-24" />
                </div>
                <div className="p-3 space-y-2">
                  <Skeleton className="h-3 w-32" />
                  <Skeleton className="h-3 w-28" />
                  <Skeleton className="h-3 w-36" />
                </div>
              </div>
              <div className="rounded-xl border border-border overflow-hidden">
                <div className="px-3 py-2 bg-secondary/30 border-b border-border">
                  <Skeleton className="h-3 w-28" />
                </div>
                <div className="p-3 grid grid-cols-2 gap-2">
                  {[0, 1, 2, 3].map((i) => (
                    <div key={i} className="rounded-lg bg-secondary/50 p-3">
                      <Skeleton className="h-2.5 w-16 mb-2" />
                      <Skeleton className="h-5 w-12" />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <>
              {/* Backend status */}
              <div className="rounded-xl border border-border overflow-hidden">
                <div className="px-3 py-2 bg-secondary/30 border-b border-border flex items-center gap-2">
                  <Server className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs font-semibold text-foreground">Backend API</span>
                </div>
                <div className="p-3 space-y-2">
                  {backendError ? (
                    <div className="flex items-center gap-2 text-destructive">
                      <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                      <span className="text-xs">{backendError}</span>
                    </div>
                  ) : health ? (
                    <>
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                        <span className="text-xs text-emerald-700 font-medium">API Online</span>
                        <Badge variant="outline" className="text-[9px] ml-auto">v{health.version}</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground">Generation Mode</span>
                        <Badge variant={getModeColor(health.generation_mode)} className="text-[10px]">
                          {health.generation_mode}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground">OpenAI</span>
                        <span className={cn("text-xs font-medium", health.openai_configured ? "text-emerald-600" : "text-muted-foreground")}>
                          {health.openai_configured ? "Configured" : "Not configured"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground">Anthropic</span>
                        <span className={cn("text-xs font-medium", health.anthropic_configured ? "text-purple-600" : "text-muted-foreground")}>
                          {health.anthropic_configured ? "Configured" : "Not configured"}
                        </span>
                      </div>
                    </>
                  ) : null}
                </div>
              </div>

              {/* Usage stats */}
              {stats && (
                <div className="rounded-xl border border-border overflow-hidden">
                  <div className="px-3 py-2 bg-secondary/30 border-b border-border flex items-center gap-2">
                    <BarChart2 className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="text-xs font-semibold text-foreground">Usage Statistics</span>
                  </div>
                  <div className="p-3 grid grid-cols-2 gap-2">
                    <StatCard label="Total Notes" value={stats.total_notes_saved} />
                    <StatCard
                      label="Avg Time"
                      value={stats.avg_processing_time_ms ? `${Math.round(stats.avg_processing_time_ms)}ms` : "—"}
                    />
                    <StatCard
                      label="Avg Sections"
                      value={stats.avg_sections_populated ? `${stats.avg_sections_populated.toFixed(1)}/4` : "—"}
                    />
                    <StatCard
                      label="Latest"
                      value={stats.latest_note_at ? new Date(stats.latest_note_at).toLocaleDateString() : "None"}
                    />
                  </div>
                  {Object.keys(stats.by_generation_mode).length > 0 && (
                    <div className="px-3 pb-3 space-y-1.5">
                      <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium">By Mode</p>
                      {Object.entries(stats.by_generation_mode).map(([mode, count]) => (
                        <div key={mode} className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground capitalize">{mode}</span>
                          <span className="font-semibold text-foreground">{count} notes</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* API docs link */}
              <a
                href={docsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 rounded-xl border border-border hover:bg-secondary/30 transition-colors group"
              >
                <div>
                  <p className="text-xs font-semibold text-foreground">API Documentation</p>
                  <p className="text-[11px] text-muted-foreground">OpenAPI / Swagger UI</p>
                </div>
                <ExternalLink className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
              </a>
            </>
          )}
        </div>
      </div>
    </>
  );
}
