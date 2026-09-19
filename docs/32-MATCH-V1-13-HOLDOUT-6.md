# Match v1.13 — Holdout cego #6

## Protocolo

Este lote foi executado sem contaminação:

1. cinco vagas inéditas foram cadastradas;
2. Professional Fit, Apply Intent e blocker foram avaliados sem abrir Match;
3. o Match inicial foi capturado em produção;
4. somente depois disso o Evidence Resolver foi utilizado;
5. o Match enriquecido foi capturado novamente.

Os timestamps confirmam que todas as resoluções humanas ocorreram depois do snapshot inicial.

## Vagas

| Empresa | Vaga | Fit humano | Intent | Blocker |
| --- | --- | ---: | ---: | --- |
| Central Ailos | Analista de Segurança da Informação II — IAM | 1 | 1 | não |
| Copabo | Analista de Pricing | 0 | 0 | não |
| Machado Meyer | Analista Sênior de Projetos | 2 | 1 | não |
| Confitec | Analista de Dados Pleno | 1 | 1 | sim |
| Grupo Piracanjuba | Analista de Projetos TI / Business Partner | 2 | 2 | sim |

## Match inicial

| Vaga | Score observado | Cobertura | Ranking confidence-aware | Faixa possível |
| --- | ---: | ---: | ---: | --- |
| Central Ailos | 100 | 56 | 78 | 56–100 |
| Copabo | 25 | 24 | 44 | 6–82 |
| Machado Meyer | 54 | 50 | 52 | 27–77 |
| Confitec | 80 | 44 | 63 | 35–91 |
| Grupo Piracanjuba | 70 | 43 | 59 | 30–87 |

O NDCG@5 do ranking inicial foi aproximadamente **0,760**.

Com apenas cinco vagas, esse valor é descritivo e não deve ser usado isoladamente para recalibrar pesos.

## Evidence Resolution

Foram coletadas 30 resoluções:

- 9 CONFIRMED;
- 1 PARTIAL;
- 20 NOT_HAVE;
- 0 UNSURE.

UNKNOWNs do lote caíram de 32 para 2.

Cobertura média:

- antes: **43,4%**;
- depois: **94,6%**.

## Match enriquecido

| Vaga | Fit humano | Score | Cobertura | Ranking | Band |
| --- | ---: | ---: | ---: | ---: | --- |
| Machado Meyer | 2 | 62 | 100 | 62 | PARTIAL |
| Confitec | 1 | 58 | 91 | 57 | PARTIAL |
| Grupo Piracanjuba | 2 | 57 | 100 | 57 | PARTIAL |
| Central Ailos | 1 | 56 | 100 | 56 | PARTIAL |
| Copabo | 0 | 50 | 82 | 50 | PARTIAL |

O NDCG@5 enriquecido foi aproximadamente **0,955**.

A correlação de ordem melhorou de forma importante, mas n=5 continua pequeno.

## Achado principal

O único erro de ordenação relevante no conjunto enriquecido foi:

```text
Confitec (Fit humano 1)
acima de
Piracanjuba (Fit humano 2)
```

A análise da fonte mostrou um problema anterior ao matcher:

```text
Título:
Analista de Dados Pleno

Descrição normalizada:
"A descrição da vaga busca Analista de Sistemas Pleno..."
```

Ou seja, o próprio objeto da vaga contém conflito entre o papel anunciado no título e o papel declarado na descrição.

Isso pertence à taxonomia:

```text
BAD_JOB_NORMALIZATION
```

e não justifica alterar os pesos do Professional Fit.

Quando a Confitec é removida apenas para análise diagnóstica — não para esconder o erro end-to-end — a ordenação das quatro vagas sem conflito de normalização é perfeita neste lote.

## Outros sinais

### Central Ailos

O Match inicial alto veio de requisitos transferíveis já confirmados, enquanto quatro requisitos específicos de IAM estavam UNKNOWN.

Depois das respostas humanas:

- os quatro UNKNOWNs viraram GAP;
- cobertura chegou a 100%;
- score caiu de 100 observado para 56.

O confidence-aware v1.12 evitou tratar 100/56 como certeza absoluta, mas o caso confirma que UNKNOWNs de domínio ainda precisam ser resolvidos quando a vaga está fora da trajetória principal.

### Copabo

O usuário confirmou ausência de experiência em Pricing/Precificação/Controladoria/Suprimentos e de Power BI, enquanto competências transversais foram confirmadas.

O score final de 50 é superior ao Fit humano 0, mas a vaga permanece no fim da ordenação do conjunto. Isso deve ser acompanhado nos próximos lotes antes de qualquer alteração de pesos.

### Machado Meyer e Piracanjuba

As duas vagas avaliadas como Fit 2 ficaram nas primeiras posições entre as vagas sem erro de normalização.

## Decisão

Os pesos permanecem congelados.

Não há evidência suficiente para nova calibração de REQUIRED/PREFERRED.

O próximo erro concreto a atacar está na qualidade da vaga antes do Match:

> título e descrição não podem representar funções incompatíveis sem que o sistema sinalize revisão.

Isso motiva o Match v1.14 — Job Normalization Quality Gate.
