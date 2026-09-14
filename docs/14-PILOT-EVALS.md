# HireIn — Pilot Evaluation Dataset

## Status

A baseline de avaliação do Match está implementada e agora possui um workspace visual para o piloto.

O objetivo continua sendo medir antes de adicionar complexidade. Esta etapa não melhora o algoritmo automaticamente e não adiciona embeddings, reranking ou LLM.

---

## 1. Princípio

O HireIn só deve adicionar tecnologia quando houver um erro mensurável que a justifique.

```text
Match v0 determinístico
        ↓
30–50 vagas reais
        ↓
avaliação humana 0–4
        ↓
Recall / NDCG / cobertura
        ↓
classificação dos erros
        ↓
decisão técnica baseada em evidência
```

A avaliação humana é a referência independente. Ela nunca deve ser alterada para fazer o algoritmo parecer melhor.

---

## 2. Onde os dados reais ficam

Dados reais não são versionados no Git.

O piloto pode usar duas formas locais complementares:

1. PostgreSQL local, usado pela interface `/jobs/review`;
2. `.local-data/`, usado pelo CLI de importação e relatórios offline.

A estrutura local opcional permanece:

```text
.local-data/
├─ profile/
├─ resumes/
├─ jobs/
└─ evals/
```

`.local-data/` está ignorado pelo repositório.

As únicas amostras versionadas ficam em `evals/matching/fixtures/` e são sintéticas.

---

## 3. Unidade de avaliação

Cada vaga pode receber uma avaliação humana:

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
reason = texto livre opcional
error_category = categoria opcional do erro dominante
```

A nota representa a percepção real do piloto sobre a oportunidade. Ela não deve copiar o score do HireIn.

---

## 4. Workspace visual

A rota do piloto é:

```text
/jobs/review
```

Ela permite:

- escolher uma vaga já cadastrada;
- visualizar o Match atual;
- comparar score e cobertura com a percepção humana;
- registrar nota `0–4`;
- registrar blocker real;
- escrever um motivo livre;
- classificar o erro dominante quando houver;
- acompanhar métricas agregadas sem editar JSON manualmente.

As labels ficam persistidas no PostgreSQL do piloto pela tabela:

```text
pilot_job_evaluations
```

A relação é 1:1 com `job_postings`.

---

## 5. API de avaliação

### Listar vagas para revisão

```text
GET /api/v1/evals/jobs
```

Retorna todas as vagas do Job Core junto da avaliação humana existente, quando houver.

### Salvar avaliação

```text
PUT /api/v1/evals/jobs/{job_id}
```

Payload:

```json
{
  "relevance": 4,
  "blocker_real": false,
  "reason": "A oportunidade faz sentido para meu perfil.",
  "error_category": null
}
```

### Relatório atual

```text
GET /api/v1/evals/report
```

O relatório recalcula o Match para as vagas rotuladas e produz a baseline usando as labels humanas persistidas.

Isso é importante: se o Match mudar em uma branch futura, as mesmas decisões humanas podem ser reutilizadas para comprovar se houve melhora ou regressão.

---

## 6. O que o benchmark mede

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

## 7. Como vagas sem score são tratadas

Uma vaga com:

```text
score = null
band = INSUFFICIENT_DATA
```

não recebe score artificial.

Na baseline ela é posicionada depois das vagas com score. Assim, falta de cobertura aparece como problema mensurável em vez de ser escondida.

---

## 8. Taxonomia de erro

A interface permite classificar o erro dominante como:

```text
MISSING_PROFILE_EVIDENCE
BAD_JOB_NORMALIZATION
SIMPLE_ALIAS
SEMANTIC_EQUIVALENCE
PREFERENCE_RULE
COVERAGE_FAILURE
RANKING_WEIGHT
OTHER
```

Interpretação:

- `MISSING_PROFILE_EVIDENCE`: o candidato possui a experiência, mas ela não está estruturada no perfil;
- `BAD_JOB_NORMALIZATION`: a vaga foi cadastrada ou normalizada de forma inadequada;
- `SIMPLE_ALIAS`: os dois lados usam nomes simples diferentes para o mesmo conceito;
- `SEMANTIC_EQUIVALENCE`: a relação existe, mas exige entendimento de contexto;
- `PREFERENCE_RULE`: modalidade, contrato, localização, senioridade ou salário foram tratados inadequadamente;
- `COVERAGE_FAILURE`: o Match ficou sem dados suficientes para decidir;
- `RANKING_WEIGHT`: os itens foram avaliados, mas os pesos produziram uma ordem ruim;
- `OTHER`: falha relevante ainda não coberta pela taxonomia.

A taxonomia é analítica. Registrar uma categoria não corrige automaticamente o algoritmo.

---

## 9. CLI local opcional

O fluxo por arquivos continua disponível para importação em lote e relatórios locais:

```bash
uv run --package hirein-api python scripts/pilot_eval.py import
uv run --package hirein-api python scripts/pilot_eval.py evaluate
uv run --package hirein-api python scripts/pilot_eval.py run
```

O CLI trabalha com `.local-data/jobs/*.json`, manifesto local e labels locais. Ele é útil para datasets maiores, automações de análise e reprodutibilidade fora da interface.

Para o uso cotidiano do piloto, `/jobs/review` é o fluxo preferencial.

---

## 10. Critério para adicionar tecnologia

Não adicionar embeddings apenas porque existem falsos gaps.

Exemplos:

- muitos `SIMPLE_ALIAS` → aliases/taxonomia podem ser suficientes;
- muitos `SEMANTIC_EQUIVALENCE` → benchmark de embeddings passa a fazer sentido;
- muitos `BAD_JOB_NORMALIZATION` → melhorar ingestão/classificação de requisitos primeiro;
- muitos `MISSING_PROFILE_EVIDENCE` → melhorar Candidate Core antes do Match;
- muitos `COVERAGE_FAILURE` → entender qual dado estruturado está ausente;
- muitos `RANKING_WEIGHT` → recalibrar pesos com o dataset antes de usar modelo generativo.

LLM só entra quando houver uma tarefa clara, eval correspondente e fallback determinístico.

---

## 11. Gate operacional

### Smoke test

Primeiro conjunto:

```text
5 vagas reais
```

Objetivo: confirmar que o fluxo de cadastro → Match → avaliação humana → relatório é confortável e confiável.

### Dataset de decisão

Depois:

```text
30–50 vagas reais
```

Nesse ponto devemos olhar distribuição das categorias de erro, Recall, NDCG e cobertura antes de escolher a próxima técnica.

---

## 12. Critério de aceite

A etapa de eval está pronta tecnicamente quando:

- dados reais continuam fora do Git;
- avaliações podem ser registradas pela interface;
- labels continuam independentes do score;
- persistência sobrevive a reinicializações do app;
- Match atual pode ser recalculado sobre labels antigas;
- Recall@K e NDCG@K são calculados por código testado;
- cobertura insuficiente continua visível;
- CLI local permanece disponível;
- migrations são reproduzíveis;
- baseline funciona sem embeddings e sem LLM.

A validação de produto termina apenas depois do dataset de aproximadamente 30–50 vagas reais rotuladas.
