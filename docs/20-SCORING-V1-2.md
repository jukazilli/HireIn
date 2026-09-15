# HireIn Match — Scoring v1.2

## Objetivo

Reduzir falso otimismo no Match sem transformar ausência de evidência em `GAP`.

O Match v1.1 já preserva qualificadores da vaga e mantém três estados distintos:

- `MATCHED`: há evidência confirmada;
- `GAP`: há evidência suficiente para concluir incompatibilidade;
- `UNKNOWN`: falta evidência para concluir.

O problema observado no piloto era matemático: requisitos obrigatórios em `UNKNOWN` eram removidos do denominador do score. Isso podia elevar artificialmente vagas com um requisito central ainda não comprovado.

## Regra v1.2

O status do requisito não muda.

Para o score de requisitos:

1. `MATCHED` participa do numerador e denominador;
2. `GAP` participa apenas do denominador;
3. `UNKNOWN` **obrigatório** participa do denominador como risco não resolvido;
4. `UNKNOWN` preferencial continua neutro;
5. `INFO` continua fora do score.

A cobertura continua medindo apenas requisitos efetivamente avaliados (`MATCHED` + `GAP`). Portanto, um `UNKNOWN` obrigatório reduz a confiança do score, mas não é falsamente contado como requisito avaliado.

## Fórmula

```text
requirement_score =
  matched_weight /
  (evaluated_weight + unknown_required_weight)
```

Pesos atuais continuam os mesmos:

- obrigatório: 3;
- preferencial: 1;
- informativo: 0.

Nenhum peso especial por tecnologia, empresa ou domínio foi introduzido nesta versão. Isso evita calibrar o algoritmo especificamente para as 10 vagas do piloto.

## Evidência do piloto

Após Job Normalization v1.1, o ranking das 10 vagas apresentou correlação aproximada de `0,92` com as avaliações humanas. O maior desvio foi uma vaga TMS na qual `TMS` era obrigatório e `UNKNOWN`, mas o score permanecia alto porque o requisito desaparecia do denominador.

Aplicando apenas a regra conservadora da v1.2 sobre o mesmo conjunto, a correlação projetada sobe para aproximadamente `0,95`, sem alterar as notas humanas nem criar aliases adicionais.

A validação final deve ser feita novamente nas mesmas 10 vagas após deploy e, depois, em 10 vagas inéditas para evitar overfitting.

## Guardrails

- `UNKNOWN` não vira `GAP` automaticamente;
- nenhum LLM participa desta regra;
- nenhum domínio recebe peso manual extra;
- dados `AI_DRAFT` continuam sem elevar o score;
- blocker de localização continua prevalecendo sobre o score;
- cobertura mínima continua em 60%;
- o score não representa probabilidade de contratação.
