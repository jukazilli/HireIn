# ADR-0008 — Contratos de API gerados a partir de OpenAPI

- **Status:** Accepted
- **Data:** 2026-09-14
- **Escopo:** contrato entre frontend e backend

## Contexto

O HireIn terá frontend em TypeScript/SvelteKit e backend em Python/FastAPI.

Manter manualmente os mesmos contratos em duas linguagens cria risco de divergência entre:

- DTOs;
- enums;
- campos obrigatórios;
- estados;
- erros;
- payloads de requests/responses.

FastAPI já produz OpenAPI a partir dos schemas Pydantic.

## Alternativas consideradas

### Tipos duplicados manualmente

Simples no começo, mas tende a gerar drift e bugs silenciosos conforme o domínio cresce.

### GraphQL

Poderia oferecer schema forte, mas adicionaria uma camada de complexidade que não resolve nenhum problema real do piloto melhor que REST tipado.

### OpenAPI como fonte de contrato

Permite gerar tipos/clientes TypeScript a partir da API real.

## Decisão

A API FastAPI será a fonte de verdade dos contratos HTTP.

O frontend deverá consumir tipos/clientes gerados a partir do documento OpenAPI, evitando duplicação manual sempre que possível.

Fluxo esperado:

```text
Pydantic schemas
      ↓
FastAPI
      ↓
OpenAPI
      ↓
geração de tipos/client
      ↓
SvelteKit
```

## Consequências positivas

- redução de drift;
- mudanças incompatíveis ficam mais visíveis;
- melhor experiência de desenvolvimento;
- documentação da API derivada da implementação;
- base para testes de contrato.

## Trade-offs

- geração precisa fazer parte do fluxo de desenvolvimento;
- ferramentas geradoras podem produzir tipos pouco ergonômicos em alguns casos;
- mudanças no schema precisam ser tratadas com disciplina.

## Regras

- não editar manualmente arquivos gerados;
- schemas de API não devem expor diretamente modelos internos de persistência;
- mudanças breaking devem ser explicitadas;
- erros devem possuir formato previsível;
- enums relevantes ao domínio devem ser estáveis e documentados.

## Gatilhos de revisão

Revisar se:

- REST deixar de atender requisitos reais do produto;
- uma nova interface pública exigir estratégia de versionamento diferente;
- contratos assíncronos/event-driven passarem a representar parte relevante do sistema.
