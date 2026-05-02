import { useState, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import type { GenerateResponse, AppState, GenerationMode } from "@/types";

interface UseGenerateReturn {
  state: AppState;
  result: GenerateResponse | null;
  error: string | null;
  generate: (transcript: string, mode?: GenerationMode) => Promise<GenerateResponse | null>;
  reset: () => void;
}

export function useGenerate(): UseGenerateReturn {
  const [state, setState] = useState<AppState>("idle");
  const [result, setResult] = useState<GenerateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);

  const generate = useCallback(
    async (transcript: string, mode?: GenerationMode): Promise<GenerateResponse | null> => {
      controllerRef.current?.abort();
      const controller = new AbortController();
      controllerRef.current = controller;

      setState("loading");
      setError(null);
      setResult(null);

      try {
        const response = await api.generate(transcript, mode, controller.signal);
        setResult(response);
        setState("success");
        return response;
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") {
          return null;
        }
        const message = err instanceof Error ? err.message : "An unexpected error occurred.";
        setError(message);
        setState("error");
        throw err instanceof Error ? err : new Error(message);
      } finally {
        if (controllerRef.current === controller) {
          controllerRef.current = null;
        }
      }
    },
    []
  );

  const reset = useCallback(() => {
    controllerRef.current?.abort();
    controllerRef.current = null;
    setState("idle");
    setResult(null);
    setError(null);
  }, []);

  return { state, result, error, generate, reset };
}
