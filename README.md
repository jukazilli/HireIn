# HireIn

**HireIn** é um agente pessoal de carreira focado no mercado brasileiro.

A proposta é ajudar o candidato a encontrar vagas relevantes, entender sua compatibilidade, preparar candidaturas melhores e reduzir o trabalho repetitivo de processos seletivos.

> **Fase atual:** HireIn Match v0 implementado e em validação; o próximo gate é formar o dataset real do piloto com 30–50 vagas avaliadas.

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
11. [Candidate Core](docs/11-CANDIDATE-CORE.md)
12. [Job Core](docs/12-JOB-CORE.md)
13. [HireIn Match v0](docs/13-MATCH-V0.md)
14. [Architecture Decision Records](docs/adr/README.md)

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

A Etapa A possui uma baseline executável com:

- monorepo TypeScript + Python;
- SvelteKit/Svelte no frontend;
- FastAPI no core;
- PostgreSQL + pgvector para desenvolvimento e CI;
- SQLAlchemy + Alembic;
- health checks de liveness e readiness;
- OpenAPI como fonte do contrato para TypeScript;
- `uv.lock` e `pnpm-lock.yaml` versionados;
- CI com instalações bloqueadas e checks de frontend, backend, migrations e contrato.

## Candidate Core

A Etapa B criou a fonte de verdade profissional do piloto:

```text
CandidateProfile
│
├── identidade profissional
├── preferências de carreira
├── experiências
│   └── fatos/evidências
├── formação
├── skills
├── certificações
└── idiomas
```

Fatos carregam proveniência (`USER_CONFIRMED`, `RESUME_EXTRACTED`, `AI_DRAFT` etc.) para impedir que inferências futuras sejam tratadas como verdades sem confirmação humana.

No piloto existe um único perfil primário e a edição ocorre por `GET/PUT /api/v1/profile`.

## Job Core

A Etapa C cria a fonte de verdade das oportunidades:

```text
vaga bruta
   ↓
JobPosting
   ↓
JobRequirements
```

A descrição original é preservada e requisitos são estruturados por tipo e importância. A deduplicação usa fingerprint determinístico priorizando `plataforma + external_id`, depois URL e, por último, empresa + cargo + localização.

No piloto a ingestão continua manual:

```text
GET  /api/v1/jobs
POST /api/v1/jobs
GET  /api/v1/jobs/{id}
PUT  /api/v1/jobs/{id}
```

A interface de validação fica em `/jobs`. Parsing por IA, scraping e Auto Apply continuam desligados.

## HireIn Match v0

O Match conecta Candidate Core e Job Core sem embeddings ou LLM:

```text
Candidate Core
      +
Job Core
      ↓
evidências confirmadas
      ↓
MATCHED / GAP / UNKNOWN
      +
preferências separadas
      ↓
score + cobertura + explicação
```

Somente dados `USER_CONFIRMED` podem aumentar o score. `AI_DRAFT`, dados extraídos ainda não confirmados e inferências de sistema ficam excluídos da pontuação.

A avaliação é calculada sob demanda por:

```text
GET /api/v1/jobs/{id}/match
```

A interface de validação fica em `/jobs/match` e mostra score, band, cobertura, evidências, gaps, itens não avaliáveis e conflitos de preferência.

Se menos de 60% do peso dos requisitos puder ser avaliado, o sistema retorna `INSUFFICIENT_DATA` em vez de inventar precisão. Preferências comuns não viram blockers automáticos.

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

O próximo gate não é adicionar IA. É formar um dataset real de aproximadamente **30–50 vagas brasileiras** e registrar manualmente:

- se a vaga realmente interessa;
- quais requisitos foram identificados corretamente;
- quais matches e gaps fazem sentido;
- falsos negativos por sinônimo ou contexto;
- erros de ordenação do score.

Esses dados decidirão se o ganho seguinte vem de regras melhores, aliases/taxonomia, embeddings, reranking ou LLM. A tecnologia só entra depois que o problema estiver medido.

A ordem detalhada e os critérios de aceite permanecem em `docs/09-IMPLEMENTATION-PLAN.md`.

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
