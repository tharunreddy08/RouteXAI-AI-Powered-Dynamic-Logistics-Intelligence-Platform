# RouteXAI — Frontend (Phase 5)

React + Vite + TypeScript + Tailwind dashboard for the RouteXAI logistics
platform, connected to the FastAPI backend built in Phases 1-4.

## Stack

React 19, Vite, TypeScript, Tailwind CSS v3, React Router, Axios, Framer
Motion, React Leaflet (with Leaflet), Lucide icons.

## What's included

- **Auth**: login/register pages, JWT stored in `localStorage`, auto-attached
  to every API call, role-aware route guards (`RequireAuth`)
- **Dashboard**: fleet-wide KPIs, fleet snapshot, recent hardware events, ML
  model status, recent orders — all pulled live from the backend, no mock data
- **Orders**: full order list with status filters, CSV/JSON upload, one-click
  "Optimize All"
- **Manual Order Entry**: the exact form from spec section 7 — Add Order,
  Save & Optimize, Clear Form
- **Fleet & Map**: Leaflet dark-tile map with vehicle markers (route-colored),
  order markers (priority-colored diamonds), and route polylines; traffic
  mode selector; re-optimize button
- **Hardware Demo**: per-vehicle Trigger BLOCK_DETECTED / Clear Block
  buttons, a live "Hardware Signal Active" banner, and an event timeline —
  wired directly to the Phase 4 hardware endpoints
- **Rider Performance**: ranked leaderboard by efficiency score
- **Route History**: predicted vs. actual ETA table (the data that feeds the
  Phase 3 self-learning feedback loop)
- **Analysis** (new, Phase 6): Daily/Weekly/Monthly/Yearly view modes with a
  date/week/month/year selector, an animated line chart (deliveries + avg
  ETA with tooltips for fuel efficiency and delay %), four summary cards,
  a real (not simulated) ML Insights panel pulled from `/ml/status`, a
  predicted-vs-actual ETA feed pulled from `/route-history`, and a
  **Download Report** button that generates a real downloadable PDF
  client-side via jsPDF

Design: a dark "AI logistics command center" theme — deep navy surfaces,
a signal-cyan accent for live/active state, a 5-color route palette so each
vehicle's route is visually distinct on the map, Space Grotesk for display
type paired with Inter for body text and JetBrains Mono for data/metrics.

**Honesty note on Analysis chart data**: per spec section 22, this is
explicitly one place where the spec permits simulated frontend-only data
("No backend calculations are required for these analysis visualizations").
The chart/summary numbers are a deterministic seeded generator (same filter
always reproduces the same numbers) — clearly labeled as simulated in the
page itself — while the ML Insights panel and Predicted vs Actual ETA feed
on the same page are real, live backend data.

## What's NOT in yet

- Order status 15-minute auto-sync indicator in the UI
- Settings page

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

## Next phase

Remaining polish items only — the core spec is functionally complete:
order status 15-minute auto-sync, a Settings page, Docker Compose
end-to-end verification, and expanded test coverage for the Analysis page.
