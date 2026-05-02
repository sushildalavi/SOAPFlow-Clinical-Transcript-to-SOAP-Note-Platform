import { Activity, Github, ExternalLink, History, Settings } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

interface NavbarProps {
  onToggleHistory?: () => void;
  onToggleSettings?: () => void;
  historyCount?: number;
}

export function Navbar({ onToggleHistory, onToggleSettings, historyCount }: NavbarProps) {
  const docsUrl = api.docsUrl();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-white/80 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary shadow-sm shadow-primary/30">
              <Activity className="h-4 w-4 text-primary-foreground" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[15px] font-semibold tracking-tight text-foreground">
                SOAPFlow
              </span>
              <Badge variant="teal" className="text-[10px] px-1.5 py-0">
                v1.0
              </Badge>
            </div>
          </div>

          {/* Nav center */}
          <nav className="hidden md:flex items-center gap-6">
            <span className="text-sm text-muted-foreground">
              AI Clinical Documentation Assistant
            </span>
          </nav>

          {/* Actions */}
          <div className="flex items-center gap-1">
            <a
              href={docsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="hidden sm:flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              aria-label="Open API documentation in a new tab"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              <span className="hidden lg:inline">API Docs</span>
            </a>

            <a
              href="https://github.com/sushildalavi/SOAPFlow"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              aria-label="View source on GitHub"
            >
              <Github className="h-4 w-4" />
              <span className="hidden sm:inline">GitHub</span>
            </a>

            {onToggleHistory && (
              <Button
                variant="outline"
                size="sm"
                onClick={onToggleHistory}
                className="relative gap-1.5"
                aria-label={`Open note history${historyCount ? ` (${historyCount} saved)` : ""}`}
                title="Note History"
              >
                <History className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">History</span>
                {historyCount !== undefined && historyCount > 0 && (
                  <span
                    className="absolute -top-1.5 -right-1.5 flex h-4 min-w-[1rem] items-center justify-center rounded-full bg-primary px-1 text-[9px] font-bold text-primary-foreground shadow-sm"
                    aria-hidden="true"
                  >
                    {historyCount > 9 ? "9+" : historyCount}
                  </span>
                )}
              </Button>
            )}

            {onToggleSettings && (
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={onToggleSettings}
                aria-label="Open system status"
                title="System Status"
              >
                <Settings className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
