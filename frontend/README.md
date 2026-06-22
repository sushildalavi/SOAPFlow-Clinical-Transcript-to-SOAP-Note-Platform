# SOAPFlow Frontend

React 19 + Vite + TypeScript frontend for the SOAPFlow backend.

## Run

```bash
npm install
npm run dev
```

The dev server proxies `/api/*` to the backend by default.

## Build and test

```bash
npm run build
npm run lint
npm test
```

## Project layout

- App shell and entrypoint
- API wrapper and helpers
- Hooks for generation, streaming, history, and toasts
- SOAP cards, voice input, history, settings, evaluation, layout, and shared UI components

## Notes

- Streaming is token-based over SSE.
- UI primitives live in the local component library pattern.
- The production build is served behind nginx.
