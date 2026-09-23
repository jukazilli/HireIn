# HireIn — Resume Tailoring Foundation

> **Status:** implementação da Fase 4  
> **Slice:** 4.3 — Currículo estruturado + priorização determinística + diff  
> **Depende de:** `docs/36-APPLICATION-DRAFT-STATE.md`  
> **Auto Submit:** OFF  
> **LLM/provider:** ainda não selecionado

## 1. Objetivo

Criar a fronteira técnica entre uma candidatura aprovada e qualquer futura geração de currículo.

Esta slice não gera texto novo.

Ela produz:

```text
ApplicationDraft(APPROVED)
        ↓
Candidate Core USER_CONFIRMED
        ↓
ResumeDocument base
        ↓
priorização por evidence_snapshot aprovado
        ↓
ResumeDocument direcionado
        ↓
ResumeDiff
```

O resultado é um currículo estruturado e auditável que pode ser comparado antes de qualquer rewriter generativo.

## 2. Gate de entrada

O preview só pode ser criado para:

```text
ApplicationDraft.status = APPROVED
```

Estados `DRAFT` e `READY_FOR_REVIEW` retornam conflito.

Isso garante que um mecanismo de tailoring futuro não trabalhe sobre uma base que ainda não passou por revisão humana.

## 3. ResumeDocument

O documento estruturado contém:

- identidade e headline;
- contatos;
- highlights;
- experiências;
- claims por experiência;
- skills;
- formação;
- certificações;
- idiomas.

### Regra de provenance

Entram nas seções factuais apenas entidades:

```text
source_type = USER_CONFIRMED
```

Itens `AI_DRAFT`, `SYSTEM_INFERRED`, `RESUME_EXTRACTED` ou `ATS_IMPORTED` não são incluídos automaticamente.

### Resumo profissional

O campo livre `professional_summary` do Candidate Core não é reutilizado nesta etapa.

Motivo: hoje ele não possui provenance por claim. Reaproveitá-lo como bloco indivisível impediria validar factualidade frase a frase.

O resumo direcionado deverá ser criado futuramente somente a partir de claims permitidas.

## 4. Base x versão direcionada

### Base

Mantém:

- experiências em ordem cronológica;
- ordem atual das skills;
- ordem atual de highlights;
- ordem atual de formação, certificações e idiomas;
- claims confirmadas dentro de cada experiência.

### Direcionada

Não altera texto.

Pode apenas priorizar dentro das seções entidades que estejam no `evidence_snapshot` da candidatura aprovada.

Exemplos:

```text
Skills base:
Excel
SQL

Evidence snapshot:
SQL → requisito MATCHED

Skills direcionadas:
SQL
Excel
```

Claims de experiência seguem a mesma regra.

## 5. O que não pode ser reordenado

Experiências profissionais permanecem cronológicas.

Uma vaga-alvo não pode fazer o sistema mover uma experiência antiga acima de uma experiência atual apenas para parecer mais aderente.

O tailoring atua dentro da experiência, priorizando claims relevantes, sem reescrever a história profissional.

## 6. ResumeDiff

Toda mudança determinística produz uma entrada de diff:

```text
entity_type
entity_id
label
change = PRIORITIZED
before_index
after_index
reason
```

A razão é fixa:

```text
Evidência USER_CONFIRMED ligada a requisito MATCHED no draft aprovado.
```

Isso permite que a interface explique exatamente por que um item subiu de posição.

## 7. Endpoint

```text
GET /api/v1/applications/{application_id}/resume-preview
```

Resposta:

```text
application_id
job_id
company_name
job_title
base_resume
targeted_resume
diff
allowed_evidence_ids
guardrails
```

## 8. allowed_evidence_ids

Essa lista contém as entidades explicitamente presentes no `evidence_snapshot` aprovado.

Ela será a principal fronteira para o rewriter futuro.

Um provider generativo não deverá receber autorização implícita para inventar ou ampliar claims fora dessa lista.

## 9. Testes

A slice deve provar:

- preview bloqueado para `DRAFT`;
- preview bloqueado para `READY_FOR_REVIEW`;
- preview liberado para `APPROVED`;
- `AI_DRAFT` excluído do currículo estruturado;
- skill matched sobe de posição;
- claim matched sobe dentro da experiência;
- diff explica as priorizações;
- experiência continua cronológica;
- resumo profissional livre não vaza para o preview;
- OpenAPI e cliente TypeScript continuam derivados do backend.

## 10. Próxima slice — Rewriter Eval Harness

Antes de conectar um provider real, a próxima slice deve definir:

### Entrada

```text
ResumeTailoringInput
- job context mínimo
- ResumeDocument base
- ResumeDocument direcionado
- allowed_evidence_ids
- gaps
- unknowns
```

### Saída

```text
ResumeRewriteCandidate
- summary
- sections
- source_claim_ids por trecho
- rationale
```

### Métricas mínimas

- factual precision;
- unsupported claim rate;
- schema adherence;
- cobertura das evidências relevantes;
- qualidade PT-BR;
- edição humana necessária;
- latência;
- custo.

### Gate

Um modelo só pode ser escolhido depois de produzir resultados mensuráveis no dataset do piloto.

Até lá:

```text
LLM DEFAULT = UNDECIDED
AUTO SUBMIT = OFF
```
