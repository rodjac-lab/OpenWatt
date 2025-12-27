# UI integration pack

1. Export the latest OpenAPI schema without running the server:
   python scripts/export_openapi.py --out specs/openapi.generated.json
2. Feed the JSON into your preferred generator (e.g. `npx openapi-typescript specs/openapi.generated.json --output ui/types/api.ts`).
3. Reuse the shared freshness/badge mapping described in `docs/ui/badges.md`.
4. Bind the generated client to the FastAPI endpoints listed in the README (start with `/v1/tariffs` and `/v1/tariffs/history`).

Next steps for the UI squad:

- Use the pre-scaffolded Next.js app under `ui/` (run `npm install && npm run dev`).
- Consume the `Tariff` type defined in `docs/ui/types.ts` until the generated types are wired in CI.
- Surface freshness badges exactly as specified (no other wording) to stay aligned with the Spec-Kit.
