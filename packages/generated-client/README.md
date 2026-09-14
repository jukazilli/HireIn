# Generated API contract

This package is generated from FastAPI OpenAPI. FastAPI remains the source of truth; the TypeScript schema is a versioned build artifact consumed by the frontend.

Workflow:

```bash
uv run --package hirein-api python scripts/export_openapi.py
pnpm generate:api-types
```

`openapi.json` is temporary and remains ignored by Git.
`src/schema.d.ts` is generated, committed and must never be hand-edited.

The CI regenerates `src/schema.d.ts` from the current FastAPI application and fails when the generated result differs from the committed schema. Therefore a backend contract change must regenerate and commit the TypeScript contract in the same change.

Frontend code should import API request/response/enumeration types from this generated contract, preferably through `apps/web/src/lib/api.ts`, instead of recreating API shapes manually.
