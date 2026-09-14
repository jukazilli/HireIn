# HireIn — Infraestrutura

> **Status:** estratégia de infraestrutura do piloto  
> **Objetivo:** custo próximo de zero, baixa superfície operacional e caminho claro de evolução  
> **Documento anterior:** [04 — Engenharia](04-ENGINEERING.md)

---

## 1. Estratégia

O HireIn não precisa nascer com infraestrutura de SaaS.

A primeira infraestrutura será **local-first**, porque o piloto tem um único usuário e o componente mais delicado — automação de navegador — funciona melhor próximo da sessão real do usuário.

A infraestrutura evoluirá por fases.

```text
P0 — piloto local
      ↓
P1 — painel privado hospedado + agente local
      ↓
P2 — beta multiusuário
      ↓
P3 — escala
```

A passagem entre fases depende de evidência, não de expectativa.

---

# 2. P0 — Piloto local

## Objetivo

Validar o ciclo completo sem custo fixo relevante.

### Topologia

```text
┌──────────────────────────────┐
│ computador do piloto         │
│                              │
│ SvelteKit Web                │
│ localhost                    │
│       │                      │
│       ▼                      │
│ FastAPI Core                 │
│ 127.0.0.1                    │
│       │                      │
│       ├─────────────┐        │
│       ▼             ▼        │
│ local files     Playwright   │
│                 Agent        │
│                    │         │
└────────────────────┼─────────┘
                     │ HTTPS
                     ▼
               sites / ATS

                     HTTPS/TLS
                         │
                         ▼
                   Neon Postgres
```

### Componentes

#### Web

- SvelteKit;
- execução local;
- nenhuma necessidade inicial de CDN;
- build de produção deve continuar funcionando mesmo quando o app é usado localmente.

#### API

- FastAPI;
- bind em `127.0.0.1`;
- não exposta diretamente à internet;
- único usuário no piloto.

#### Agent

- processo local Python;
- Playwright;
- Chromium como primeiro navegador de execução;
- modo headed durante desenvolvimento e validação;
- automação pode ser observada e interrompida pelo usuário.

#### Banco

- Neon PostgreSQL Free;
- conexão TLS;
- pgvector habilitado quando necessário;
- apenas dados necessários ao piloto.

#### Arquivos

Inicialmente:

```text
~/.hirein/
├─ documents/
├─ generated/
├─ browser-profile/
└─ logs/
```

Esse diretório:

- não entra no Git;
- não fica dentro do repositório;
- deve ter permissões restritas ao usuário da máquina quando possível.

---

# 3. Por que não Docker obrigatório no P0

Docker pode ser útil, mas não será requisito para executar o agent local no começo.

Playwright e perfil de navegador precisam de integração razoável com o desktop durante o piloto.

Podemos usar container para:

- testes de PostgreSQL;
- CI;
- ambiente reproduzível da API.

Mas não devemos criar complexidade de GUI/browser containerizado antes de isso gerar benefício.

---

# 4. Banco remoto x local

Poderíamos usar PostgreSQL local, porém Neon foi preferido para o piloto porque:

- evita manutenção local do banco;
- facilita backup e acesso consistente;
- oferece free tier;
- pgvector é suportado;
- continua sendo PostgreSQL padrão.

### Regra de portabilidade

Migrations precisam rodar também em um PostgreSQL padrão fora da Neon.

Se alguma feature proprietária da Neon for proposta, ela deve passar por ADR próprio.

---

# 5. Embeddings no P0

Primeira preferência:

```text
modelo local
      ↓
Python worker
      ↓
pgvector
```

Objetivo:

- custo zero por embedding;
- dados do perfil não precisam sair para um provedor;
- benchmark reproduzível.

Se hardware local não oferecer desempenho suficiente, avaliar API externa com custo e política de dados explícitos.

---

# 6. LLM no P0

A infraestrutura não fica acoplada a um provedor.

Ordem de avaliação:

1. modelo/local inference quando qualidade for suficiente;
2. Cloudflare Workers AI dentro da alocação gratuita, se o benchmark passar;
3. provedor pago de baixo custo quando qualidade/privacidade justificarem.

### Regra de privacidade já no piloto

Não usar gratuitamente um provedor com política que permita utilizar currículo/dados pessoais para melhoria de produto sem decisão consciente.

Por isso o Gemini Developer API Free não é a opção default para dados pessoais do HireIn na política atual consultada.

---

# 7. Scheduler no piloto

Não será criado um cluster ou serviço de scheduler.

Para tarefas como descoberta de vagas:

- comando manual durante desenvolvimento;
- scheduler simples no processo local quando necessário;
- execução apenas enquanto a máquina estiver ligada é aceitável no P0.

O piloto não exige disponibilidade 24x7.

---

# 8. Segredos

Usar arquivo local ignorado pelo Git:

```text
.env
```

Com um `.env.example` contendo somente nomes das variáveis.

Nunca versionar:

- API keys;
- tokens;
- cookies;
- sessions;
- passwords;
- connection strings com senha;
- dados pessoais reais.

### GitHub

O repositório atual é público. Portanto, qualquer dado usado no piloto deve ser tratado como proibido dentro do repository tree.

---

# 9. Logs no P0

Logs locais com rotação simples.

Não precisamos inicialmente de Datadog, ELK, Grafana Cloud ou infraestrutura equivalente.

Necessário:

- JSON/structured logs;
- correlation/attempt ID;
- redaction;
- nível configurável;
- retenção curta.

Quando surgir produção multiusuário, a observabilidade deverá ser redesenhada.

---

# 10. Backups no piloto

### Banco

Usar recursos do provedor + export periódico quando dados começarem a ser relevantes.

### Documentos

Os documentos originais já devem existir em fonte externa/controlada pelo usuário.

O HireIn não deve ser a única cópia de currículo ou documentos importantes.

### Configurações

Preferências podem ser exportadas em formato estruturado no futuro.

---

# 11. P1 — Painel privado hospedado + agente local

Essa fase somente é necessária se quisermos acessar o painel sem iniciar tudo localmente.

Topologia desejada:

```text
Cloudflare
SvelteKit Web
      │
      ▼
Hosted API
      │
      ├──────────────→ Neon Postgres
      │
      ▼
Task table
      ▲
      │ outbound polling / secure channel
      │
Local Agent
Playwright
      │
      ▼
ATS
```

### Princípio importante

Mesmo com o painel hospedado, o agente pode continuar na máquina do usuário.

Isso traz vantagens:

- sessão/autenticação de ATS permanece local;
- navegador visível;
- menor custo de browser cloud;
- usuário pode assumir o processo;
- reduz necessidade de guardar credenciais de job boards no servidor.

O agent inicia conexões de saída. Evitar abrir porta do computador para internet.

---

# 12. Frontend hospedado

## Candidato: Cloudflare Workers

A documentação atual da Cloudflare recomenda Workers como plataforma principal para novos apps, e existe integração para SvelteKit.

Para o painel privado, o volume esperado é muito inferior ao free tier.

### Regra

Não mover lógica pesada de matching ou Playwright para Worker apenas porque o frontend está na Cloudflare.

O limite de CPU do plano gratuito torna Workers ótimo para frontend/BFF leve, não para workloads pesados de IA e browser automation.

---

# 13. Object storage remoto

Quando os documentos precisarem ficar disponíveis para API hospedada:

## Candidato: Cloudflare R2

Motivos:

- API compatível com S3;
- free tier suficiente para piloto/beta pequeno;
- sem cobrança de egress padrão;
- evita inventar um storage próprio.

### Requisitos antes de usar

- criptografia em trânsito;
- chaves privadas;
- bucket não público;
- URLs assinadas com curta duração;
- política de retenção;
- deleção consistente;
- classificação de dados.

---

# 14. P2 — Beta multiusuário

**Não implementar antes de privacidade/LGPD/security gate.**

Novas necessidades:

- autenticação real;
- isolamento por usuário;
- autorização;
- consentimento;
- retenção/deleção;
- storage remoto seguro;
- secrets management;
- observabilidade central;
- backups formais;
- rate limiting;
- abuse controls;
- worker orchestration;
- política de disponibilidade;
- audit log protegido.

### Topologia possível

```text
CDN / Edge
    │
Web App
    │
API containers
    │
PostgreSQL
    │
Job Queue
    ├─────────→ AI workers
    └─────────→ Agent workers / local agents

Object Storage
Observability
Auth Provider
```

Essa topologia é apenas direção, não autorização para provisionar serviços agora.

---

# 15. P3 — Escala

Somente métricas reais justificam:

- Redis/RabbitMQ/Temporal;
- replicas de banco;
- dedicated vector service;
- autoscaling workers;
- Kubernetes;
- multi-region.

A ordem deve ser orientada por gargalos observados.

---

# 16. Gatilhos para sair do local-first

Considerar API hospedada quando houver pelo menos um dos casos:

- necessidade real de acesso remoto;
- discovery precisa rodar com notebook desligado;
- segundo usuário;
- automações assíncronas frequentes;
- integração por webhook externo.

Considerar browser workers em cloud somente quando:

- o fluxo for permitido e estável;
- sessão local não for requisito;
- custo por execução estiver conhecido;
- segurança de credenciais estiver resolvida;
- houver benefício comparado ao local agent.

---

# 17. Ambientes

No piloto:

```text
dev
pilot
```

Não precisamos de `dev`, `qa`, `staging`, `preprod`, `prod` separados.

### `dev`

- dados sintéticos;
- mocks;
- testes.

### `pilot`

- dados reais do único usuário;
- migrations estáveis;
- ações reais conscientemente executadas.

Antes de beta público, criar `staging` formal.

---

# 18. CI/CD

## P0

GitHub Actions:

```text
push / PR
   ↓
lint + types + tests + build
```

Nenhum deploy automático é obrigatório.

## P1

Frontend pode ter preview/deploy automático.

API deve possuir deploy reproduzível por container.

### Regra

Não criar pipeline que execute candidatura real.

CI nunca possui credenciais de ATS de produção.

---

# 19. Infra as Code

Não começar com Terraform/OpenTofu apenas para criar dois recursos manualmente.

Quando P1/P2 criar múltiplos recursos persistentes e ambientes, adotar IaC.

Preferência futura: OpenTofu/Terraform-compatible, após avaliação dos providers realmente usados.

---

# 20. Observabilidade por fase

| Fase | Estratégia |
|---|---|
| P0 | logs locais + DB audit events |
| P1 | logs centralizados mínimos + error tracking |
| P2 | métricas, traces e alertas formais |
| P3 | SLOs e capacidade por componente |

Não coletar telemetria comportamental só porque uma ferramenta oferece SDK.

---

# 21. Referências de capacidade atuais

Valores consultados em setembro de 2026 e sujeitos a mudança:

### Cloudflare Workers Free

- 100.000 requests/dia;
- 10 ms de CPU por invocação no plano Free;
- adequado para frontend/BFF leve, não para Playwright.

### Neon Free

A documentação de pricing consultada informa, entre outros limites:

- 50 CU-hours/mês por projeto;
- 0,5 GB de storage por projeto;
- scale-to-zero;
- 5 GB de egress/mês;
- pgvector suportado pela plataforma.

### Cloudflare R2 Free

- 10 GB-month de storage;
- 1 milhão de operações Class A/mês;
- 10 milhões de operações Class B/mês;
- egress sem cobrança padrão.

### Workers AI

- alocação gratuita de 10.000 neurons/dia;
- Customer Content não é usado para treinar ou melhorar serviços sem consentimento explícito segundo a documentação atual.

Esses números devem ser revalidados antes de qualquer decisão de produção.

---

# 22. Referências oficiais

- Cloudflare Workers pricing: https://developers.cloudflare.com/workers/platform/pricing/
- Cloudflare Workers limits: https://developers.cloudflare.com/workers/platform/limits/
- Cloudflare SvelteKit: https://developers.cloudflare.com/workers/framework-guides/web-apps/sveltekit/
- Cloudflare R2 pricing: https://developers.cloudflare.com/r2/pricing/
- Cloudflare Workers AI data usage: https://developers.cloudflare.com/workers-ai/platform/data-usage/
- Cloudflare Workers AI pricing: https://developers.cloudflare.com/workers-ai/platform/pricing/
- Neon pricing overview: https://neon.com/pricing
- Neon pgvector concepts: https://neon.com/docs/ai/ai-concepts

---

## 23. Conclusão

Para o piloto, a melhor infraestrutura é a que **não existe sem necessidade**.

O HireIn começará com browser e core local, PostgreSQL gerenciado gratuito e IA intercambiável. Isso nos permite testar o problema real antes de pagar por disponibilidade, containers, filas, observabilidade e browsers remotos que ainda não precisamos.
