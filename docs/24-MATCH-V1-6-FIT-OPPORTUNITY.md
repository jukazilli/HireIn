# Match v1.6 — Professional Fit e Opportunity Compatibility

## Status

Implementada, testada e publicada em produção após o encerramento do Blind Holdout #4.

- PR: #42
- commit de produção: `1333863f9b262558acae512b5d32b2e2ec40643a`
- CI: contrato OpenAPI, web, Python e E2E aprovados
- sem migração de banco
- sem recalibração de pesos

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


## Regressão pós-Holdout #4

Esta regressão foi executada **depois** da revelação das avaliações humanas e, portanto, não é uma nova validação cega.

Como o v1.6 calcula Professional Fit diretamente a partir de `requirement_score` e `evaluation_coverage` já produzidos pelo matcher, os resultados profissionais do Holdout #4 ficam deterministicamente:

| Oportunidade | Professional Fit | Confiança |
| --- | ---: | ---: |
| Gaudium — Analista de Implantação | 100% | 20% |
| Populos — Analista de Implementação ITSM Pleno | 100% | 30% |
| Grupo Autoglass — Analista de Projetos I - PMO | 100% | 14% |
| Neogrid — Product Manager Specialist I | sem score | 0% |
| NEXDOM Healthtech — Consultor de Implantação e Negócios Júnior | 100% | 15% |

O blocker de localização da Populos passa corretamente para Opportunity Compatibility e deixa de transformar Professional Fit em zero.

### Efeito no ranking profissional

Usando o ranking de benchmark existente, que reduz scores de baixa confiança em direção ao prior neutro de 50, a ordem de regressão fica:

1. Populos;
2. Gaudium;
3. NEXDOM;
4. Grupo Autoglass;
5. Neogrid.

Métricas de regressão:

- amostra: 5;
- relevantes por Professional Fit humano >= 3: 3;
- vagas com score: 4;
- confiança média: 15,8%;
- Recall@5: 100%;
- NDCG@5: ~0,717.

No v1.5, o NDCG@5 havia sido 1,000 porque o blocker geográfico empurrava Populos para o fim do ranking. A queda no v1.6 não significa que a separação de dimensões está errada; ela revela que o blocker de oportunidade estava mascarando uma deficiência do Professional Fit.

### Diagnóstico

O caso Populos expõe o principal problema restante:

```text
Professional Fit = 100%
Confidence = 30%
muitos requisitos obrigatórios = UNKNOWN
```

Com pouca evidência avaliada, um conjunto pequeno de requisitos favoráveis ainda pode produzir 100% de Fit. O ranking suaviza esse número pela confiança, mas 30% de cobertura ainda pode colocar a vaga acima de oportunidades profissionalmente melhores que possuem cobertura ainda menor.

Isso não deve ser corrigido ajustando pesos para reproduzir o Holdout #4.

## Próximo gate de engenharia

Antes de usar Professional Fit como sinal forte do Search Profile v0, tratar a camada de evidência/confiança:

1. aumentar recuperação auditável de evidências já existentes no Candidate Core;
2. distinguir melhor ausência de evidência de contraprova confirmada;
3. revisar requisitos compostos para evitar que evidência parcial valide o conjunto;
4. investigar como representar evidência negativa/limites conhecidos sem transformar ausência em GAP;
5. avaliar ranking quando todas as oportunidades possuem `INSUFFICIENT_DATA`;
6. só depois rodar um novo conjunto cego para validar a evolução.

O Holdout #4 permanece conjunto de desenvolvimento/regressão e não deve ser reutilizado como validação cega.
