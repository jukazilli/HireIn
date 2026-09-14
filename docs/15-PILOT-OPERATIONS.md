# HireIn — Operação do Piloto

## Objetivo

Este documento descreve como executar o piloto individual do HireIn sem avançar prematuramente para IA, scraping ou Auto Apply.

O objetivo operacional é responder uma pergunta simples:

> O HireIn consegue priorizar vagas que eu realmente considero boas melhor do que uma ordenação ingênua?

---

## 1. Fluxo principal

O fluxo recomendado do piloto é:

```text
/pilot
  ↓
/
Candidate Profile
  ↓
/jobs
Cadastro manual de vagas
  ↓
/jobs/match
Inspeção do Match
  ↓
/jobs/review
Avaliação humana
  ↓
/pilot
Métricas + diagnóstico
```

O dashboard `/pilot` é o ponto de entrada operacional.

---

## 2. Smoke test — 5 vagas

Antes de formar um dataset maior, usar apenas 5 vagas reais.

Escolher vagas que representem situações diferentes:

1. uma vaga que pareça excelente para o perfil;
2. uma vaga boa, mas com algum gap real;
3. uma vaga razoável;
4. uma vaga claramente fraca;
5. uma vaga com linguagem/sinônimos diferentes do perfil para testar normalização.

O objetivo destas 5 vagas não é medir performance estatística.

Elas servem para detectar:

- erro de cadastro;
- requisito mal estruturado;
- score inexplicável;
- cobertura muito baixa;
- problema na revisão humana;
- problema de persistência;
- dificuldade de uso do fluxo.

---

## 3. Avaliação humana

Cada vaga recebe uma relevância independente do score do HireIn:

```text
0 = eu não me candidataria
1 = fraca
2 = razoável
3 = boa
4 = excelente
```

A nota deve ser dada com base na oportunidade real, não para concordar com o algoritmo.

Também registrar, quando fizer sentido:

```text
blocker_real = true | false
reason = explicação livre
error_category = causa dominante do erro
```

---

## 4. Taxonomia de erro

Usar a categoria apenas quando houver algo relevante para diagnosticar.

```text
MISSING_PROFILE_EVIDENCE
```

A vaga exige algo que realmente existe no histórico do candidato, mas o Candidate Core não contém evidência suficiente.

```text
BAD_JOB_NORMALIZATION
```

O requisito foi estruturado incorretamente a partir da vaga.

```text
SIMPLE_ALIAS
```

O problema poderia ser resolvido por um alias simples, por exemplo nomes equivalentes de ferramentas ou cargos.

```text
SEMANTIC_EQUIVALENCE
```

Os textos são semanticamente equivalentes, mas não por igualdade textual simples.

```text
PREFERENCE_RULE
SALARY_RULE
SENIORITY_RULE
```

O problema está numa regra determinística específica.

```text
COVERAGE_FAILURE
```

A análise retornou muitos `UNKNOWN` / `INSUFFICIENT_DATA` mesmo com informações suficientes disponíveis.

```text
RANKING_WEIGHT
```

Os requisitos foram avaliados corretamente, porém o peso relativo produziu uma ordenação ruim.

```text
OTHER
```

O erro não se encaixa nas categorias anteriores.

---

## 5. Gate após 5 vagas

O smoke test é aprovado quando:

- as 5 vagas podem ser cadastradas sem quebra operacional;
- o Candidate Profile é suficiente para produzir Match;
- cada Match possui explicação compreensível;
- as avaliações humanas persistem;
- `/pilot` mostra o progresso correto;
- o relatório é gerado;
- nenhuma informação real aparece no Git;
- nenhum erro crítico de modelagem impede continuar.

Se um problema operacional grave aparecer, corrigir antes de coletar mais vagas.

---

## 6. Baseline mínima — 30 vagas

Após o smoke test, aumentar o dataset gradualmente.

Meta mínima:

```text
30 vagas avaliadas
```

Nesse momento observar:

- Recall@5;
- Recall@10;
- NDCG@5;
- NDCG@10;
- cobertura média;
- proporção de vagas sem score;
- distribuição das categorias de erro;
- quantidade de blockers reais;
- proporção de vagas humanas 3–4.

Não alterar o algoritmo toda vez que uma vaga isolada parecer errada.

Primeiro procurar padrões.

---

## 7. Baseline estendida — 50 vagas

Se o fluxo estiver saudável, continuar até aproximadamente 50 vagas.

Objetivo:

```text
reduzir o risco de escolher tecnologia com base em poucos exemplos
```

A Etapa F deve ser escolhida a partir do erro dominante.

Exemplos:

```text
SIMPLE_ALIAS dominante
→ taxonomia/aliases
```

```text
SEMANTIC_EQUIVALENCE dominante
→ benchmark de embeddings PT-BR/multilíngues
```

```text
BAD_JOB_NORMALIZATION dominante
→ melhorar parsing/classificação da vaga
```

```text
MISSING_PROFILE_EVIDENCE dominante
→ melhorar Candidate Core/importação de currículo
```

```text
RANKING_WEIGHT dominante
→ recalibrar pesos e ranking
```

A presença de IA no roadmap depende destes resultados.

---

## 8. O que não fazer durante o piloto

Não:

- aumentar score manualmente para “parecer certo”;
- alterar labels humanas para concordar com o HireIn;
- adicionar embeddings antes de saber se equivalência semântica é um problema relevante;
- adicionar LLM para resolver aliases triviais;
- criar scraping em massa;
- criar Auto Apply;
- publicar dados reais do candidato ou das avaliações no Git;
- interpretar score como probabilidade de contratação.

---

## 9. Dashboard

A página:

```text
/pilot
```

mostra:

- status do Candidate Profile;
- quantidade de vagas cadastradas;
- quantidade de vagas revisadas;
- progresso 5 / 30 / 50;
- número de vagas boas/excelentes;
- blockers reais;
- métricas de ranking;
- categorias de erro dominantes;
- próxima ação recomendada.

O dashboard não possui lógica própria de Match.

Ele apenas apresenta dados produzidos pelos módulos já validados.

---

## 10. Critério de encerramento desta fase

A fase de validação termina quando houver dados suficientes para escrever uma decisão técnica do tipo:

> Nas primeiras N vagas do piloto, X% dos erros relevantes vieram de equivalência semântica. Regras e aliases resolveram apenas Y%. Portanto vamos benchmarkar embeddings A/B/C usando o dataset real anonimizado/local.

ou:

> A maioria dos erros veio de normalização e evidência ausente. Embeddings não atacariam o gargalo dominante. A próxima etapa será melhorar ingestão e modelagem.

Essa evidência é o gate para qualquer nova tecnologia de IA.
