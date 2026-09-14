# ADR-0007 — Fila baseada em PostgreSQL no piloto

- **Status:** Accepted
- **Data:** 2026-09-14
- **Escopo:** processamento assíncrono inicial

## Contexto

O HireIn precisará executar tarefas que não devem bloquear uma requisição HTTP, por exemplo:

- importar e normalizar vagas;
- gerar embeddings;
- recalcular matches;
- preparar currículo;
- executar adapters;
- processar retries;
- classificar eventos.

No piloto haverá um único usuário e volume reduzido.

## Alternativas consideradas

### Redis + BullMQ / Celery

São soluções maduras, mas introduzem outro serviço e outra dependência operacional antes de existir volume que justifique isso.

### RabbitMQ

Excelente broker para topologias de mensageria mais complexas, porém excessivo para a necessidade atual.

### PostgreSQL

Uma tabela durável pode representar jobs com estados explícitos e locking transacional.

Modelo conceitual:

```text
jobs
- id
- type
- payload
- status
- available_at
- attempts
- max_attempts
- locked_at
- locked_by
- last_error
- created_at
- completed_at
```

## Decisão

No piloto, utilizar **PostgreSQL como fila durável**.

Workers devem obter jobs com locking seguro e evitar processamento duplicado.

Estados mínimos:

```text
PENDING
RUNNING
COMPLETED
FAILED
DEAD_LETTER
```

Retries devem utilizar backoff e limite explícito.

## Consequências positivas

- zero serviço adicional;
- persistência e auditoria simples;
- facilidade de inspecionar falhas;
- transações podem coordenar criação de estado + job;
- custo praticamente zero no piloto.

## Trade-offs

- não é ideal para throughput muito elevado;
- polling pode ser menos eficiente;
- exige cuidado com locks e concorrência;
- não possui todos os recursos de brokers especializados.

## Gatilhos de revisão

Migrar para broker dedicado quando medições mostrarem pelo menos um destes problemas:

- backlog crescente;
- latência incompatível;
- concorrência elevada;
- necessidade de prioridades/topologias mais sofisticadas;
- carga da fila prejudicando o banco transacional;
- necessidade de workers distribuídos em grande escala.

## Regra

Não adicionar Redis ou RabbitMQ apenas para reproduzir uma arquitetura de SaaS em escala que o HireIn ainda não possui.
