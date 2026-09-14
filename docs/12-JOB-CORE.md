# Job Core v0

## Objetivo

O Job Core é a fonte de verdade das oportunidades dentro do HireIn.

Assim como o Candidate Core separa o candidato de um currículo específico, o Job Core separa a oportunidade do HTML, PDF, post ou página onde ela foi encontrada.

O primeiro corte é deliberadamente manual e auditável.

```text
vaga bruta
   ↓
JobPosting
   ↓
JobRequirements
```

Não existe scraping, browser automation ou parsing obrigatório por IA nesta etapa.

---

## Princípio central

A descrição original da vaga nunca deve ser substituída pela interpretação do HireIn.

O sistema armazena simultaneamente:

1. **fonte original** — texto bruto e URLs;
2. **dados normalizados** — empresa, cargo, modalidade, contrato, senioridade etc.;
3. **requisitos estruturados** — unidades que futuramente poderão ser comparadas ao Candidate Core.

Isso mantém rastreabilidade.

Se o HireIn afirmar futuramente que uma vaga exige SQL, deve ser possível voltar ao trecho da vaga que sustentou essa conclusão.

---

## JobPosting

A entidade principal possui:

```text
JobPosting
│
├── identidade / deduplicação
│   ├── fingerprint
│   ├── source_kind
│   ├── source_platform
│   ├── external_id
│   ├── source_url
│   └── apply_url
│
├── empresa e cargo
├── localização
├── modalidade
├── contrato
├── senioridade
├── remuneração
├── datas
├── status
├── description_raw
└── JobRequirements[]
```

A `description_raw` preserva a vaga original recebida pelo sistema.

---

## Fontes

Fontes previstas:

- `MANUAL`;
- `ATS`;
- `JOB_BOARD`;
- `COMPANY_SITE`;
- `OTHER`.

No piloto, a entrada principal continua sendo `MANUAL`.

Os outros tipos já existem no domínio para que futuras integrações não exijam remodelar a entidade.

---

## Deduplicação

Cada vaga recebe um fingerprint SHA-256 determinístico.

A identidade é escolhida nesta ordem:

### 1. ID externo + plataforma

Quando os dois existem:

```text
source_platform + external_id
```

é a identidade preferencial.

Exemplo:

```text
Gupy + 123456
```

### 2. URL da fonte

Se não houver ID externo, uma URL conhecida pode servir como identidade.

### 3. Fallback

Somente quando não existem identificadores melhores:

```text
empresa + cargo + localização
```

normalizados.

O objetivo não é provar que duas descrições textuais são semanticamente iguais. O objetivo inicial é impedir duplicatas óbvias no dataset do piloto.

Uma colisão conhecida retorna HTTP `409`.

---

## Requisitos estruturados

Um `JobRequirement` representa uma unidade comparável da vaga.

Campos principais:

```text
kind
importance
value
normalized_value
min_years
source_text
ordinal
```

### Tipos

O domínio inicial prevê:

- `SKILL`;
- `EXPERIENCE`;
- `EDUCATION`;
- `LANGUAGE`;
- `CERTIFICATION`;
- `LOCATION`;
- `WORK_MODEL`;
- `CONTRACT`;
- `DOMAIN`;
- `TOOL`;
- `RESPONSIBILITY`;
- `OTHER`.

### Importância

Cada requisito é classificado como:

- `REQUIRED` — requisito obrigatório declarado;
- `PREFERRED` — desejável/diferencial;
- `INFO` — informação contextual que não deve penalizar o candidato como requisito.

Essa separação é essencial para o Match.

Uma habilidade desejável não pode ter o mesmo peso de um blocker explícito.

---

## Rastreabilidade do requisito

Além do valor normalizado, o requisito pode manter `source_text`.

Exemplo:

```text
kind: TOOL
importance: REQUIRED
value: TOTVS Protheus
source_text: "Experiência comprovada com TOTVS Protheus é obrigatória"
```

Futuramente, mesmo que a extração seja feita por IA, a interface deverá conseguir explicar de onde veio a interpretação.

---

## Normalização

Valores dos requisitos recebem uma versão normalizada para comparação básica e deduplicação.

O v0 utiliza normalização determinística simples:

- case folding;
- remoção de espaços redundantes.

Exemplo:

```text
"  TOTVS   Protheus "
        ↓
"totvs protheus"
```

Isso **não é matching semântico**.

Sinônimos como:

```text
Analista de Implantação
Consultor de Implantação
```

continuam sendo conceitos diferentes nesta etapa.

Resolver equivalências e similaridade pertence ao HireIn Match/evals futuros.

---

## API

### Listar vagas

```http
GET /api/v1/jobs
```

Retorna um resumo das vagas e a quantidade de requisitos.

### Criar vaga

```http
POST /api/v1/jobs
```

Cria uma oportunidade normalizada.

Duplicata determinística:

```http
409 Conflict
```

### Detalhe

```http
GET /api/v1/jobs/{job_id}
```

### Substituir vaga

```http
PUT /api/v1/jobs/{job_id}
```

Mantém o ID interno e substitui os requisitos dentro da mesma unidade de trabalho.

---

## Persistência

Migration:

```text
0003_job_core
```

Tabelas:

```text
job_postings
job_requirements
```

`job_requirements.job_id` usa cascade delete.

Existe unicidade para:

- fingerprint da vaga;
- requisito semântico dentro da mesma vaga (`kind + importance + normalized_value`).

---

## Interface manual

A rota:

```text
/jobs
```

é um workspace de validação do Job Core.

Ela permite:

- registrar fonte e identificadores;
- informar empresa/cargo/localização;
- registrar modalidade, contrato e senioridade;
- registrar faixa salarial;
- colar a descrição integral;
- adicionar requisitos manualmente;
- classificar requisito por tipo e importância;
- preservar o trecho original do requisito;
- visualizar o dataset já salvo.

A interface declara explicitamente:

```text
Parsing por IA = desligado
Auto Apply = desligado
```

Ela existe para formar um dataset confiável antes de automatizar a ingestão.

---

## Por que ainda não usamos IA

Neste momento precisamos descobrir primeiro se o **modelo do domínio** representa corretamente vagas brasileiras.

Adicionar um LLM agora esconderia duas classes de erro:

1. modelagem inadequada;
2. extração inadequada.

Primeiro queremos testar manualmente cerca de 30–50 vagas reais e ajustar a ontologia.

Depois poderemos criar um conjunto de verdade humana:

```text
vaga bruta
+ requisitos esperados
+ importância esperada
```

Esse dataset poderá avaliar extração por regras ou IA de forma objetiva.

---

## O que ainda não é um blocker

O Job Core v0 não tenta interpretar automaticamente:

- benefícios;
- cultura;
- palavras subjetivas como “dinâmico”;
- score de compatibilidade;
- equivalência semântica de cargos;
- equivalência de tecnologias;
- relevância do requisito para o candidato.

Esses problemas pertencem a etapas posteriores.

---

## Dados e privacidade

O Job Core trabalha principalmente com dados públicos de oportunidades e empresas.

Mesmo assim, não devemos persistir sem necessidade:

- dados pessoais de recrutadores obtidos fora da finalidade da vaga;
- cookies/sessões;
- credenciais de portais;
- dados de outros candidatos.

Esses dados não são necessários para o Job Core.

---

## Fora do escopo

O Job Core v0 não inclui:

- crawler;
- scraping automático;
- extensão;
- Gupy adapter;
- Greenhouse adapter;
- Lever adapter;
- Playwright;
- APIs privadas de job boards;
- embeddings;
- LLM de parsing;
- HireIn Match;
- currículo adaptado;
- candidatura;
- Auto Apply.

---

## Gate para o próximo domínio

A Etapa C está pronta quando:

```text
vaga manual
   ↓
persistência
   ↓
deduplicação
   ↓
requisitos estruturados
   ↓
rastreabilidade ao texto original
   ↓
CI verde
```

Depois começa o **HireIn Match v0**.

O primeiro Match deve ser explicável e majoritariamente determinístico:

```text
Candidate Core
      +
Job Core
      ↓
blockers
      ↓
compatibilidades
      ↓
gaps
      ↓
score explicável
```

Embeddings e LLMs só deverão entrar quando os casos que regras determinísticas não resolvem estiverem medidos.
