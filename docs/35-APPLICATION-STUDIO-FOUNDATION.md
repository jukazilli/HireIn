# HireIn — Application Studio Foundation

> **Status:** implementação inicial da Fase 4  
> **Slice:** 4.1 — Job Workspace + Truth Boundary  
> **Match baseline:** congelada em `6961713ae95c874986ddc83ac3a949b5c452737a`  
> **Auto Submit:** OFF

## 1. Objetivo

A primeira slice da Fase 4 não começa escolhendo um LLM nem reescrevendo currículo.

Ela estabelece a fronteira que qualquer geração futura deverá respeitar:

```text
vaga avaliada
    ↓
Match v1.14
    ↓
evidências USER_CONFIRMED
    ↓
Candidate Core
    ↓
briefing determinístico
    ↓
[próxima slice] tailoring + diff + revisão persistida
```

O objetivo é tornar explícito, antes de qualquer texto generativo, **quais fatos profissionais podem sustentar uma candidatura**.

## 2. Decisões desta slice

### 2.1 Match permanece congelado

Nenhum peso, regra ou parser do Match é alterado.

O Application Studio apenas consome o contrato já produzido pelo Match v1.14.

### 2.2 Candidate Core continua sendo a fonte de verdade

O Studio não cria uma segunda base de competências, experiências ou fatos.

Podem aparecer como evidência segura nesta slice apenas itens cuja proveniência seja:

```text
USER_CONFIRMED
```

Isso inclui confirmações originadas no Evidence Gap Resolver, pois esse fluxo já promove respostas humanas válidas para `CandidateFact(USER_CONFIRMED)`.

### 2.3 UNKNOWN continua UNKNOWN

A ausência de evidência não autoriza inferência.

Um requisito `UNKNOWN`:

- não vira experiência;
- não entra como força;
- não pode ser usado por um futuro rewriter como fato;
- deve permanecer visível no briefing.

### 2.4 Sem LLM nesta slice

Ainda não existe provider escolhido para Resume Tailoring.

Isso é intencional e preserva o ADR-0006: a seleção do modelo deve ocorrer por eval específico da tarefa.

## 3. Entrega funcional

Nova rota:

```text
/applications
```

Nome de produto:

```text
Application Studio
```

A tela:

1. lista apenas vagas com avaliação humana registrada;
2. carrega vaga e Match reais pela API existente;
3. mostra Professional Fit e confiança;
4. reúne evidências de requisitos `MATCHED` com `source_type = USER_CONFIRMED`;
5. mostra o inventário confirmado do Candidate Core;
6. gera um briefing determinístico copiável;
7. mantém gaps e UNKNOWNs explícitos;
8. sinaliza quando o Match está em `INSUFFICIENT_DATA`;
9. deixa tailoring e submissão bloqueados.

## 4. Briefing determinístico

O briefing não é currículo e não é texto de candidatura.

Ele funciona como entrada auditável para a próxima etapa.

Contém:

- vaga e empresa;
- Professional Fit e confiança;
- evidências confirmadas ligadas aos requisitos atendidos;
- gaps explícitos;
- requisitos ainda não comprovados;
- regra de não transformar UNKNOWN em experiência.

Nenhuma informação nova é produzida.

## 5. Fronteira de implementação

Nesta slice, o Studio é uma **view sobre fontes de verdade existentes**.

Ele não persiste ainda:

- `ApplicationDraft`;
- estado `DRAFT / READY_FOR_REVIEW / APPROVED`;
- versões de currículo;
- diff;
- respostas de formulário;
- aprovação humana do documento final.

Esses itens entram na slice 4.2 para manter migration, contrato OpenAPI, máquina de estados e revisão humana em uma mudança isolada e testável.

## 6. Slice 4.2

A próxima implementação deverá introduzir o domínio `applications` no FastAPI/PostgreSQL.

Contrato mínimo esperado:

```text
ApplicationDraft
- id
- job_id
- profile_id
- status
- base_resume_ref
- tailored_content
- evidence_snapshot
- created_at
- updated_at
- approved_at
```

Estados iniciais:

```text
DRAFT
  ↓
READY_FOR_REVIEW
  ↓
APPROVED
```

Transições devem ser explícitas e testadas.

Material não aprovado não pode seguir para automação.

## 7. Tailoring v1

Depois da persistência e do diff, o Resume Tailoring v1 poderá ser conectado por uma porta de domínio, nunca diretamente a um SDK de provider.

Permitido:

- reorganizar;
- resumir;
- destacar;
- adaptar vocabulário.

Proibido:

- criar experiência;
- aumentar senioridade;
- inventar números ou resultados;
- transformar conhecimento genérico em requisito específico;
- promover `AI_DRAFT` ou `SYSTEM_INFERRED` a fato objetivo;
- esconder gap objetivo.

## 8. Gate da Fase 4

A Fase 4 não termina quando o sistema consegue produzir texto.

Ela termina quando o piloto demonstrar conjuntamente:

- 100% dos fatos objetivos corretos;
- 0 experiência inventada;
- alterações claramente identificáveis;
- revisão humana antes de aprovação;
- redução perceptível do trabalho de preparação;
- histórico suficiente para medir edições e rejeições.

Até esse gate:

```text
AUTO SUBMIT = OFF
```
