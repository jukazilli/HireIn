# Blind Holdout #3 — Development baseline

## Status

Concluído com avaliação humana feita antes da revelação do Match v1.4.

Depois da revelação, este lote deixou de ser holdout cego e passou a ser conjunto de desenvolvimento/regressão. Ele não deve ser usado para provar a qualidade final da v1.5.

## Resultado do v1.4

A amostra contém 10 vagas inéditas no momento da avaliação humana.

Principais sinais observados:

- 1 vaga recebeu relevância humana >= 3;
- Recall@5: 0%;
- NDCG@5: aproximadamente 0,053;
- NDCG@10: aproximadamente 0,414;
- cobertura média: aproximadamente 17,5%;
- 6 de 10 vagas receberam score numérico.

O erro dominante foi estrutural: vagas sem score por evidência insuficiente eram ordenadas depois de vagas com score numérico 0, mesmo quando o 0 vinha de incompatibilidade conhecida. Além disso, requisitos compatíveis com evidências já confirmadas no Candidate Core continuaram como `UNKNOWN` em casos de formação, implantação de ERP, treinamento e projetos.

## Decisão

O v1.5 deve corrigir a semântica de aderência/confiança e a recuperação segura de evidências antes de qualquer recalibração de pesos.

O próximo benchmark cego real deve ser o Blind Holdout #4, usando vagas novas e sem consultar o Match antes da avaliação humana.
