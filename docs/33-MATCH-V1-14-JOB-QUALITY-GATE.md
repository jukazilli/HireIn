# Match v1.14 — Job Normalization Quality Gate

## Contexto

O holdout cego #6 mostrou uma divergência que não deve ser corrigida alterando pesos do matcher.

A vaga da Confitec foi cadastrada com:

```text
title = Analista de Dados Pleno
```

enquanto a própria descrição normalizada declarava:

```text
A descrição da vaga busca Analista de Sistemas Pleno...
```

O Match avaliou corretamente os requisitos estruturados fornecidos. O problema é que o objeto de vaga descreve dois papéis diferentes.

## Objetivo

Adicionar uma camada conservadora de qualidade de normalização antes que uma vaga seja usada em recomendação automática.

O v1.14 **não altera**:

- Professional Fit;
- pesos REQUIRED/PREFERRED;
- confidence-aware ranking;
- Candidate Core;
- Evidence Resolver;
- Opportunity Compatibility;
- Apply Intent.

Ele adiciona metadata explícita:

```json
{
  "job_quality": {
    "status": "REVIEW",
    "rankable": false,
    "warnings": [
      "job_title_specialization_conflicts_with_description"
    ],
    "declared_role": "analista de sistemas pleno"
  }
}
```

## Regra conservadora

O quality gate não tenta compreender toda a descrição semanticamente.

Ele só reage quando encontra uma declaração explícita de papel no início da descrição, por padrões como:

- `vaga busca ...`;
- `vaga procura ...`;
- `buscamos ...`;
- `procuramos ...`;
- `oportunidade para ...`;
- `posição para ...`.

Menções incidentais como:

```text
"fazer interface com analistas de sistemas"
```

não ativam o gate.

## Conflitos detectados

### Família de papel diferente

```text
Título: Product Owner
Descrição: Buscamos Analista de Sistemas...
```

Resultado:

```text
job_role_family_conflicts_with_description
```

### Especialização incompatível dentro da mesma família

```text
Título: Analista de Dados
Descrição: A vaga busca Analista de Sistemas...
```

Resultado:

```text
job_title_specialization_conflicts_with_description
```

## Comportamento

Quando há conflito forte:

```text
status = REVIEW
rankable = false
```

O Match continua sendo calculado e exibido para auditoria.

Isso é deliberado: esconder o cálculo dificultaria depuração e benchmark.

Porém a interface avisa que a vaga não deve entrar em ranking/recomendação automática até que a fonte seja revisada.

## Benchmark

O relatório de avaliação passa a expor:

- `job_quality_status`;
- `rankable`;
- `job_quality_warnings`.

As métricas históricas continuam end-to-end e não removem automaticamente vagas problemáticas. Isso evita melhorar NDCG artificialmente excluindo erros da ingestão.

O quality gate existe para classificar a origem do erro, não para maquiar o benchmark.

## Relação com embeddings

Este gate não substitui busca semântica ou embeddings.

A arquitetura já prevê benchmark de embeddings multilíngues para equivalência semântica. O v1.14 resolve um problema mais básico: fonte internamente inconsistente.

Não faz sentido usar um modelo semântico para compensar uma vaga cujo título e descrição discordam explicitamente.

## Gate de fechamento da Fase 3

Após o deploy do v1.14, executar um último holdout cego pequeno.

Critérios:

1. nenhuma alteração adicional nos pesos;
2. snapshot inicial antes de Evidence Resolution;
3. quality gate identifica conflitos fortes sem falsos positivos;
4. ranking enriquecido permanece coerente com Fit humano;
5. erros remanescentes são classificados por origem;
6. se o erro dominante não for mais `RANKING_WEIGHT`, congelar o Match determinístico.

Se o último holdout passar, a Fase 3 pode ser encerrada e o roadmap avança para a Fase 4 — Application Studio.
