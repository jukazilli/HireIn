# Generated API contract

This package is generated from FastAPI OpenAPI and must not become a second source of truth.

Workflow:

```bash
uv run --package hirein-api python scripts/export_openapi.py
pnpm generate:api-types
```

`openapi.json` and `src/schema.d.ts` are generated locally and intentionally ignored by Git.
Do not hand-edit generated schema files.
