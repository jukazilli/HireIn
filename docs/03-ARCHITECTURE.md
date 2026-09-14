# HireIn — Arquitetura

> **Status:** arquitetura proposta para o piloto  
> **Prioridade:** validar produto com custo e complexidade mínimos sem criar dívida estrutural desnecessária  
> **Documento anterior:** [02 — Product Flows](02-PRODUCT-FLOWS.md)

---

## 1. Princípio de decisão tecnológica

O HireIn não deve escolher tecnologia porque ela é popular, familiar ou rápida de digitar.

Cada decisão deve responder:

1. qual problema concreto estamos resolvendo;
2. quais alternativas razoáveis existem;
3. quais requisitos do HireIn pesam mais nessa decisão;
4. qual é o custo operacional;
5. qual é o custo de mudança;
6. quais riscos a tecnologia introduz;
7. qual evidência faria a decisão ser revista.

A arquitetura será **evolutiva**. Começaremos simples, mas com limites claros entre domínio, IA, integrações e automação.

---

## 2. Requisitos arquiteturais que realmente importam

O HireIn precisa lidar bem com:

- dados estruturados do candidato;
- documentos e currículos;
- busca e normalização de vagas;
- matching semântico;
- LLMs potencialmente intercambiáveis;
- automação de navegador;
- adapters diferentes por ATS;
- tarefas de longa duração;
- retries e idempotência;
- auditoria;
- execução local no piloto;
- possível execução distribuída futuramente;
- privacidade e rastreabilidade;
- baixo custo inicial.

O maior desafio técnico do produto está no **domínio + matching + integrações + automação**, não na renderização da interface.

---

## 3. Estilo arquitetural

### Decisão: monólito modular + worker de automação

Não começaremos com microserviços.

A primeira arquitetura será:

```text
┌──────────────────────────────┐
│          Web App             │
│     SvelteKit / TypeScript   │
└──────────────┬───────────────┘
               │ HTTPS/JSON
               ▼
┌──────────────────────────────┐
│       HireIn Core API        │
│      Python / FastAPI        │
│                              │
│ Profile                      │
│ Jobs                         │
│ Matching                     │
│ Applications                 │
│ AI orchestration             │
│ ATS registry                 │
└──────────────┬───────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐   ┌────────────────┐
│ PostgreSQL   │   │ Agent Worker   │
│ + pgvector   │   │ Playwright     │
└──────────────┘   └───────┬────────┘
                            │
                            ▼
                     ATS / job sites
```

O agente de navegador é um processo separado porque possui ciclo de vida, dependências e falhas diferentes da API.

### Por que não microserviços

No piloto:

- existe um único usuário;
- o volume é pequeno;
- os limites de domínio ainda estão sendo validados;
- observabilidade distribuída seria custo sem benefício;
- deploy e debugging ficariam desnecessariamente complexos.

A separação lógica será feita por módulos. Extração para serviços independentes só ocorrerá quando existir um gargalo mensurável.

---

# 4. Frontend

## Decisão: SvelteKit + TypeScript

### Por que SvelteKit

O HireIn precisa de uma interface rica em:

- formulários;
- listas e filtros;
- detalhes de vagas;
- comparação de informações;
- estados de candidatura;
- feedback rápido;
- experiência responsiva.

A decisão por SvelteKit não é motivada por “ser mais fácil”. Os fatores são:

1. **baixo peso conceitual para uma aplicação cujo backend real estará em Python**;
2. Svelte compila componentes e reduz parte do runtime necessário no navegador;
3. SvelteKit oferece roteamento, SSR/prerender e estrutura de aplicação sem exigir que o backend de domínio seja escrito em JavaScript;
4. existe adapter oficial para Cloudflare;
5. WXT possui módulo oficial para Svelte, permitindo reutilizar conhecimento e design system na futura extensão;
6. TypeScript permanece disponível onde realmente agrega valor: UI, contratos e extensão.

### Alternativas analisadas

#### Next.js / React

**Pontos fortes**

- enorme ecossistema;
- mercado de desenvolvedores amplo;
- bibliotecas abundantes;
- excelente solução quando o backend também fica dentro do ecossistema Next.

**Por que não é a primeira escolha**

O núcleo do HireIn será Python por razões de IA e automação. Assim, boa parte das vantagens full-stack do Next seria duplicada pela API Python. Também adicionaríamos conceitos específicos de React/Next sem necessidade arquitetural clara.

React não está proibido. A decisão deve ser revista se:

- dependências críticas existirem somente no ecossistema React;
- expansão da equipe tornar disponibilidade de profissionais um fator dominante;
- SvelteKit apresentar limitação concreta em produção.

#### Nuxt 4 / Vue

É uma alternativa tecnicamente forte e portátil, com SSR e Nitro. Ficou em segundo lugar. Não foi escolhido porque, para o escopo do HireIn, SvelteKit entrega uma camada de UI menor e suficiente sem trazer um segundo backend de aplicação.

#### React + Vite SPA

Funcionaria bem para o painel autenticado. Porém exigiria montar manualmente mais convenções de roteamento/data loading e não oferece vantagem material sobre SvelteKit para este produto.

### Decisão de UI

Não adotaremos uma biblioteca visual que determine a identidade do produto.

O frontend deve usar:

- design tokens;
- CSS variables;
- componentes próprios para padrões importantes;
- acessibilidade por padrão;
- dependências visuais pequenas e substituíveis.

Tailwind ou outra utility layer pode ser avaliada durante o Design System, mas não é requisito arquitetural.

---

# 5. Extensão de navegador

## Decisão: WXT + Svelte + TypeScript + Manifest V3

A extensão será utilizada quando chegarmos ao modo Copilot de candidatura.

### Responsabilidades

- detectar páginas suportadas;
- reconhecer ATS;
- comunicar-se com o HireIn;
- preencher campos quando autorizado;
- mostrar estado da candidatura;
- solicitar intervenção do usuário;
- nunca guardar desnecessariamente dados sensíveis no storage da extensão.

### Por que WXT

WXT fornece estrutura específica para extensões modernas e possui integração oficial com Svelte, Vue, React e Solid. Isso evita construir manualmente infraestrutura de content scripts, background scripts e bundling.

### Regra importante

A extensão e o worker Playwright são complementares, não concorrentes:

- **extensão:** boa para automação assistida dentro da sessão real do usuário;
- **Playwright worker:** bom para testes, adapters reproduzíveis e fluxos controlados.

No piloto, o caminho mais confiável para cada ATS deverá ser escolhido por evidência.

---

# 6. Backend e domínio

## Decisão: Python + FastAPI

### Motivação

O backend estará próximo de:

- parsing de documentos;
- embeddings;
- NLP;
- avaliação de matching;
- LLM orchestration;
- browser automation;
- datasets de avaliação;
- scripts de ingestão.

Python concentra esse ecossistema e evita criar um backend Node apenas para depois manter workers Python separados.

FastAPI foi escolhido porque:

- usa type hints e Pydantic;
- gera OpenAPI e JSON Schema;
- facilita gerar clientes TypeScript;
- suporta I/O assíncrono;
- não força ORM ou banco específico;
- possui boa adequação para APIs modernas.

### Alternativas

#### NestJS

Muito forte para APIs TypeScript. Não foi escolhido porque IA, parsing e Playwright continuariam exigindo Python ou outro runtime, aumentando o número de stacks no backend.

#### Django

Excelente framework “batteries included”, especialmente para CRUD, admin e autenticação. Ficou como alternativa caso o produto futuro dependa fortemente de backoffice administrativo. Para o piloto, FastAPI oferece uma superfície menor para o tipo de workload previsto.

---

# 7. Banco de dados

## Decisão: PostgreSQL + pgvector

O domínio do HireIn é fortemente relacional:

```text
candidate
  ├─ experiences
  ├─ skills
  ├─ answers
  └─ preferences

jobs
  ├─ requirements
  ├─ sources
  └─ embeddings

applications
  ├─ answers
  ├─ documents
  ├─ attempts
  └─ events
```

PostgreSQL oferece transações, constraints, relacionamentos e histórico com alta maturidade.

`pgvector` permite manter busca vetorial no mesmo banco, eliminando a necessidade inicial de Pinecone, Weaviate, Qdrant ou outro banco vetorial dedicado.

### Por que não MongoDB

O problema não é primariamente documento-esquema-livre. Integridade, relações, auditoria e transações são mais importantes.

### Por que não banco vetorial dedicado no piloto

O volume esperado não justifica mais um serviço. Se benchmarks futuros demonstrarem que pgvector virou gargalo, a interface de busca semântica poderá ser extraída.

---

# 8. Hospedagem do PostgreSQL no piloto

## Decisão: Neon Free como primeira opção hospedada

Motivos:

- PostgreSQL real;
- free tier suficiente para um piloto pequeno;
- scale-to-zero;
- suporte a pgvector;
- portabilidade por usar Postgres padrão.

Não devemos usar funcionalidades proprietárias críticas do provedor sem necessidade. O objetivo é conseguir migrar para outro PostgreSQL se custos, privacidade ou disponibilidade mudarem.

---

# 9. ORM e migrations

## Decisão: SQLAlchemy 2 + Alembic

Motivos:

- maturidade;
- controle explícito sobre SQL e transações;
- migrations consolidadas;
- não acopla o domínio a uma solução experimental;
- compatível com PostgreSQL avançado.

Pydantic será usado nos contratos/API; SQLAlchemy nos modelos de persistência. Não devemos transformar automaticamente cada tabela em contrato público.

---

# 10. Automação de navegador

## Decisão: Playwright Python

Playwright é apropriado para:

- Chromium, Firefox e WebKit;
- execução headed ou headless;
- seletores semânticos;
- upload de arquivos;
- isolamento de contextos;
- automação async;
- screenshots/tracing de depuração.

### Como será usado

```text
ApplicationAttempt
      ↓
ATS Registry
      ↓
Adapter específico
      ↓
Playwright
      ↓
validação
      ↓
WAITING_USER ou SUBMITTED
```

### O que não faz parte da arquitetura

- stealth plugins como requisito;
- spoofing de fingerprint;
- serviços de CAPTCHA;
- rotação de proxy para contornar controles;
- mascarar automação como humano.

Bloqueio gera fallback para modo assistido/manual.

---

# 11. ATS Adapter Architecture

Toda integração de candidatura deve implementar um contrato semelhante a:

```text
ATSAdapter
├─ can_handle(url)
├─ inspect(job)
├─ start_application()
├─ map_fields()
├─ fill_known_fields()
├─ upload_documents()
├─ detect_unknown_questions()
├─ validate_before_submit()
├─ submit()                [quando permitido]
└─ collect_confirmation()
```

Adapters não devem acessar diretamente regras de matching ou prompts.

### Primeiros candidatos

- Gupy;
- Greenhouse;
- Lever.

A ordem final deve considerar acesso oficial, facilidade técnica e volume real de vagas encontradas no piloto.

---

# 12. Filas e tarefas

## Decisão do piloto: PostgreSQL como fila durável simples

Não adicionaremos Redis, RabbitMQ, Kafka ou Temporal no primeiro momento.

Tarefas pequenas podem ser registradas numa tabela de jobs com:

- status;
- `available_at`;
- tentativas;
- lease/lock;
- erro;
- payload versionado;
- timestamps.

Workers podem adquirir trabalho de forma transacional.

### Quando adotar fila dedicada

Somente quando métricas mostrarem necessidade de:

- alto throughput;
- fan-out;
- priorização complexa;
- milhares de jobs concorrentes;
- retenção/event streaming independente;
- workflows distribuídos longos.

---

# 13. Arquitetura de IA

## Decisão: IA como porta/adaptador, não como dependência espalhada

Nenhum módulo de domínio deve chamar diretamente SDK de OpenAI, Gemini, Anthropic ou outro provedor.

Criar interfaces como:

```text
TextGenerator
EmbeddingProvider
StructuredJudge
ResumeRewriter
```

Implementações ficam em adapters.

### Benefícios

- trocar provedor;
- rodar localmente;
- testar prompts sem rede;
- comparar qualidade;
- controlar custo;
- escolher provedor conforme sensibilidade dos dados.

---

# 14. Embeddings

## Decisão: não fixar modelo antes de benchmark

O português brasileiro e títulos profissionais locais tornam perigoso escolher modelo somente por ranking genérico.

Candidatos iniciais para avaliação local podem incluir modelos multilíngues como:

- BGE-M3;
- multilingual-e5.

A escolha deverá ser feita com um corpus HireIn contendo pares:

```text
perfil ↔ vaga relevante
perfil ↔ vaga parcialmente relevante
perfil ↔ vaga irrelevante
```

### Critérios

- qualidade em PT-BR;
- custo;
- latência em CPU;
- memória;
- dimensão do embedding;
- licença;
- facilidade de execução local.

Somente após o benchmark o modelo será fixado.

---

# 15. LLM generativo

## Decisão: provider-agnostic e benchmark por tarefa

Não existe um “melhor LLM” universal para todas as funções.

Devemos avaliar separadamente:

- extração estruturada;
- classificação de requisito;
- explicação de match;
- resposta aberta;
- tailoring de currículo.

### Métrica antes de preço

Modelo barato que inventa experiência é mais caro para o produto do que um modelo um pouco mais caro e confiável.

### Piloto gratuito

Opções locais ou free tiers podem ser usados **somente quando a política de dados for aceitável**.

Exemplo importante: em setembro de 2026, a documentação do Gemini Developer API informa que conteúdo enviado no free tier pode ser usado para melhorar produtos. Por isso, não será o default para currículo/dados pessoais do HireIn.

Cloudflare Workers AI declara que não utiliza Customer Content para treinar modelos ou melhorar serviços sem consentimento explícito e possui alocação gratuita; ele entra como candidato, mas somente será escolhido se o benchmark de qualidade passar.

---

# 16. Documentos e arquivos

### Piloto

Currículos e artefatos sensíveis podem permanecer no disco local fora do repositório.

### Evolução

Quando armazenamento remoto for necessário, a primeira opção arquitetural é object storage compatível com S3. Cloudflare R2 é candidato por oferecer API S3 e free tier, mas a escolha definitiva deve considerar a política de privacidade da fase pública.

O banco armazena metadados e referências, não blobs grandes sem necessidade.

---

# 17. Contrato Web ↔ API

FastAPI/OpenAPI será a fonte de verdade dos contratos HTTP.

O cliente TypeScript deve ser gerado a partir do schema OpenAPI sempre que possível.

Evitar:

```text
interface Job no frontend
+
class JobResponse no backend
+
atualização manual dos dois
```

Preferir:

```text
Pydantic schema
      ↓
OpenAPI
      ↓
TypeScript client gerado
```

---

# 18. Event log e auditoria

Ações importantes devem produzir eventos imutáveis ou append-only logicamente:

```text
JOB_DISCOVERED
MATCH_CALCULATED
APPLICATION_DRAFTED
ANSWER_GENERATED
ANSWER_CONFIRMED
APPLICATION_STARTED
USER_INTERVENTION_REQUIRED
APPLICATION_SUBMITTED
APPLICATION_CONFIRMED
STATUS_CHANGED
```

Esses eventos servem para:

- auditoria;
- debugging;
- métricas;
- aprendizado futuro;
- reconstrução de timeline.

---

# 19. Segurança arquitetural do piloto

O piloto será local-first.

Regras:

- API ligada preferencialmente a `127.0.0.1`;
- credenciais fora do Git;
- nenhum cookie/sessão de ATS versionado;
- documentos pessoais fora do repositório;
- logs com redaction;
- banco remoto acessado por TLS;
- permissões mínimas;
- sem exposição pública do Playwright worker.

Quando houver terceiros, o modelo de segurança muda e precisará de threat model formal.

---

# 20. Tecnologia escolhida x tecnologia adiada

| Camada | Piloto | Status |
|---|---|---|
| Web | SvelteKit + TypeScript | escolhido |
| Extensão | WXT + Svelte + MV3 | escolhido para fase Copilot |
| API | Python + FastAPI | escolhido |
| ORM | SQLAlchemy 2 | escolhido |
| Migrations | Alembic | escolhido |
| Banco | PostgreSQL | escolhido |
| Vetores | pgvector | escolhido |
| PostgreSQL hospedado | Neon Free | escolhido para piloto |
| Browser automation | Playwright Python | escolhido |
| Queue | PostgreSQL jobs | escolhido para piloto |
| Embedding model | benchmark multilíngue | **a decidir por evidência** |
| LLM | provider abstraction | **a decidir por tarefa** |
| Object storage remoto | R2 candidato | adiado |
| Auth multiusuário | OIDC/OAuth-compatible | adiado |
| Redis | não necessário agora | adiado |
| Kafka | não necessário agora | adiado |
| Kubernetes | explicitamente não necessário | adiado |
| Microserviços | não necessários | adiado |

---

# 21. Gatilhos de revisão arquitetural

Uma decisão só deve ser revisada por evidência concreta.

Exemplos:

### SvelteKit → outra UI

- limitação comprovada;
- ecossistema impede requisito crítico;
- custo de equipe supera benefício técnico.

### pgvector → vector database

- latência ou recall não atendem metas em volume real;
- necessidade de escala/isolamento específica.

### Postgres Queue → fila dedicada

- contenção;
- throughput insuficiente;
- workflows complexos;
- necessidade de prioridades/retries que tornem a implementação caseira arriscada.

### local worker → cloud workers

- múltiplos usuários;
- disponibilidade 24x7;
- necessidade de processamento sem máquina do usuário ligada;
- termos das plataformas permitirem o modelo operacional.

---

# 22. Referências técnicas consultadas

- FastAPI — Features: https://fastapi.tiangolo.com/features/
- FastAPI — Async: https://fastapi.tiangolo.com/async/
- Playwright Python: https://playwright.dev/python/
- WXT — Frontend frameworks: https://wxt.dev/guide/essentials/frontend-frameworks.html
- Cloudflare — SvelteKit deployment: https://developers.cloudflare.com/workers/framework-guides/web-apps/sveltekit/
- pgvector: https://github.com/pgvector/pgvector
- Neon — AI/pgvector docs: https://neon.com/docs/ai/ai-concepts
- Cloudflare Workers AI — Data usage: https://developers.cloudflare.com/workers-ai/platform/data-usage/
- Gemini Developer API — Pricing/data-use indication: https://ai.google.dev/gemini-api/docs/pricing

---

## 23. Conclusão

A arquitetura inicial foi escolhida para concentrar complexidade onde o produto realmente precisa dela.

O HireIn não será um app React com automação anexada depois. Ele será um **sistema de domínio e agentes**, com uma interface leve sobre um núcleo Python, persistência relacional e integrações explicitamente isoladas.

A regra de evolução será:

> **não adicionar infraestrutura por antecipação e não manter tecnologia por apego. Medir, comparar e trocar quando os dados justificarem.**
