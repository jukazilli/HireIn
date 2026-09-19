# Match v1.13 — Benchmark Purity

## Problema encontrado

Durante a revisão final do Match v1.12, a implementação do benchmark ainda carregava uma regra antiga:

```text
algorithm_blocked = true
→ ranking_signal = -1
```

Isso contradizia a arquitetura definida desde o Match v1.6.

O benchmark usado para validar o matcher deve responder somente:

```text
"Quão bem o Professional Fit ordena vagas segundo a avaliação humana de aderência profissional?"
```

Localização, modalidade, contrato e outros blockers pertencem a **Opportunity Compatibility**.

Apply Intent pertence ao usuário.

Misturar qualquer uma dessas dimensões no ranking de avaliação pode melhorar ou piorar NDCG artificialmente sem que o matcher profissional tenha mudado.

## Correção

O `ranking_signal` do benchmark passa a usar exclusivamente:

```text
Professional Fit observado
+
confidence/cobertura
```

pela fórmula confidence-aware do v1.12:

```text
ranking_score =
    fit * confidence
  + 50 * (1 - confidence)
```

`algorithm_blocked` continua disponível como metadata para diagnóstico, mas não altera o ranking profissional.

## Separação de dimensões

### Benchmark do Match

Usa:

- Professional Fit;
- confidence;
- labels humanas de Fit 0–4.

Não usa:

- location blocker;
- work-model blocker;
- contract blocker;
- salary blocker;
- Apply Intent.

### Ranking/recomendação do produto

Será uma camada posterior e poderá combinar:

- Professional Fit;
- Opportunity Compatibility;
- Apply Intent;
- recência;
- exploração/diversidade;
- outros sinais documentados.

Esse ranking de produto não deve ser confundido com a métrica de qualidade do matcher.

## Critérios de aceite

1. um blocker de oportunidade não altera `ranking_signal`;
2. duas vagas com o mesmo Fit/confiança recebem o mesmo sinal mesmo que uma esteja bloqueada por localização;
3. NDCG/Recall do benchmark medem apenas capacidade profissional;
4. Opportunity Compatibility continua disponível no relatório para análise independente;
5. nenhum peso do Match é alterado;
6. nenhuma evidência do Candidate Core é alterada.

## Relação com o gate da Fase 3

O projeto já ultrapassou o volume mínimo documentado de 30–50 labels humanas.

Antes de declarar o Match fechado, os próximos holdouts devem verificar separadamente:

1. qualidade do Professional Fit confidence-aware;
2. qualidade da Opportunity Compatibility;
3. qualidade do Candidate Core após Evidence Resolution;
4. incidência de erros pela taxonomia do piloto.

Somente depois disso a Fase 3 pode ser encerrada e o roadmap avança para a Fase 4 — Application Studio.
