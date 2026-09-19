# Match v1.12 — Confidence-Aware Match & Ranking

## Evidência que motivou a mudança

O primeiro holdout estritamente cego após o v1.11 separou corretamente:

1. avaliação humana de Professional Fit e Apply Intent;
2. captura do Match inicial;
3. Evidence Resolver;
4. captura do Match enriquecido.

As cinco vagas do lote terminaram assim:

| Vaga | Fit humano | Match inicial | Cobertura inicial | Match enriquecido | Cobertura final |
| --- | ---: | ---: | ---: | ---: | ---: |
| Vedamotors | 4 | 100 | 43 | 79 | 100 |
| Essentia | 3 | 100 | 9 | 64 | 76 |
| Fin-X | 3 | 100 | 31 | 56 | 56 |
| Alloha | 2 | 75 | 50 | 57 | 88 |
| Itix | 2 | 100 | 16 | 44 | 100 |

O experimento confirmou que um score observado alto com cobertura muito baixa pode ser matematicamente correto e, ao mesmo tempo, inadequado para apresentação e ordenação.

Exemplo:

```text
Professional Fit observado: 100
Cobertura: 9%
Band: INSUFFICIENT_DATA
```

Esse resultado significa apenas que os poucos requisitos avaliados foram atendidos. Ele não significa que a vaga tenha aderência profissional comprovada de 100%.

## Objetivo

O v1.12 torna a incerteza parte explícita do contrato do Match sem recalibrar os pesos do Professional Fit.

O score atual continua existindo e mantém a mesma semântica:

```text
score = aderência entre requisitos efetivamente avaliados
```

São adicionados três sinais:

```text
ranking_score
score_floor
score_ceiling
```

## Confidence-adjusted ranking score

O sinal de ranking usa um prior neutro de 50.

```text
ranking_score =
    observed_fit * confidence
  + 50 * (1 - confidence)
```

Com confiança em escala 0–1.

Exemplos:

```text
100% fit / 100% confiança -> ranking 100
100% fit / 16% confiança  -> ranking 58
100% fit / 9% confiança   -> ranking ~54
75% fit / 50% confiança   -> ranking ~62
```

Baixa cobertura não é tratada como incompatibilidade. O sinal apenas reduz a certeza de um resultado extremo.

O benchmark de eval e o contrato público do Match passam a usar a mesma função.

## Faixa possível de Professional Fit

O v1.12 também calcula uma faixa determinística a partir dos requisitos.

### Floor

Assume que todos os requisitos ainda UNKNOWN terminariam como GAP.

```text
score_floor =
    matched_weight / total_professional_weight
```

### Ceiling

Assume que todos os requisitos ainda UNKNOWN terminariam como MATCHED.

```text
score_ceiling =
    (matched_weight + unknown_weight) / total_professional_weight
```

UNKNOWN continua sendo incerteza. Não é transformado em gap.

Quando toda a vaga foi avaliada:

```text
score_floor = score_ceiling = Professional Fit
```

## Relação entre faixa e ranking

O prior neutro de 50 equivale conceitualmente ao ponto médio da incerteza restante.

Portanto:

- score observado responde “entre o que já foi avaliado, quanto atende?”;
- score floor/ceiling responde “qual faixa ainda é possível?”;
- ranking score responde “qual sinal conservador devemos usar para ordenar enquanto falta evidência?”;
- confidence responde “quanto da vaga já conseguimos avaliar?”.

Nenhum desses valores representa probabilidade de entrevista ou contratação.

## UX

Quando a confiança fica abaixo do gate de 60%, a interface deixa de usar o score observado como headline.

Em vez de:

```text
Professional Fit
100%
Dados insuficientes
```

passa a priorizar:

```text
Professional Fit
Aderência ainda incerta
16% dos requisitos avaliados

Faixa possível 16%–100%
Sinal de ranking 58
```

O score observado continua disponível no contrato para auditoria e compatibilidade retroativa.

## Compatibilidade

Os campos legados permanecem inalterados:

- `score`;
- `requirement_score`;
- `evaluation_coverage`;
- `band`.

Novos campos em `professional_fit`:

```json
{
  "score": 100,
  "confidence": 16,
  "band": "INSUFFICIENT_DATA",
  "ranking_score": 58,
  "score_floor": 16,
  "score_ceiling": 100
}
```

O relatório de eval também expõe `ranking_score`.

## O que não muda

- pesos REQUIRED/PREFERRED;
- regras de MATCHED/GAP/UNKNOWN;
- Opportunity Compatibility;
- Apply Intent;
- Evidence Resolver;
- Candidate Core;
- atomização v1.11;
- política de provenance;
- ausência de LLM/embeddings no matcher atual.

## Critérios de aceite

1. score bruto continua idêntico ao v1.11;
2. baixa cobertura não exibe 100% como certeza visual;
3. ranking score converge para o score bruto conforme a confiança chega a 100%;
4. score floor nunca supera score ceiling;
5. UNKNOWN amplia a faixa, mas não cria GAP;
6. vaga totalmente resolvida possui floor = ceiling = score;
7. benchmark e produto usam a mesma função de ranking;
8. nenhuma recalibração específica para o holdout revelado.

## Próximo gate

Depois do deploy do v1.12:

1. rodar regressão sobre o holdout v1.11 já rotulado;
2. confirmar que o ranking bruto não sofreu alteração;
3. verificar a nova apresentação de baixa cobertura;
4. medir o ranking confidence-aware em novo lote inédito;
5. classificar erros restantes entre:
   - normalização;
   - evidência faltante;
   - equivalência semântica;
   - pesos/ranking;
   - preferência/oportunidade.

O Match só será considerado fechado para a Fase 3 quando o dataset rotulado de aproximadamente 30–50 vagas tiver evidência suficiente de ranking útil, explicabilidade e ausência de falsos fatos.

Depois desse gate, o roadmap manda avançar para a Fase 4 — Application Studio, antes de qualquer Auto Apply irrestrito.
