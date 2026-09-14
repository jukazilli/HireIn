# HireIn — Plano da primeira implementação

> **Status:** pronto para iniciar a vertical slice do piloto
> **Escopo:** transformar a documentação-base em um primeiro fluxo funcional sem Auto Apply irrestrito
> **Regra:** implementar apenas o necessário para provar o ciclo candidato → vaga → match → preparação → revisão

---

## 1. Objetivo da primeira vertical slice

A primeira versão funcional não deve tentar provar todo o HireIn.

Ela deve responder uma pergunta simples:

> **Conseguimos representar corretamente um candidato real, interpretar uma vaga real e produzir uma recomendação de candidatura explicável sem inventar informações?**

Fluxo mínimo:

```text
Candidate Profile
      ↓
Job Input
      ↓
Job Normalization
      ↓
Rule Filters / Blockers
      ↓
Match v0
      ↓
Explanation
      ↓
Application Draft
      ↓
Human Review
```

Nesta etapa:

- não existe submissão automática;
- não existe browser agent operando ATS real;
- não existe multiusuário;
- não existe autenticação pública;
- não existe billing;
- não existe scraping em massa;
- não existe dependência obrigatória de LLM pago.

---

## 2. Estrutura inicial do monorepo

Criar somente os diretórios necessários à vertical slice:

```text
HireIn/
├─ apps/
│  └─ web/
│
├─ services/
│  └─ api/
│
├─ packages/
│  └─ generated-client/
│
├─ evals/
│  ├─ matching/
│  └─ extraction/
│
├─ docs/
│  ├─ adr/
│  └─ ...
│
├─ scripts/
│
├─ pnpm-workspace.yaml
├─ pyproject.toml
└─ README.md
```

Não criar `apps/extension` ou `services/agent` até o fluxo de Match + Application Draft estar validado.

---

## 3. Toolchain definida

Conforme a baseline de engenharia:

### TypeScript

- pnpm workspace;
- SvelteKit;
- TypeScript strict;
- svelte-check;
- formatter/linter definidos no bootstrap do projeto;
- testes unitários para regras de UI quando houver lógica relevante.

### Python

- uv;
- Python em versão estável compatível com as dependências escolhidas;
- FastAPI;
- Pydantic;
- SQLAlchemy 2;
- Alembic;
- pytest;
- type checking;
- lint/format automatizados.

### Contratos

- FastAPI gera OpenAPI;
- cliente TypeScript é gerado a partir do contrato;
- frontend não duplica manualmente schemas da API.

---

## 4. Domínios que entram na primeira slice

### 4.1 Profile

Responsável por representar fatos profissionais e preferências.

Entidades/conceitos iniciais:

```text
CandidateProfile
Experience
Education
Skill
Certification
Language
CareerPreference
CandidateFact
```

Regras obrigatórias:

- cada fato objetivo possui origem;
- fato vindo de IA não vira verdade automaticamente;
- perfil deve distinguir informação objetiva de preferência;
- dados sensíveis ficam fora do MVP sempre que não forem necessários.

### 4.2 Jobs

Responsável por representar uma vaga de forma normalizada.

Conceitos iniciais:

```text
Job
Company
JobRequirement
JobPreference
JobLocation
Compensation
```

Requisitos devem distinguir:

```text
REQUIRED
PREFERRED
UNKNOWN
```

### 4.3 Matching

Responsável por produzir recomendação e evidências.

Saída conceitual:

```json
{
  "score": 0.86,
  "recommendation": "recommended",
  "blockers": [],
  "strengths": [],
  "gaps": [],
  "evidence": []
}
```

### 4.4 Applications

Nesta fase representa apenas o rascunho da candidatura.

Estados iniciais:

```text
DRAFT
READY_FOR_REVIEW
APPROVED
```

`APPLYING` e `SUBMITTED` ficam fora da primeira slice.

---

## 5. Primeira versão do Match

O Match v0 deve ser deliberadamente híbrido.

### Camada 1 — Regras determinísticas

Avaliar antes de IA:

- localização incompatível;
- modalidade incompatível;
- tipo de contrato incompatível;
- senioridade claramente incompatível;
- requisito obrigatório confirmado como ausente;
- faixa salarial incompatível quando ambas forem conhecidas.

Um blocker obrigatório não pode ser compensado por similaridade semântica alta.

### Camada 2 — Similaridade / equivalência

Usar inicialmente heurísticas e/ou embeddings apenas quando o benchmark mínimo existir.

Não esconder a origem da pontuação.

### Camada 3 — Julgamento estruturado opcional

LLM pode ser usado para:

- classificar requisito ambíguo;
- relacionar experiência real com requisito;
- explicar o resultado.

Sempre com saída estruturada validada.

### Regra

O score não é uma verdade matemática. É um instrumento de priorização que deve ser auditável.

---

## 6. Dataset inicial do piloto

Criar dois conjuntos separados.

### Fixtures versionadas

Somente dados sintéticos.

Usar uma persona fictícia para CI e testes.

### Dataset real local

Fora do Git:

```text
.local-data/
├─ profile/
├─ resumes/
├─ jobs/
└─ evals/
```

Adicionar ao `.gitignore` desde o primeiro commit de código.

Objetivo inicial:

- 1 perfil real completo;
- 5 vagas para smoke test;
- depois 30–50 vagas reais para benchmark.

Cada vaga real deverá receber avaliação humana simples:

```text
0 = irrelevante
1 = fraca
2 = razoável
3 = boa
4 = excelente
```

E, quando aplicável:

```text
blocker_real = true/false
motivo
```

Esse conjunto será a base do primeiro eval de ranking.

---

## 7. Ordem de implementação

### Etapa A — Bootstrap

Entregas:

- monorepo;
- workspace TS;
- ambiente Python;
- `.gitignore` seguro;
- `.env.example` sem secrets;
- FastAPI health check;
- SvelteKit carregando;
- CI mínimo;
- conexão local com Postgres de desenvolvimento;
- Alembic funcionando.

Aceite:

```text
frontend builda
backend inicia
testes executam
migration sobe banco vazio
nenhum secret ou dado real versionado
```

### Etapa B — Candidate Core

Entregas:

- schema do candidato;
- migrations;
- API CRUD mínima;
- tela de perfil;
- proveniência de fatos;
- importação manual estruturada.

Ainda não importar currículo com IA.

Aceite:

- perfil real pode ser representado sem campos improvisados;
- informação objetiva e preferência são distintas;
- origem dos fatos é persistida.

### Etapa C — Job Core

Entregas:

- schema de vaga;
- entrada manual por URL + texto copiado;
- normalização estruturada;
- requisitos required/preferred;
- tela de detalhe da vaga.

Aceite:

- uma vaga real pode ser representada de forma consistente;
- requisitos eliminatórios podem ser marcados explicitamente.

### Etapa D — Match v0

Entregas:

- regras determinísticas;
- score por dimensão;
- blockers;
- strengths/gaps;
- explicação por evidência;
- primeira tela de Match.

Aceite:

- nenhum blocker é escondido por score alto;
- usuário consegue entender por que recebeu aquela recomendação;
- resultado é reproduzível para entradas iguais quando não usa IA.

### Etapa E — Dataset e eval

Entregas:

- script para importar dataset local;
- labels humanas;
- relatório de ranking;
- Recall@K / NDCG@K quando aplicável;
- baseline sem embeddings.

Aceite:

- conseguimos medir se uma alteração melhora ou piora ranking.

### Etapa F — IA controlada

Somente depois da baseline.

Adicionar uma tarefa por vez:

1. extração de requisitos;
2. classificação required/preferred;
3. explicação do match;
4. tailoring de resumo profissional.

Cada inclusão precisa de eval e fallback.

### Etapa G — Application Draft

Entregas:

- versão adaptada do currículo/summary;
- respostas sugeridas;
- evidências usadas;
- diff entre original e adaptado;
- aprovação humana.

Aceite:

- zero fatos novos não suportados;
- usuário consegue identificar toda alteração;
- material não aprovado não pode seguir para automação futura.

---

## 8. Regras para o Codex

Ao receber este projeto, o Codex deve:

1. ler `README.md`;
2. ler `docs/03-ARCHITECTURE.md`;
3. ler `docs/04-ENGINEERING.md`;
4. ler `docs/07-PRIVACY-SECURITY-LGPD.md`;
5. ler `docs/adr/README.md` e ADRs relacionados à tarefa;
6. implementar somente o escopo solicitado;
7. não substituir stack sem ADR;
8. não adicionar serviços externos sem justificativa;
9. não criar Auto Apply antes da fase definida;
10. não inserir dados reais em fixtures;
11. não colocar provider SDK dentro do domínio;
12. não introduzir microserviços, Redis, Kafka ou vector DB dedicado sem evidência e ADR;
13. não selecionar LLM/embedding definitivo sem eval;
14. não implementar mecanismos para burlar anti-bot/CAPTCHA.

---

## 9. Definition of Done da primeira slice

A slice só está pronta quando for possível executar:

```text
1. cadastrar perfil
2. cadastrar vaga real
3. visualizar requisitos normalizados
4. gerar Match
5. visualizar blockers/strengths/gaps
6. ver evidências que sustentam a recomendação
7. gerar draft de candidatura sem inventar fatos
8. revisar manualmente o draft
```

E os seguintes controles estiverem verdadeiros:

- nenhum dado sensível real versionado;
- migrations reproduzíveis;
- testes de domínio passando;
- contrato OpenAPI válido;
- cliente TypeScript gerável;
- logs não contêm PII desnecessária;
- custo de cada chamada externa observável;
- nenhuma submissão de vaga ocorre automaticamente.

---

## 10. O que vem depois

Somente após essa slice e o dataset de 30–50 vagas:

```text
benchmark de embeddings
        ↓
ADR do embedding default
        ↓
melhoria do Match
        ↓
Application Studio amadurece
        ↓
Playwright/ATS Adapter supervisionado
```

O browser agent é consequência de um bom sistema de decisão e preparação; não é o primeiro produto a ser construído.
