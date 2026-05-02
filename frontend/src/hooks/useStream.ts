/**
 * useStream — SSE hook for real-time SOAP generation streaming.
 * Connects to GET /api/v1/stream and builds up the full response token-by-token.
 */
import { useState, useCallback, useRef } from "react";

export type StreamState = "idle" | "streaming" | "done" | "error";

interface StreamResult {
  rawJson: string;        // accumulates streamed tokens
  elapsedMs: number | null;
}

interface UseStreamReturn {
  state: StreamState;
  result: StreamResult | null;
  error: string | null;
  startStream: (transcript: string, mode?: string) => void;
  stopStream: () => void;
  reset: () => void;
}

export function useStream(): UseStreamReturn {
  const [state, setState] = useState<StreamState>("idle");
  const [result, setResult] = useState<StreamResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);
  const bufferRef = useRef<string>("");

  const stopStream = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    stopStream();
    setState("idle");
    setResult(null);
    setError(null);
    bufferRef.current = "";
  }, [stopStream]);

  const startStream = useCallback(
    (transcript: string, mode?: string) => {
      reset();
      bufferRef.current = "";

      const params = new URLSearchParams({ transcript });
      if (mode) params.set("mode", mode);

      const es = new EventSource(`/api/v1/stream?${params.toString()}`);
      esRef.current = es;
      setState("streaming");

      es.onmessage = (event: MessageEvent) => {
        try {
          const parsed = JSON.parse(event.data) as {
            type: "token" | "done" | "error";
            content?: string;
            elapsed_ms?: number;
            message?: string;
          };

          if (parsed.type === "token" && parsed.content) {
            bufferRef.current += parsed.content;
            setResult({ rawJson: bufferRef.current, elapsedMs: null });
          } else if (parsed.type === "done") {
            setResult({ rawJson: bufferRef.current, elapsedMs: parsed.elapsed_ms ?? null });
            setState("done");
            es.close();
          } else if (parsed.type === "error") {
            setError(parsed.message ?? "Streaming error.");
            setState("error");
            es.close();
          }
        } catch {
          // Non-JSON message — ignore
        }
      };

      es.onerror = () => {
        setError("Connection lost. Please try again.");
        setState("error");
        es.close();
      };
    },
    [reset]
  );

  return { state, result, error, startStream, stopStream, reset };
}
