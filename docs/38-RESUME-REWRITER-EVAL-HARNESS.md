# HireIn — Resume Rewriter Eval Harness

> **Status:** Fase 4 — slice 4.4  
> **Objetivo:** preparar benchmark de LLM sem selecionar provider antecipadamente  
> **Dados reais:** somente em `.local-data/`

## 1. Por que esta slice existe

O HireIn já possui uma fronteira factual determinística:

```text
Candidate Core
  ↓
ApplicationDraft APPROVED
  ↓
Resume Tailoring Preview
  ↓
allowed_evidence_ids
```

O próximo risco é introduzir uma LLM que produza texto plausível, porém não sustentado.

Por isso o provider só poderá ser conectado a um contrato estruturado e sua saída deverá ser mensurável.

## 2. Porta de domínio

A interface é:

```text
ResumeRewriter
  rewrite(ResumeRewriteInput)
    → ResumeRewriteCandidate
```

Nenhum SDK de provider pertence ao domínio.

Adapters futuros podem implementar essa porta para:

- OpenAI;
- Anthropic;
- Google;
- modelo local;
- outro provider.

## 3. Entrada

`ResumeRewriteInput` contém:

- application id;
- empresa e cargo;
- briefing aprovado;
- currículo direcionado determinístico;
- `allowed_evidence_ids`;
- gaps;
- unknowns;
- constraints explícitas.

O modelo não deve receber autorização aberta para explorar todo o Candidate Core.

## 4. Saída rastreável

Cada bloco gerado precisa conter:

```text
section
text
source_evidence_ids
target_experience_id (quando aplicável)
```

Se uma frase não consegue citar a evidência que a sustenta, ela não deveria existir na saída.

## 5. Validação determinística

O harness calcula:

- referências fora do boundary;
- target de experiência inválido;
- duplicação de blocos;
- cobertura de evidências;
- overlap lexical diagnóstico.

### Hard structural fail

A saída falha estruturalmente se:

```text
unsupported_reference_count > 0
OR invalid_target_count > 0
OR duplicate_block_count > 0
```

## 6. Factualidade semântica

Referenciar um ID válido não prova que a frase é fiel à evidência.

Exemplo:

```text
Fonte:
"SQL — consultas básicas"

Saída incorreta:
"Especialista em SQL com otimização avançada de bancos"
```

O ID pode estar correto e a frase continuar falsa.

Portanto a primeira seleção de modelo exige avaliação humana.

## 7. Gate humano

Critério inicial:

```text
factual_precision = 5/5
unsupported_claims = 0
pt_br_quality >= 4/5
usefulness >= 4/5
```

`editing_effort` é acompanhado separadamente: menor é melhor, mas não compensa erro factual.

## 8. Execução local

O CLI:

```bash
uv run --package hirein-api python scripts/tailoring_eval.py
```

lê:

```text
.local-data/evals/tailoring/preview.json
.local-data/evals/tailoring/candidates/*.json
.local-data/evals/tailoring/reviews/*.json
```

e gera:

```text
.local-data/evals/tailoring/report.json
.local-data/evals/tailoring/report.md
```

## 9. O que ainda não foi feito

Esta slice não:

- escolhe provider;
- chama API externa;
- envia dado pessoal;
- gera currículo em produção;
- persiste output de LLM;
- autoriza submissão.

## 10. Próximo gate

Depois de criar um pequeno dataset real de candidaturas aprovadas, executar o mesmo prompt e schema com modelos candidatos.

Registrar por execução:

- provider;
- model;
- prompt version;
- latência;
- tokens;
- custo;
- output estruturado;
- review humano.

Só depois dessa evidência devemos criar um ADR escolhendo o default para Resume Tailoring.

Até lá:

```text
LLM DEFAULT = UNDECIDED
AUTO SUBMIT = OFF
```
