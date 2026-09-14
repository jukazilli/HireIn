# HireIn

**HireIn** é um agente pessoal de carreira focado no mercado brasileiro.

A proposta é ajudar o candidato a encontrar vagas relevantes, entender sua compatibilidade, preparar candidaturas melhores e reduzir o trabalho repetitivo de processos seletivos.

> **Fase atual:** fundação técnica implementada; próxima etapa é o Candidate Core da primeira vertical slice do piloto individual.

O projeto começa pequeno: um único usuário, custo recorrente próximo de zero e revisão humana das candidaturas. A expansão para terceiros somente deverá acontecer após validação real do produto e tratamento formal de privacidade, segurança e LGPD.

## Princípios

- qualidade de match antes de volume;
- automação progressiva;
- usuário no controle;
- IA não pode inventar fatos profissionais;
- começar com custo zero ou mínimo;
- tecnologia escolhida por adequação técnica, não por popularidade ou facilidade de codificação;
- evitar dependência de estratégias de evasão de mecanismos anti-bot;
- infraestrutura local-first durante o piloto;
- preparar escala somente depois de provar valor.

## Documentação

1. [Briefing de Produto](docs/01-BRIEFING.md)
2. [Product Flows](docs/02-PRODUCT-FLOWS.md)
3. [Arquitetura](docs/03-ARCHITECTURE.md)
4. [Engenharia](docs/04-ENGINEERING.md)
5. [Infraestrutura](docs/05-INFRASTRUCTURE.md)
6. [Custos](docs/06-COSTS.md)
7. [Privacy, Security & LGPD](docs/07-PRIVACY-SECURITY-LGPD.md)
8. [Roadmap orientado a validação](docs/08-ROADMAP.md)
9. [Plano da primeira implementação](docs/09-IMPLEMENTATION-PLAN.md)
10. [Bootstrap técnico](docs/10-BOOTSTRAP.md)
11. [Architecture Decision Records](docs/adr/README.md)

O arquivo [`AGENTS.md`](AGENTS.md) concentra guardrails operacionais para agentes de código e deve ser mantido coerente com os documentos acima.

## Decisões técnicas atuais

| Camada | Direção atual |
|---|---|
| Web | SvelteKit + TypeScript |
| Extensão futura | WXT + Svelte + Manifest V3 |
| Core API | Python + FastAPI |
| Banco | PostgreSQL + pgvector |
| Banco hospedado no piloto | Neon Free |
| ORM / migrations | SQLAlchemy 2 + Alembic |
| Browser automation | Playwright Python |
| Queue do piloto | PostgreSQL |
| Embeddings | modelo multilíngue a escolher por benchmark PT-BR |
| LLM | provider-agnostic, escolha por tarefa/eval |
| Execução do piloto | local-first |

As decisões estruturais possuem ADRs com contexto, alternativas, trade-offs e gatilhos de revisão. LLM e embeddings permanecem propositalmente sem escolha definitiva até existirem evals com dados PT-BR representativos.

## Fundação técnica

A Etapa A do plano de implementação já possui uma baseline executável com:

- monorepo TypeScript + Python;
- SvelteKit/Svelte no frontend;
- FastAPI no core;
- PostgreSQL + pgvector para desenvolvimento e CI;
- SQLAlchemy + Alembic;
- health checks de liveness e readiness;
- OpenAPI como fonte do contrato para TypeScript;
- `uv.lock` e `pnpm-lock.yaml` versionados;
- CI com instalações bloqueadas e checks de frontend, backend, migrations e contrato.

Nenhum LLM, embedding, ATS adapter, extensão ou Auto Apply foi introduzido no bootstrap.

## Orçamento do piloto

Meta inicial:

```text
Infraestrutura fixa: US$ 0/mês
IA:                   US$ 0/mês como alvo
Teto experimental IA: até US$ 5/mês somente se necessário
```

O objetivo é pagar somente depois que um gargalo ou ganho de qualidade estiver comprovado.

## Gate de expansão

O HireIn não será aberto a terceiros apenas porque o piloto funciona tecnicamente.

A sequência definida é:

```text
piloto individual
      ↓
validar valor e confiabilidade
      ↓
formalizar privacy/security/LGPD
      ↓
private beta pequeno
      ↓
validar segurança operacional
      ↓
escalar
```

O checklist completo está em `docs/07-PRIVACY-SECURITY-LGPD.md`.

## Próximo marco

A próxima implementação é o **Candidate Core**, primeiro domínio funcional da vertical slice:

```text
perfil estruturado
     ↓
fatos com proveniência
     ↓
preferências profissionais
     ↓
API + persistência
     ↓
interface de edição
```

Depois entram Job Core, Match determinístico e Application Draft, nessa ordem.

A ordem detalhada, critérios de aceite e limites dessa implementação estão em `docs/09-IMPLEMENTATION-PLAN.md`.

Não haverá Auto Apply irrestrito no primeiro marco.

## Governança técnica

Antes de alterar uma decisão estrutural, consulte `docs/adr/README.md`.

Novas decisões relevantes devem ser registradas como ADRs. Em especial, ainda deverão receber ADRs futuros quando houver evidência suficiente:

- modelo de embeddings;
- LLM default por tarefa;
- autenticação futura;
- execução remota do browser;
- eventual migração de queue;
- storage remoto de documentos.
