# HireIn — Engenharia

> **Status:** baseline de engenharia do piloto  
> **Objetivo:** permitir evolução rápida sem transformar o piloto em código descartável  
> **Documento anterior:** [03 — Arquitetura](03-ARCHITECTURE.md)

---

## 1. Filosofia de engenharia

O HireIn precisa começar pequeno, mas não improvisado.

A meta não é escrever a menor quantidade possível de código. É escrever **o menor sistema que consiga provar a hipótese do produto com segurança, rastreabilidade e capacidade de mudança**.

Princípios:

- simplicidade deliberada;
- domínio antes de framework;
- integração externa atrás de adapters;
- estados explícitos;
- idempotência;
- dados com origem conhecida;
- IA tratada como componente não determinístico;
- logs úteis sem vazar dados;
- testes focados em risco;
- automação reversível;
- nenhuma dependência adicionada sem função clara.

---

## 2. Estrutura proposta do repositório

```text
HireIn/
├─ apps/
│  ├─ web/                 # SvelteKit
│  └─ extension/           # WXT + Svelte (quando iniciar Copilot)
│
├─ services/
│  ├─ api/                 # FastAPI / domínio
│  └─ agent/               # Playwright worker
│
├─ packages/
│  ├─ ui/                  # tokens/componentes compartilháveis TS
│  └─ generated-client/    # cliente TypeScript gerado do OpenAPI
│
├─ docs/
│  └─ ...
│
├─ scripts/
│  └─ ferramentas de desenvolvimento/eval
│
├─ evals/
│  ├─ matching/
│  ├─ extraction/
│  └─ generation/
│
└─ README.md
```

### Por que monorepo

Nesta fase:

- todos os componentes pertencem ao mesmo produto;
- mudanças de contrato precisam ser coordenadas;
- existe um único ciclo de release;
- separar repositórios aumentaria overhead sem isolamento real.

Monorepo não significa acoplamento irrestrito. As fronteiras de módulo continuam obrigatórias.

---

## 3. Gestão de dependências

### Python

Usar `uv` para ambiente, instalação e lockfile do ecossistema Python.

Motivos:

- lock reproduzível;
- velocidade;
- reduz combinação manual de pip/virtualenv/requirements;
- adequado para API, workers e scripts.

### TypeScript

Usar `pnpm` com workspace.

Motivos:

- workspace eficiente;
- compartilhamento controlado entre `web`, `extension` e packages;
- lockfile único para a camada TypeScript.

### Regra

Não adicionar dependência somente para economizar poucas linhas de código.

Antes de adicionar biblioteca, avaliar:

1. manutenção ativa;
2. licença;
3. superfície de segurança;
4. tamanho/impacto;
5. dificuldade de remoção;
6. se a plataforma já resolve o problema.

---

## 4. Organização do backend por domínio

Não organizar o core somente por artefato técnico como `controllers/`, `services/`, `models/` globais.

Preferir módulos por capacidade:

```text
hirein/
├─ profile/
├─ jobs/
├─ matching/
├─ applications/
├─ documents/
├─ ai/
├─ ats/
├─ audit/
└─ shared/
```

Dentro de cada módulo podem existir:

```text
domain.py
schemas.py
repository.py
service.py
routes.py
```

quando fizer sentido.

A estrutura deve crescer com o domínio, não por ritual.

---

## 5. Camadas e dependências

Regra de direção:

```text
HTTP / CLI / Worker
        ↓
Application Services
        ↓
Domain
        ↓
Ports (interfaces)
        ↑
Adapters externos
```

O domínio não deve importar:

- SDK de LLM;
- Playwright;
- Neon;
- Cloudflare;
- bibliotecas específicas de ATS.

Esses detalhes pertencem às bordas.

---

## 6. Modelo de dados e migrations

### Regras

- todas as mudanças de schema passam por migration;
- migration aplicada não é editada depois de compartilhada;
- constraints importantes ficam também no banco;
- datas em UTC no armazenamento;
- IDs internos não dependem de informação pessoal;
- exclusão lógica somente quando há requisito real;
- eventos de auditoria não devem ser silenciosamente sobrescritos.

### Identificadores

Preferir UUID/UUIDv7 ou identificador equivalente semântico para entidades distribuíveis.

Não usar CPF, e-mail ou URL externa como chave primária.

---

## 7. Proveniência de fatos

Informação do candidato deve carregar origem.

Exemplo conceitual:

```text
CandidateFact
- id
- type
- value
- source_type
- source_ref
- confidence
- confirmed_at
- created_at
```

Possíveis origens:

```text
USER_CONFIRMED
RESUME_EXTRACTED
ATS_IMPORTED
AI_DRAFT
SYSTEM_INFERRED
```

### Regra crítica

`AI_DRAFT` e `SYSTEM_INFERRED` não podem ser usados como fatos objetivos em candidatura automática sem uma regra explícita de promoção/validação.

---

## 8. Estado de candidatura como máquina de estados

Estados não serão strings alteradas livremente.

Transições devem ser validadas.

Exemplo:

```text
DRAFT
  ↓
READY_FOR_REVIEW
  ↓
APPROVED
  ↓
APPLYING
  ├─→ WAITING_USER
  ├─→ FAILED
  └─→ SUBMITTED
          ↓
      CONFIRMED
```

Resultados de recrutamento formam outra dimensão posterior:

```text
REJECTED
ASSESSMENT
INTERVIEW
OFFER
HIRED
WITHDRAWN
```

Separar estado operacional de resultado evita confundir “worker falhou” com “empresa rejeitou”.

---

## 9. Idempotência

Candidatura duplicada é um erro grave.

Cada tentativa deve possuir chave idempotente baseada em algo como:

```text
candidate_id
+
normalized_job_id
+
application_variant
```

Antes de executar `submit`, o sistema precisa verificar:

- já existe candidatura confirmada?
- existe tentativa em andamento?
- houve resposta ambígua do ATS após submit?

Em caso de dúvida após um timeout pós-envio, **não repetir automaticamente o submit**.

Marcar para inspeção.

---

## 10. Engenharia dos ATS Adapters

Cada adapter deve ser isolado e versionável.

Estrutura possível:

```text
ats/
├─ base.py
├─ registry.py
├─ greenhouse/
│  ├─ adapter.py
│  ├─ selectors.py
│  ├─ parser.py
│  └─ fixtures/
├─ lever/
└─ gupy/
```

### Seletores

Preferir, nesta ordem:

1. atributos/contratos públicos estáveis;
2. `label` e relações acessíveis;
3. roles/ARIA;
4. `name`/identificadores semânticos;
5. seletores CSS específicos somente quando inevitável.

Evitar:

```text
nth-child(7)
classe gerada aleatoriamente
XPath absoluto
```

### Contratos

Adapter deve retornar erros de domínio conhecidos, por exemplo:

```text
UnsupportedFlow
UnknownRequiredField
UserInterventionRequired
PlatformBlockedAutomation
SubmissionUncertain
ApplicationConfirmed
```

Não propagar exceção bruta do Playwright para a UI.

---

## 11. Política de CAPTCHA e anti-bot

Engenharia não deve “resolver” bloqueios criando uma corrida armamentista contra as plataformas.

Ao detectar proteção:

```text
1. parar interação automática
2. persistir estado
3. informar usuário
4. permitir takeover
5. retomar somente quando seguro
```

Não implementar como parte do produto:

- spoofing de fingerprint;
- CAPTCHA farms;
- stealth patches;
- proxy rotation para burlar limite;
- simulação artificial de comportamento humano para enganar proteção.

Além de risco de plataforma, isso tornaria o produto estruturalmente frágil.

---

## 12. Prompts como código versionado

Prompts importantes não devem viver como strings soltas em handlers.

Estrutura:

```text
ai/prompts/
├─ requirement_classifier/
│  ├─ v1.txt
│  └─ schema.py
├─ match_explainer/
├─ resume_tailoring/
└─ open_answer/
```

Cada execução relevante registra:

- prompt version;
- model/provider;
- parâmetros;
- schema de saída;
- input references;
- resultado validado;
- custo quando disponível.

Isso permite comparar regressões.

---

## 13. Structured Output primeiro

Sempre que possível, a IA deve retornar estrutura validável.

Evitar:

```text
"Acho que ele combina bastante com a vaga."
```

Preferir:

```json
{
  "recommendation": "recommended",
  "required_gaps": [],
  "optional_gaps": ["Power BI avançado"],
  "evidence": ["experiência em implantação de ERP"],
  "confidence": 0.89
}
```

A resposta passa por schema antes de entrar no domínio.

Texto narrativo pode ser derivado depois.

---

## 14. Evals de IA

Testes unitários tradicionais não são suficientes para LLMs.

Manter datasets pequenos e revisados para:

- extração de currículo;
- classificação required vs desired;
- equivalência de cargos brasileiros;
- detecção de blocker;
- ranking de vagas;
- tailoring sem invenção.

### Exemplo de dataset

```text
case_id
candidate_profile_fixture
job_fixture
expected_blockers
expected_relevance_band
forbidden_claims
```

Antes de trocar modelo ou prompt, executar eval.

### Regra

Não promover um modelo porque ele parece melhor em três testes manuais.

---

## 15. Benchmark de embeddings

Criar corpus PT-BR com casos reais anonimizados do piloto.

Comparar modelos usando métricas como:

- Recall@K;
- NDCG@K;
- ranking humano;
- latência CPU;
- consumo de RAM;
- tamanho de storage.

A escolha do embedding deve ser reproduzível.

---

## 16. Testes

### 16.1 Unitários

Foco em:

- regras de filtro;
- blockers;
- score aggregation;
- state machine;
- idempotência;
- normalização;
- deduplicação.

### 16.2 Integration

- PostgreSQL real em container/CI;
- migrations;
- repositories;
- OpenAPI;
- adapters de IA com fake provider.

### 16.3 ATS contract tests

Usar fixtures de HTML permitidas/capturadas para testar mapeamento sem acessar portais a cada execução.

### 16.4 E2E

Poucos e críticos:

```text
perfil → job → match → draft → application flow
```

Ambientes externos reais não devem ser parte obrigatória de todo CI porque são instáveis e podem causar ações reais.

---

## 17. Fixtures e dados de teste

Nunca usar currículo real completo ou credenciais reais em fixtures versionadas.

Criar persona sintética:

```text
Pessoa Exemplo
Analista de Implantação
experiência fictícia controlada
```

Testes que precisarem de dados do piloto devem executar localmente em diretório não versionado.

---

## 18. Logging

Logs devem ser estruturados.

Exemplo conceitual:

```json
{
  "event": "application_field_mapped",
  "attempt_id": "...",
  "ats": "greenhouse",
  "field_type": "phone",
  "result": "success"
}
```

Não registrar por padrão:

- currículo integral;
- telefone;
- CPF;
- respostas sensíveis;
- tokens;
- cookies;
- passwords;
- HTML integral de páginas autenticadas.

Implementar redaction central.

---

## 19. Erros e retries

Retry deve existir somente para erros reconhecidamente transitórios.

### Pode tentar novamente

- timeout antes de qualquer ação irreversível;
- falha temporária de rede;
- rate limit com indicação de retry;
- erro de leitura idempotente.

### Não tentar automaticamente

- submit cujo resultado ficou incerto;
- CAPTCHA;
- pergunta obrigatória desconhecida;
- alteração estrutural do ATS;
- autenticação expirada;
- validação de dados rejeitada.

---

## 20. CI do piloto

Em todo pull request ou push relevante:

```text
Python
- lint/format
- type check
- unit tests
- integration tests essenciais

TypeScript/Svelte
- lint
- type check / svelte-check
- unit tests
- build

Global
- migration validation
- secret scanning
```

Playwright contra ATS real não faz parte do CI automático.

---

## 21. Branching e commits

Começar simples:

- `main` sempre utilizável;
- branches curtas por mudança;
- pull request mesmo em projeto solo para revisar diff quando mudança for relevante;
- commits pequenos e descritivos;
- sem commits de `.env`, arquivos pessoais ou sessões de navegador.

Não adotar GitFlow pesado no piloto.

---

## 22. Definition of Done

Uma feature não está pronta porque “funcionou uma vez”.

Para fluxos críticos, considerar:

- regra de domínio implementada;
- erros conhecidos tratados;
- log/auditoria suficiente;
- testes adequados;
- nenhum dado sensível vazando em logs;
- documentação atualizada quando muda contrato;
- comportamento de fallback definido;
- impacto em custo conhecido quando envolve IA externa.

---

## 23. Política de dívida técnica

Dívida conscientemente aceita deve ser marcada com:

```text
motivo
risco
quando revisar
```

Exemplo aceitável:

> “No piloto, não há autenticação multiusuário porque API e UI rodam localmente. Revisar antes de qualquer exposição pública.”

Exemplo não aceitável:

> “Depois a gente vê segurança.”

---

## 24. Métrica de engenharia do piloto

Não perseguiremos cobertura de código como objetivo isolado.

Indicadores mais relevantes:

- zero candidaturas duplicadas causadas pelo sistema;
- zero fatos inventados enviados;
- percentual de flows que terminam em estado conhecido;
- taxa de intervenção manual por ATS;
- regressões detectadas antes de executar candidatura real;
- tempo para reparar adapter quebrado;
- custo por candidatura preparada;
- capacidade de reproduzir uma decisão de IA.

---

## 25. Conclusão

A engenharia do HireIn deve proteger exatamente os pontos em que um agente de carreira pode causar dano: **dados incorretos, ação duplicada, automação frágil e decisões impossíveis de explicar**.

O código do piloto pode ser pequeno. Os contratos sobre verdade, idempotência, estados e auditoria não podem ser vagos.
