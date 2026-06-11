# HummingID Gateway

TypeScript API gateway — the public entrypoint of HummingID. Handles HTTP, WebSocket, jobs, and orchestrates calls to the Python ML service.

## Quickstart

```bash
cd gateway
npm install
cp .env.example .env
npm run dev
```

Open http://127.0.0.1:8080/api/v1/health.

## Scripts

- `npm run dev` — hot-reload dev server (tsx watch)
- `npm test` — run Vitest
- `npm run typecheck` — tsc --noEmit
- `npm run build` — emit JS to `dist/`
- `npm start` — run built JS

## Layout

```
gateway/
  src/
    routes/        # HTTP routes
    services/      # Outbound clients (ML service, etc.)
    config.ts      # Zod-validated env config
    app.ts         # Hono app factory
    server.ts      # Node entrypoint
  tests/
```
