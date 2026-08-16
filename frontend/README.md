# RouteXAI — Frontend 
## Local setup

```bash
cd frontend
npm install
cp .env.example .env      # points at http://localhost:8000 by default
npm run dev
```

Make sure the backend is running first (see `backend/README.md`) and has
been seeded (`python -m seed.seed_data`), then open http://localhost:5173
and log in with one of the seeded demo accounts.

**Note on CORS**: the backend's default `CORS_ORIGINS` includes
`http://localhost:5173` (Vite's default dev port) and `http://localhost:3000`.
If you run the frontend on a different port, add it to the backend's
`CORS_ORIGINS` env var.

## Build

```bash
npm run build       # type-checks with tsc -b, then builds to dist/
npm run preview      # serve the production build locally
```

Verified: `npm run build` and `tsc -b --noEmit` both pass cleanly, and the
dev server was smoke-tested end-to-end against a live, seeded backend
(login, CORS, and every page module compiling without errors).

## Project structure

```text
frontend/
├── src/
│   ├── main.tsx / App.tsx        # entry point, router
│   ├── lib/
│   │   ├── api.ts                 # axios client + typed endpoint functions
│   │   ├── auth.tsx               # AuthContext, RequireAuth route guard
│   │   ├── toast.tsx              # toast notification system
│   │   └── types.ts               # TS types mirroring backend schemas
│   ├── components/
│   │   ├── Layout.tsx             # sidebar + topbar + footer
│   │   └── Badges.tsx             # status/priority/traffic badges
│   └── pages/
│       ├── LoginPage.tsx / RegisterPage.tsx
│       ├── DashboardPage.tsx
│       ├── OrdersPage.tsx / ManualOrderEntryPage.tsx
│       ├── FleetMapPage.tsx
│       ├── HardwareDemoPage.tsx
│       ├── RiderPerformancePage.tsx
│       ├── RouteHistoryPage.tsx
│       └── AnalyticsPage.tsx
├── tailwind.config.js              # RouteXAI design tokens
├── .env.example
└── package.json
```
