# Match v1.6 — Professional Fit e Opportunity Compatibility

## Status

Implementação iniciada após o encerramento do Blind Holdout #4.

## Objetivo

Eliminar a mistura conceitual entre competência profissional e viabilidade/preferência da oportunidade.

O v1.5 ainda permitia que preferências entrassem no score final e que um blocker de localização transformasse o score legado em zero. Isso tornava impossível interpretar o número como Professional Fit puro.

O v1.6 separa as dimensões.

## Modelo

```text
Professional Fit
  score
  confidence
  band
  evidence / gaps / unknowns

Opportunity Compatibility
  score
  coverage
  blocked
  blockers
  preference results

Apply Intent
  valor humano 0–4
  não inferido pelo matcher
```

## Regras

### Professional Fit

- usa somente requisitos profissionais;
- `score` é calculado sobre requisitos efetivamente avaliados;
- `confidence` mede cobertura de evidência;
- abaixo de 60% de confiança a banda permanece `INSUFFICIENT_DATA`;
- localização, salário, contrato ou modalidade não reduzem o score profissional.

### Opportunity Compatibility

- usa resultados de preferência;
- possui score e cobertura próprios;
- blocker explícito de localização pode marcar `blocked = true`;
- blocker não altera Professional Fit;
- conflitos sem regra de blocker permanecem conflitos normais.

### Apply Intent

- pertence ao usuário;
- continua armazenado no módulo de avaliações;
- não é inferido pelo Match;
- não entra no Professional Fit.

## Compatibilidade de API

Campos legados continuam disponíveis:

| Campo legado | Semântica no v1.6 |
| --- | --- |
| `score` | alias de Professional Fit score |
| `band` | alias de Professional Fit band |
| `requirement_score` | alias de Professional Fit score |
| `evaluation_coverage` | alias de Professional Fit confidence |
| `preference_score` | alias de Opportunity Compatibility score |

Novos campos:

```json
{
  "professional_fit": {
    "score": 82,
    "confidence": 75,
    "band": "STRONG"
  },
  "opportunity_compatibility": {
    "score": 67,
    "coverage": 50,
    "blocked": true,
    "blockers": ["LOCATION"]
  }
}
```

## Ranking de avaliação

As métricas de Professional Fit deixam de usar blockers de oportunidade para alterar o ranking do benchmark.

Isso é necessário porque o ground truth do matcher é capacidade profissional, não decisão de candidatura.

Ranking/recomendação de produto será uma camada posterior e poderá combinar Fit, Compatibility, Intent, recência e exploração.

## Evidência

O v1.6 não recalibra pesos e não transforma UNKNOWN em MATCHED para melhorar métricas.

O problema de baixa cobertura observado no Holdout #4 permanece explícito e será tratado por melhorias auditáveis de evidência e Candidate Core, não por inflação de score.

## UX

A tela de revisão passa a mostrar lado a lado:

- Professional Fit;
- Opportunity Compatibility;
- Apply Intent.

Assim um usuário pode enxergar combinações como:

```text
Fit profissional: alto
Compatibilidade da oportunidade: bloqueada por localização
Apply Intent: baixo
```

sem interpretar uma restrição logística como falta de capacidade profissional.

## Critérios de aceite

1. blocker de localização não zera Professional Fit;
2. Professional Fit continua condicionado à confiança;
3. Opportunity Compatibility expõe score, cobertura e blockers;
4. Apply Intent permanece humano;
5. relatório de benchmark de Match usa Professional Fit;
6. contrato legado continua funcional;
7. UI mostra as três dimensões explicitamente;
8. sem mudança de pesos para otimizar holdouts revelados.
