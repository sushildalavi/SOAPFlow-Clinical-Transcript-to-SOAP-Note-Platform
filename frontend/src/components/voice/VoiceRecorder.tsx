import { useState, useRef, useCallback } from "react";
import { Mic, MicOff, Loader2, AudioWaveform } from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

interface VoiceRecorderProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

type RecorderState = "idle" | "recording" | "uploading" | "error";

const MAX_RECORDING_MS = 5 * 60 * 1000; // 5 minutes

export function VoiceRecorder({ onTranscript, disabled }: VoiceRecorderProps) {
  const [state, setState] = useState<RecorderState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);

  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const startTimeRef = useRef<number>(0);

  const stopTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = null;
  };

  const stopRecording = useCallback(() => {
    if (mediaRef.current && mediaRef.current.state !== "inactive") {
      mediaRef.current.stop();
      setState("uploading");
    }
  }, []);

  const uploadAudio = useCallback(async (blob: Blob, mimeType: string) => {
    setState("uploading");
    try {
      const formData = new FormData();
      const ext = mimeType.includes("webm") ? "webm" : "mp3";
      formData.append("file", blob, `recording.${ext}`);

      const response = await fetch(api.url("/transcribe"), {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Transcription failed.");
      }

      const data = await response.json();
      onTranscript(data.transcript);
      setState("idle");
      setElapsedMs(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
      setState("error");
    }
  }, [onTranscript]);

  const startRecording = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";

      const recorder = new MediaRecorder(stream, { mimeType });
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stopTimer();
        stream.getTracks().forEach((t) => t.stop());
        const blob = new Blob(chunksRef.current, { type: mimeType });
        await uploadAudio(blob, mimeType);
      };

      recorder.start(500); // collect chunks every 500ms
      mediaRef.current = recorder;
      startTimeRef.current = Date.now();
      setState("recording");

      // Elapsed timer
      timerRef.current = setInterval(() => {
        const elapsed = Date.now() - startTimeRef.current;
        setElapsedMs(elapsed);
        if (elapsed >= MAX_RECORDING_MS) stopRecording();
      }, 200);
    } catch {
      setError("Microphone access denied. Check browser permissions.");
      setState("error");
    }
  }, [stopRecording, uploadAudio]);

  const formatTime = (ms: number) => {
    const s = Math.floor(ms / 1000);
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  };

  const isRecording = state === "recording";
  const isUploading = state === "uploading";

  return (
    <div className="flex flex-col items-start gap-2">
      <div className="flex items-center gap-2">
        <Button
          type="button"
          variant={isRecording ? "destructive" : "outline"}
          size="sm"
          className="h-8 gap-1.5 text-xs"
          disabled={disabled || isUploading}
          onClick={isRecording ? stopRecording : startRecording}
        >
          {isUploading ? (
            <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Transcribing…</>
          ) : isRecording ? (
            <><MicOff className="h-3.5 w-3.5" /> Stop ({formatTime(elapsedMs)})</>
          ) : (
            <><Mic className="h-3.5 w-3.5" /> Record Audio</>
          )}
        </Button>

        {isRecording && (
          <span className="flex items-center gap-1 text-xs text-red-500 animate-pulse">
            <AudioWaveform className="h-3.5 w-3.5" />
            Recording
          </span>
        )}
      </div>

      {error && (
        <p className="text-xs text-destructive">{error}</p>
      )}

      {!isRecording && !isUploading && !error && (
        <p className="text-xs text-muted-foreground">
          Record a doctor-patient conversation — Whisper will transcribe it automatically.
        </p>
      )}
    </div>
  );
}
