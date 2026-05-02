import { useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { NoteRecord, GenerateResponse } from "@/types";

interface UseHistoryReturn {
  notes: NoteRecord[];
  total: number;
  isLoading: boolean;
  isSaving: boolean;
  fetchHistory: () => Promise<void>;
  saveCurrentNote: (transcript: string, result: GenerateResponse) => Promise<NoteRecord | null>;
  deleteNote: (id: number) => Promise<void>;
  clearHistory: () => Promise<void>;
}

export function useHistory(): UseHistoryReturn {
  const [notes, setNotes] = useState<NoteRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const fetchHistory = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.listHistory(50, 0);
      setNotes(data.notes);
      setTotal(data.total);
    } catch {
      // silently ignore if backend offline
    } finally {
      setIsLoading(false);
    }
  }, []);

  const saveCurrentNote = useCallback(
    async (transcript: string, result: GenerateResponse): Promise<NoteRecord | null> => {
      setIsSaving(true);
      try {
        const saved = await api.saveNote({
          transcript,
          soap_note: result.soap_note,
          metadata: result.metadata,
          warnings: result.warnings,
        });
        // Prepend to local list so it shows immediately
        setNotes((prev) => [saved, ...prev]);
        setTotal((prev) => prev + 1);
        return saved;
      } catch {
        return null;
      } finally {
        setIsSaving(false);
      }
    },
    []
  );

  const deleteNote = useCallback(async (id: number) => {
    try {
      await api.deleteNote(id);
      setNotes((prev) => prev.filter((n) => n.id !== id));
      setTotal((prev) => Math.max(0, prev - 1));
    } catch {
      // ignore
    }
  }, []);

  const clearHistory = useCallback(async () => {
    try {
      await api.clearHistory();
      setNotes([]);
      setTotal(0);
    } catch {
      // ignore
    }
  }, []);

  return {
    notes,
    total,
    isLoading,
    isSaving,
    fetchHistory,
    saveCurrentNote,
    deleteNote,
    clearHistory,
  };
}
