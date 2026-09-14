# HireIn — Bootstrap técnico

> **Fase:** Etapa A da primeira vertical slice  
> **Objetivo:** tornar a arquitetura executável sem antecipar funcionalidades de produto.

## Entregas desta etapa

- monorepo com workspaces TypeScript e Python;
- SvelteKit 2 + Svelte 5;
- FastAPI;
- PostgreSQL local com pgvector;
- SQLAlchemy + Alembic;
- liveness e readiness separados;
- geração de contrato TypeScript a partir do OpenAPI;
- CI para backend, migrations, frontend e contrato;
- `.gitignore` para dados pessoais, secrets e sessões;
- Auto Apply continua inexistente.

## Versões e política

A baseline usa linhas estáveis, não previews:

- Node 22 LTS-compatible;
- pnpm 12;
- Svelte 5;
- SvelteKit 2;
- Python 3.13;
- FastAPI 0.141;
- SQLAlchemy 2.0;
- Alembic 1.20.

Dependências estruturais são fixadas em versões estáveis no bootstrap. Atualizações futuras devem ser avaliadas com testes; major upgrades não são automáticos.

## Execução local

### Banco

```bash
docker compose up -d postgres
```

### Backend

```bash
uv sync --all-packages --dev
cd services/api
uv run alembic upgrade head
uv run uvicorn hirein_api.main:app --reload
```

API:

- `GET /health/live` — processo está vivo;
- `GET /health/ready` — processo consegue acessar o banco;
- `/docs` — OpenAPI UI local.

### Frontend

```bash
pnpm install
pnpm dev:web
```

### Contrato OpenAPI

Na raiz:

```bash
uv run --package hirein-api python scripts/export_openapi.py
pnpm generate:api-types
```

Arquivos gerados ficam fora do Git para evitar edição manual e drift acidental.

## O que não entrou

- autenticação pública;
- multiusuário;
- LLM;
- embeddings;
- currículo real;
- Candidate Core;
- Job Core;
- ATS adapters;
- Playwright;
- extensão de navegador;
- Auto Apply.

Esses itens entram somente nas fases definidas em `docs/09-IMPLEMENTATION-PLAN.md`.
