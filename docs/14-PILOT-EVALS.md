# HireIn — Pilot Evaluation Dataset

## Status

Esta etapa implementa a baseline de avaliação do Match antes de embeddings, reranking ou LLM.

O objetivo não é melhorar o algoritmo nesta fase. É criar um mecanismo confiável para provar se uma mudança futura realmente melhora a priorização de vagas.

---

## 1. Princípio

O HireIn só deve adicionar complexidade quando houver um erro mensurável que a justifique.

A sequência é:

```text
Match v0 determinístico
        ↓
30–50 vagas reais
        ↓
labels humanas
        ↓
relatório de ranking
        ↓
classificação dos erros
        ↓
decisão técnica baseada em evidência
```

Nenhum dataset real é versionado.

---

## 2. Dados reais ficam fora do Git

A estrutura local é:

```text
.local-data/
├─ profile/
├─ resumes/
├─ jobs/
│  ├─ vaga-001.json
│  └─ ...
└─ evals/
   ├─ matching-labels.json
   ├─ import-manifest.json
   ├─ matching-report.json
   └─ matching-report.md
```

`.local-data/` já está ignorado pelo repositório.

As únicas amostras versionadas ficam em `evals/matching/fixtures/` e são explicitamente sintéticas.

---

## 3. Unidade de avaliação

Cada vaga real recebe uma label humana independente do score do HireIn:

```text
0 = irrelevante
1 = fraca
2 = razoável
3 = boa
4 = excelente
```

Também podem ser registrados:

```text
blocker_real = true | false
reason = texto livre
```

A label deve refletir a avaliação humana da oportunidade, não uma tentativa de reproduzir o resultado do algoritmo.

---

## 4. O que o benchmark mede

A baseline produz:

- número de vagas avaliadas;
- número de vagas humanamente relevantes;
- número de vagas que receberam score do Match;
- cobertura média do Match;
- `Recall@5`;
- `Recall@10`;
- `NDCG@5`;
- `NDCG@10`.

Para Recall, vagas com label `3` ou `4` são consideradas relevantes.

O NDCG preserva toda a escala `0–4`, premiando rankings que colocam vagas excelentes acima de vagas apenas razoáveis.

---

## 5. Como vagas sem score são tratadas

Uma vaga com:

```text
score = null
band = INSUFFICIENT_DATA
```

não recebe um score artificial para entrar no ranking.

Na baseline ela é posicionada depois das vagas com score.

Isso torna problemas de cobertura visíveis em vez de escondê-los.

---

## 6. CLI local

O script é:

```text
scripts/pilot_eval.py
```

### Importar vagas

```bash
uv run --package hirein-api python scripts/pilot_eval.py import
```

O script:

1. lê `.local-data/jobs/*.json`;
2. envia cada payload para `POST /api/v1/jobs`;
3. grava o UUID retornado em `.local-data/evals/import-manifest.json`;
4. não reinsere arquivos já mapeados no manifesto.

O manifesto é local porque relaciona arquivos potencialmente reais a registros do banco do piloto.

### Avaliar

```bash
uv run --package hirein-api python scripts/pilot_eval.py evaluate
```

O script:

1. carrega as labels humanas;
2. resolve cada arquivo pelo manifesto;
3. consulta `GET /api/v1/jobs/{id}/match`;
4. junta score e cobertura às labels;
5. calcula as métricas;
6. gera relatório JSON;
7. gera relatório Markdown para leitura humana.

### Executar as duas etapas

```bash
uv run --package hirein-api python scripts/pilot_eval.py run
```

A URL padrão da API é `http://localhost:8000` e pode ser substituída por `--api-base`.

---

## 7. Reexecução e identidade

O CLI não tenta adivinhar IDs existentes.

Se a API retornar `409` para uma vaga que não possui entrada no manifesto, o processo para com erro explícito.

Isso é intencional: associar silenciosamente um arquivo local ao registro errado contaminaria o benchmark.

---

## 8. Métricas

### Recall@K

Responde:

> Entre as vagas que eu realmente considero boas ou excelentes, quantas aparecem nas primeiras K posições do ranking?

No piloto:

```text
relevante = human_relevance >= 3
```

### NDCG@K

Responde:

> O ranking coloca as vagas mais relevantes mais perto do topo, respeitando que uma vaga 4 é melhor que uma 3, que é melhor que uma 2?

É a métrica principal quando a relevância humana é graduada.

### Cobertura

Também será acompanhada a cobertura média do Match.

Um algoritmo pode parecer conservador porque retorna `INSUFFICIENT_DATA` frequentemente. O benchmark precisa mostrar isso separadamente da qualidade de ordenação.

---

## 9. Taxonomia de erro para revisão manual

Ao revisar resultados incorretos, classificar preferencialmente em uma destas causas:

```text
MISSING_PROFILE_EVIDENCE
BAD_JOB_NORMALIZATION
SIMPLE_ALIAS
SEMANTIC_EQUIVALENCE
PREFERENCE_RULE
SALARY_RULE
SENIORITY_RULE
COVERAGE_FAILURE
RANKING_WEIGHT
OTHER
```

A primeira versão do arquivo de labels mantém apenas `reason` livre para não criar estrutura prematura. A taxonomia acima serve para a análise das primeiras 30–50 vagas e poderá virar campo estruturado depois que os padrões reais aparecerem.

---

## 10. Critério para adicionar tecnologia

Não adicionar embeddings apenas porque há falsos gaps.

Exemplos:

- se a maioria dos erros for `SIMPLE_ALIAS`, criar aliases/taxonomia é mais simples e auditável;
- se houver muita equivalência semântica real, benchmarkar embeddings pode fazer sentido;
- se o problema for classificação de requisitos, avaliar extração/classificação assistida por modelo;
- se o score estiver correto mas a explicação for ruim, melhorar apresentação antes do ranking;
- se o perfil estiver incompleto, corrigir Candidate Core/dados antes do Match.

A Etapa F só começa quando o dataset indicar qual problema vale resolver.

---

## 11. Critério de aceite

A Etapa E é considerada pronta tecnicamente quando:

- dados reais continuam fora do Git;
- vagas locais podem ser importadas de modo reproduzível;
- labels humanas podem ser registradas sem depender do Match;
- o Match de cada vaga pode ser coletado automaticamente;
- Recall@K e NDCG@K são calculados por código testado;
- relatórios local JSON e Markdown são produzidos;
- fixtures versionadas são exclusivamente sintéticas;
- a baseline funciona sem embeddings e sem LLM.

A validação de produto só termina depois que o piloto acumular aproximadamente 30–50 vagas reais rotuladas.
