# HireIn — Resume Rewriter Eval

Este diretório documenta o benchmark local usado para comparar modelos de reescrita de currículo.

Dados reais do piloto **não** devem ser commitados. Eles ficam em:

```text
.local-data/evals/tailoring/
├─ preview.json
├─ candidates/
│  ├─ provider-a.json
│  └─ provider-b.json
├─ reviews/
│  ├─ provider-a.json
│  └─ provider-b.json
├─ report.json
└─ report.md
```

## Pré-requisito

O `preview.json` deve ser a resposta real de:

```text
GET /api/v1/applications/{application_id}/resume-preview
```

Isso exige uma candidatura `APPROVED`.

## Candidate output

Cada provider deve produzir exatamente o contrato `ResumeRewriteCandidate`.

Exemplo sintético:

```json
{
  "provider": "provider-example",
  "model": "model-example",
  "prompt_version": "v1",
  "blocks": [
    {
      "section": "SUMMARY",
      "text": "Atuação em implantação de sistemas e levantamento de requisitos.",
      "source_evidence_ids": [
        "11111111-1111-1111-1111-111111111111"
      ],
      "target_experience_id": null
    },
    {
      "section": "EXPERIENCE_BULLET",
      "text": "Realizou levantamento de requisitos para implantação.",
      "source_evidence_ids": [
        "22222222-2222-2222-2222-222222222222"
      ],
      "target_experience_id": "33333333-3333-3333-3333-333333333333"
    }
  ]
}
```

Cada bloco precisa citar a evidência que o sustenta.

## Human review

Um arquivo de review é opcional durante experimentação inicial, mas obrigatório para escolher um modelo.

```json
{
  "factual_precision": 5,
  "pt_br_quality": 4,
  "usefulness": 4,
  "editing_effort": 2,
  "unsupported_claims": 0,
  "notes": "Sem fatos inventados; pequenas mudanças de estilo."
}
```

Escalas humanas usam 1–5.

O gate factual exige:

```text
factual_precision = 5
unsupported_claims = 0
pt_br_quality >= 4
usefulness >= 4
```

## Execução

```bash
uv run --package hirein-api python scripts/tailoring_eval.py
```

O CLI avalia todos os arquivos de `candidates/` e procura um review com o mesmo nome em `reviews/`.

## Métricas determinísticas

### structural_pass

Falha quando:

- o modelo referencia evidence ID não aprovado;
- um bullet aponta para experiência inexistente;
- há blocos duplicados.

### evidence_coverage

Percentual das evidências permitidas que foram usadas por pelo menos um bloco.

Cobertura alta não significa qualidade alta. O modelo não deve tentar usar toda evidência apenas para maximizar a métrica.

### average_anchor_overlap

Sobreposição lexical média entre cada bloco e suas fontes declaradas.

É apenas um alerta barato para saídas desconectadas da fonte.

**Não prova factualidade semântica.**

Uma paráfrase correta pode ter overlap baixo; uma frase errada pode compartilhar palavras com a fonte.

## Regra de seleção

O relatório não escolhe automaticamente um vencedor.

A comparação deve considerar conjuntamente:

- structural pass;
- factual precision humana;
- unsupported claims;
- qualidade PT-BR;
- utilidade;
- esforço de edição;
- latência;
- custo;
- política de dados do provider.

A escolha final de provider/modelo exige um ADR substituindo o ADR-0006.
