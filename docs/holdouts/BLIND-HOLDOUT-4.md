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
