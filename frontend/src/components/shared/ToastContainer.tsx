import { CheckCircle2, XCircle, AlertTriangle, Info, X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Toast, ToastVariant } from "@/hooks/useToast";

const icons: Record<ToastVariant, React.ReactNode> = {
  default: <Info className="h-4 w-4 text-sky-600" aria-hidden="true" />,
  success: <CheckCircle2 className="h-4 w-4 text-emerald-600" aria-hidden="true" />,
  warning: <AlertTriangle className="h-4 w-4 text-amber-600" aria-hidden="true" />,
  destructive: <XCircle className="h-4 w-4 text-red-600" aria-hidden="true" />,
};

const styles: Record<ToastVariant, string> = {
  default: "border-sky-200 bg-white",
  success: "border-emerald-200 bg-white",
  warning: "border-amber-200 bg-white",
  destructive: "border-red-200 bg-white",
};

interface ToastContainerProps {
  toasts: Toast[];
  dismiss: (id: string) => void;
}

export function ToastContainer({ toasts, dismiss }: ToastContainerProps) {
  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 w-[360px] max-w-[calc(100vw-2rem)]"
      role="region"
      aria-label="Notifications"
      aria-live="polite"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="status"
          className={cn(
            "animate-slide-up flex items-start gap-3 rounded-xl border p-4 shadow-lg",
            styles[toast.variant]
          )}
        >
          <div className="mt-0.5 shrink-0">{icons[toast.variant]}</div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-foreground">{toast.title}</p>
            {toast.description && (
              <p className="mt-0.5 text-xs text-muted-foreground">{toast.description}</p>
            )}
          </div>
          <button
            type="button"
            onClick={() => dismiss(toast.id)}
            className="shrink-0 text-muted-foreground hover:text-foreground transition-colors rounded p-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            aria-label="Dismiss notification"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}
