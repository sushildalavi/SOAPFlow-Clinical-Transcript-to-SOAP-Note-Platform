import { useEffect, useCallback } from "react";
import {
  History,
  Trash2,
  RotateCcw,
  Clock,
  FileText,
  X,
  BookOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { NoteRecord } from "@/types";
import type { useHistory } from "@/hooks/useHistory";

interface HistoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
  historyState: ReturnType<typeof useHistory>;
  onLoadNote: (note: NoteRecord) => void;
}

function formatRelativeTime(isoString: string | null): string {
  if (!isoString) return "Unknown";
  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

function formatAbsoluteTime(isoString: string | null): string {
  if (!isoString) return "";
  const date = new Date(isoString);
  return date.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function getModeColor(mode: string): string {
  if (mode === "openai") return "text-emerald-700 bg-emerald-50 border-emerald-200";
  if (mode === "anthropic") return "text-purple-700 bg-purple-50 border-purple-200";
  return "text-slate-600 bg-slate-100 border-slate-200";
}

export function HistoryPanel({ isOpen, onClose, historyState, onLoadNote }: HistoryPanelProps) {
  const { notes, total, isLoading, deleteNote, clearHistory, fetchHistory } = historyState;

  useEffect(() => {
    if (isOpen) {
      fetchHistory();
    }
  }, [isOpen, fetchHistory]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  const handleClearWithConfirm = useCallback(() => {
    if (window.confirm("Delete all saved notes? This cannot be undone.")) {
      clearHistory();
    }
  }, [clearHistory]);

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm animate-fade-in"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Slide-in panel */}
      <aside
        className={cn(
          "fixed right-0 top-0 z-50 h-full w-full max-w-sm bg-white shadow-2xl",
          "flex flex-col border-l border-border",
          "transition-transform duration-300 ease-in-out",
          isOpen ? "translate-x-0" : "translate-x-full"
        )}
        aria-label="Note history"
        aria-hidden={!isOpen}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-secondary/30">
          <div className="flex items-center gap-2">
            <History className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            <span className="text-sm font-semibold text-foreground">Note History</span>
            {total > 0 && (
              <Badge variant="outline" className="text-[10px]">
                {total}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1">
            {notes.length > 0 && (
              <Button
                variant="ghost"
                size="xs"
                onClick={handleClearWithConfirm}
                className="text-muted-foreground hover:text-destructive"
                aria-label="Clear all saved notes"
                title="Clear all history"
              >
                <Trash2 className="h-3 w-3" />
                <span>Clear all</span>
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={onClose}
              aria-label="Close history panel"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          {isLoading ? (
            <div className="divide-y divide-border" role="status" aria-label="Loading history">
              {[0, 1, 2, 3].map((i) => (
                <div key={i} className="px-4 py-3">
                  <Skeleton className="h-3.5 w-3/4 mb-2" />
                  <Skeleton className="h-2.5 w-full mb-1" />
                  <Skeleton className="h-2.5 w-5/6 mb-2" />
                  <div className="flex gap-2">
                    <Skeleton className="h-3 w-12 rounded" />
                    <Skeleton className="h-3 w-16 rounded" />
                  </div>
                </div>
              ))}
            </div>
          ) : notes.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center px-6 animate-fade-in">
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-secondary mb-3">
                <BookOpen className="h-6 w-6 text-muted-foreground" aria-hidden="true" />
              </div>
              <p className="text-sm font-medium text-foreground mb-1">No notes saved yet</p>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Generate a SOAP note and click <span className="font-medium text-foreground">Save to History</span> to store it here.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {notes.map((note) => (
                <HistoryItem
                  key={note.id}
                  note={note}
                  onLoad={() => { onLoadNote(note); onClose(); }}
                  onDelete={() => deleteNote(note.id)}
                />
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t border-border bg-secondary/30">
          <button
            type="button"
            onClick={fetchHistory}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors rounded px-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Refresh history"
          >
            <RotateCcw className="h-3 w-3" />
            Refresh
          </button>
        </div>
      </aside>
    </>
  );
}

interface HistoryItemProps {
  note: NoteRecord;
  onLoad: () => void;
  onDelete: () => void;
}

function HistoryItem({ note, onLoad, onDelete }: HistoryItemProps) {
  const preview = note.soap_note.assessment.slice(0, 80) + (note.soap_note.assessment.length > 80 ? "…" : "");
  const absolute = formatAbsoluteTime(note.created_at);

  return (
    <Card className="group rounded-none border-0 border-b border-border last:border-b-0 px-4 py-3 hover:bg-secondary/40 transition-colors shadow-none">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold text-foreground truncate mb-0.5">{note.title}</p>
          {preview && (
            <p className="text-[11px] text-muted-foreground line-clamp-2 mb-1.5">{preview}</p>
          )}
          <div className="flex items-center gap-2 flex-wrap">
            <span className={cn("text-[10px] font-medium px-1.5 py-0.5 rounded border", getModeColor(note.metadata.mode))}>
              {note.metadata.mode}
            </span>
            <span
              className="flex items-center gap-0.5 text-[10px] text-muted-foreground"
              title={absolute}
            >
              <Clock className="h-2.5 w-2.5" aria-hidden="true" />
              {formatRelativeTime(note.created_at)}
            </span>
            {note.metadata.transcript_word_count && (
              <span className="flex items-center gap-0.5 text-[10px] text-muted-foreground">
                <FileText className="h-2.5 w-2.5" aria-hidden="true" />
                {note.metadata.transcript_word_count}w
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
          <Button
            variant="outline"
            size="xs"
            onClick={onLoad}
            aria-label={`Load note: ${note.title}`}
          >
            Load
          </Button>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onDelete}
            className="text-muted-foreground hover:text-destructive"
            aria-label={`Delete note: ${note.title}`}
          >
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
