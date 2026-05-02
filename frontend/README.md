# SOAPFlow — Frontend

React 19 + Vite + TypeScript. Tailwind for styling, shadcn-style
primitives in `src/components/ui/`.

## Run it

```bash
npm install
npm run dev      # http://localhost:5173
```

The dev server proxies `/api/*` to `http://localhost:8000` (the
backend). Override with `VITE_API_URL` in `.env.local` if you want
to point at a remote backend.

## Build / lint / test

```bash
npm run build    # type-check + production build into dist/
npm run lint
npm test         # vitest
```

## Project layout

```
src/
  App.tsx              # top-level layout
  main.tsx             # entrypoint
  lib/
    api.ts             # fetch wrapper around the backend
    utils.ts           # cn(), formatters
  hooks/               # useStream, useGenerate, useHistory, useToast
  components/
    ui/                # button, card, tabs, badge, ...
    soap/              # the four SOAP cards + transcript input
    voice/             # mic capture + waveform
    history/           # past notes browser
    settings/          # model + de-id config panel
    evaluation/        # eval run UI
    layout/            # navbar
    shared/            # toasts
```

## Streaming

`useStream` wraps an `EventSource` over `/api/stream`. The backend
emits one SSE event per token (`event: token`, `data: <json>`) and a
final `event: done`. Section cards fill in as their JSON keys arrive.

If you swap to a backend that streams in larger chunks, the hook will
still work — it accumulates by section name, not by token boundary.

## Adding a UI primitive

We use the shadcn pattern: copy the component into
`src/components/ui/` and own the code. Don't reach for a heavyweight
component library unless there's a real reason.

## Notes

- Tailwind config is in `tailwind.config.js`; theme tokens live there.
- `dist/` is gitignored — production output lives behind nginx in the
  Docker image.
