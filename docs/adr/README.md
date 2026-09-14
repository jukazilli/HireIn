# Architecture Decision Records (ADRs)

Este diretório registra decisões arquiteturais relevantes do HireIn.

O objetivo é preservar o raciocínio por trás das escolhas técnicas, evitando que futuras implementações — humanas ou assistidas por IA — substituam decisões importantes apenas por preferência, popularidade ou conveniência local.

## Como ler um ADR

Cada ADR deve registrar:

- contexto;
- problema;
- alternativas consideradas;
- decisão;
- consequências positivas;
- trade-offs;
- gatilhos de revisão.

## Status possíveis

- **Accepted** — decisão vigente;
- **Proposed** — decisão em avaliação;
- **Superseded** — substituída por ADR posterior;
- **Rejected** — alternativa avaliada e recusada;
- **Deferred** — decisão propositalmente adiada.

## ADRs atuais

1. [ADR-0001 — Frontend com SvelteKit + TypeScript](0001-frontend-sveltekit.md)
2. [ADR-0002 — Core backend com Python + FastAPI](0002-backend-python-fastapi.md)
3. [ADR-0003 — PostgreSQL + pgvector como camada de dados](0003-postgresql-pgvector.md)
4. [ADR-0004 — Playwright para automação de navegador](0004-playwright-browser-automation.md)
5. [ADR-0005 — Execução local-first no piloto](0005-local-first-pilot.md)
6. [ADR-0006 — Adiar escolha definitiva de LLM e embeddings](0006-ai-model-selection-deferred.md)
7. [ADR-0007 — Fila baseada em PostgreSQL no piloto](0007-postgres-job-queue.md)
8. [ADR-0008 — Contratos de API gerados a partir de OpenAPI](0008-openapi-contracts.md)

## Regra de governança

Uma decisão aceita só deve ser substituída quando houver evidência concreta de que outra alternativa melhora significativamente pelo menos uma destas dimensões:

- confiabilidade;
- segurança;
- privacidade;
- qualidade de produto;
- custo total de operação;
- capacidade de manutenção;
- desempenho mensurado;
- compatibilidade com os objetivos do HireIn.

"É mais fácil de programar" ou "é mais popular" não são justificativas suficientes isoladamente.
