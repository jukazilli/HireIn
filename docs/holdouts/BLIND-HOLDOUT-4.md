# Blind Holdout #4 — protocolo

## Objetivo

Validar o Match v1.5 em um conjunto cego e inédito sem confundir aderência profissional com vontade de candidatura.

## Tamanho

5 vagas inéditas.

As vagas não podem ter sido usadas nos Holdouts #1, #2 ou #3 e não podem ser selecionadas com base no score do Match.

## Blinding

Antes da avaliação humana:

- não consultar o Match das cinco vagas;
- não ordenar o lote pelo Match;
- não adaptar as vagas para produzir um benchmark favorável;
- preservar uma mistura plausível de fit alto, médio e baixo quando a busca permitir;
- normalizar somente informações sustentadas pela publicação original.

## Avaliação humana

Para cada vaga, coletar antes da revelação do Match:

### Professional Fit — 0 a 4

Pergunta:

> Quanto meu perfil profissional atual atende esta vaga?

Escala:

- 0 — não atende;
- 1 — baixa aderência;
- 2 — aderência parcial;
- 3 — boa aderência;
- 4 — muito alinhada.

### Apply Intent — 0 a 4

Pergunta:

> Quanto eu realmente gostaria de me candidatar?

Escala:

- 0 — não me candidataria;
- 1 — muito improvável;
- 2 — talvez;
- 3 — provavelmente;
- 4 — eu me candidataria.

### Blocker real

Booleano separado. Deve representar algo objetivo que sozinho inviabiliza ou praticamente inviabiliza a candidatura.

### Motivo

Texto livre opcional para explicar discrepâncias entre Fit, Intent e blocker.

## Métrica principal do Match

O ground truth do algoritmo continua sendo `Professional Fit`.

A coluna histórica `relevance` é preservada no banco/API por compatibilidade e, a partir deste holdout, representa Professional Fit.

`Apply Intent` não altera o score do Match v1.5 e não entra nas métricas de ranking do matcher.

## Revelação

Somente após salvar Fit, Intent e blocker/motivo da vaga a interface pode revelar o Match.

## Análise após o lote

Comparar:

- Professional Fit humano vs Match v1.5;
- Recall@K e NDCG adequados ao lote de 5 vagas;
- confiança/cobertura;
- blockers humanos vs algorítmicos;
- diferenças entre Professional Fit e Apply Intent.

Com apenas cinco vagas, as métricas devem ser interpretadas como evidência pequena e não como estimativa estável de performance geral.

## Próximo gate

Se o Holdout #4 não revelar regressão estrutural relevante no Match v1.5, o próximo experimento será `Search Profile v0`, conforme `docs/23-JOB-DISCOVERY-STRATEGY.md` e ADR-0012.

---

# Resultado — 2026-09-17

O Blind Holdout #4 foi encerrado somente depois que as cinco avaliações humanas foram salvas. O Match v1.5 permaneceu oculto durante seleção, normalização, importação e rotulagem humana.

## Métricas oficiais

As métricas abaixo usam a implementação canônica de `services/api/src/hirein_api/evals/ranking.py`, com `Professional Fit >= 3` como relevante.

| Métrica | Resultado |
| --- | ---: |
| Amostra | 5 |
| Vagas relevantes | 3 |
| Vagas com score numérico | 4 |
| Cobertura média | 15,8% |
| Recall@5 | 100% |
| NDCG@5 | 1,000 |
| Recall@10 | 100%* |
| NDCG@10 | 1,000* |

\* Com somente cinco itens, as métricas @10 são equivalentes ao lote inteiro e não acrescentam poder de discriminação.

O ranking ajustado por confiança produziu a mesma ordem do ranking ideal de Professional Fit humano neste conjunto de cinco vagas. Esse resultado é positivo, mas deve ser tratado como evidência de amostra pequena, não como estimativa estável de performance geral.

## Blockers

Houve um blocker algorítmico explícito de localização no lote. Ele coincidiu com o blocker humano correspondente. O mecanismo de localização da v1.5, portanto, não apresentou regressão estrutural neste conjunto.

## Principal limitação revelada

A qualidade do ranking melhorou, mas a cobertura de evidência continua baixa. Todas as oportunidades não bloqueadas permaneceram com banda `INSUFFICIENT_DATA`, e a cobertura individual ficou entre 0% e 20%.

Isso significa que scores altos podem representar aderência apenas sobre uma parcela pequena dos requisitos efetivamente avaliados. Um valor como `100%` não deve ser apresentado ao usuário como aderência global quando a confiança está baixa.

A interface deve priorizar `Dados insuficientes` / confiança e deixar o percentual condicionado aos requisitos avaliados como informação secundária enquanto `evaluation_coverage < 60%`.

## Decisões de engenharia

1. Não recalibrar pesos com base neste holdout.
2. Preservar o ranking ajustado por confiança introduzido na v1.5.
3. Separar mais claramente `Professional Fit` de restrições da oportunidade, como localização, remuneração, modalidade e contrato.
4. Manter blockers explícitos como dimensão independente em vez de tratá-los como prova de baixa capacidade profissional.
5. Melhorar composição de evidências confirmadas para requisitos semânticos/compostos antes de ampliar o uso do score bruto.
6. Adicionar proteção de UX para combinações humanas logicamente contraditórias entre `Apply Intent` e `blocker_real`, sem corrigir a resposta automaticamente.

## Próxima iteração proposta

A próxima evolução do matcher deve trabalhar a separação de dimensões antes de qualquer ajuste de pesos:

```text
professional_fit_score
+ evidence_confidence
+ opportunity_compatibility
+ explicit_blockers
+ human_apply_intent
```

O ranking/recomendação poderá combinar essas dimensões em uma camada posterior, mas o `Professional Fit` não deve esconder preferência pessoal ou inviabilidade logística dentro do mesmo número.

## Status do conjunto

A partir da revelação dos resultados, o Blind Holdout #4 deixa de ser um conjunto cego e passa a ser dado de desenvolvimento/regressão. Ele não pode ser reutilizado como validação independente de uma versão futura do matcher.
