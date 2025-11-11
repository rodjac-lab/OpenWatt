# OpenWatt UI (Next.js skeleton)

## Quick start
1. Install Node.js (>= 18.18) and pnpm or npm.
2. From the repo root:
       cd ui
       npm install
       npm run dev
3. The development server exposes http://localhost:3000 with a placeholder view that fetches `/health`.
4. Copy `.env.example` (root) into `ui/.env.local` when you need to point to a remote API.

## Notes
- The UI imports freshness badges and Tariff typings from `docs/ui` until the generated OpenAPI client lands.
- Keep UI changes spec-driven: update `specs/ui.md` (or `specs/system.md`) before coding new flows.
