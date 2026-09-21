# HireIn — Application Draft State

> **Status:** implementação da Fase 4  
> **Slice:** 4.2 — Persistência, snapshot e revisão humana  
> **Depende de:** `docs/35-APPLICATION-STUDIO-FOUNDATION.md`  
> **Match baseline:** congelada em `6961713ae95c874986ddc83ac3a949b5c452737a`  
> **Auto Submit:** OFF

## 1. Objetivo

Transformar o Application Studio de uma view de preparação em um workflow persistente e auditável, sem introduzir geração por LLM e sem alterar o Match.

A unidade persistida é o `ApplicationDraft`, vinculada ao perfil do piloto e à vaga.

```text
Candidate Core + Job + Match v1.14
              ↓
      ApplicationDraft
              ↓
            DRAFT
              ↓
      READY_FOR_REVIEW
              ↓
          APPROVED
```

A aprovação representa somente revisão humana da base da candidatura. Ela não envia candidatura e não habilita automação externa.

## 2. Princípios

### 2.1 Um draft por candidato e vaga

Existe uma restrição única em:

```text
(profile_id, job_id)
```

Preparar novamente a mesma vaga enquanto o draft está em `DRAFT` atualiza o snapshot existente em vez de criar outro registro.

### 2.2 Snapshot da verdade usada

O draft preserva as evidências usadas naquele momento.

Isso permite responder posteriormente:

- quais fatos sustentaram a candidatura;
- qual versão do Match foi usada;
- quais gaps estavam explícitos;
- quais requisitos ainda estavam `UNKNOWN`;
- quando a base foi aprovada.

Uma mudança posterior no Candidate Core não altera retroativamente um snapshot já congelado para revisão.

### 2.3 Provenance é obrigatória

O snapshot de evidências inclui somente evidências ligadas a requisitos `MATCHED` cuja origem seja:

```text
USER_CONFIRMED
```

Itens `AI_DRAFT`, `SYSTEM_INFERRED`, `RESUME_EXTRACTED` ou `ATS_IMPORTED` não são promovidos implicitamente a verdade de candidatura.

### 2.4 UNKNOWN continua UNKNOWN

Requisitos sem comprovação permanecem no `unknown_snapshot`.

Eles não podem virar experiência, skill ou resultado apenas porque são relevantes para a vaga.

## 3. Modelo persistido

### ApplicationDraft

```text
id
profile_id
job_id
status
brief_text
evidence_snapshot
gap_snapshot
unknown_snapshot
match_snapshot
created_at
updated_at
approved_at
```

O `match_snapshot` registra:

```text
algorithm_version = v1.14
score
confidence
band
ranking_score
```

### ApplicationEvent

Eventos append-only registram mudanças significativas:

```text
DRAFT_CREATED
DRAFT_REFRESHED
READY_FOR_REVIEW
APPROVED
```

O evento de transição registra estado anterior e novo estado.

## 4. Máquina de estados

### DRAFT

Permite:

- revisar a base;
- atualizar o snapshot com Candidate Core + Match atuais;
- avançar para `READY_FOR_REVIEW`.

Não permite aprovação direta.

### READY_FOR_REVIEW

O snapshot fica congelado para revisão humana.

Permite:

- visualizar o conteúdo;
- aprovar a base.

Não permite refresh do snapshot.

### APPROVED

Registra a aprovação humana e `approved_at`.

Não significa:

- candidatura submetida;
- currículo enviado;
- formulário preenchido;
- automação autorizada.

## 5. API

```text
GET  /api/v1/applications
GET  /api/v1/applications/jobs/{job_id}
PUT  /api/v1/applications/jobs/{job_id}

POST /api/v1/applications/{application_id}/ready-for-review
POST /api/v1/applications/{application_id}/approve
```

O `PUT` é idempotente por perfil + vaga enquanto o estado for `DRAFT`.

Transições inválidas retornam conflito e não alteram o estado.

## 6. Application Studio

A rota `/applications` passa a consumir o draft persistido.

A tela diferencia explicitamente:

- **snapshot salvo** — evidências usadas na preparação;
- **Candidate Core atual** — fatos confirmados disponíveis hoje.

Enquanto `DRAFT`, o usuário pode atualizar o snapshot.

Em `READY_FOR_REVIEW`, a interface apresenta a aprovação como uma decisão humana explícita.

Em `APPROVED`, a interface informa que a revisão foi registrada e que nenhuma candidatura foi enviada externamente.

## 7. Testes obrigatórios

A slice cobre:

- idempotência do draft;
- exclusão de evidência não confirmada;
- persistência de `UNKNOWN`;
- criação e refresh de eventos;
- bloqueio de aprovação direta;
- bloqueio de refresh depois de `READY_FOR_REVIEW`;
- aprovação somente depois da revisão;
- 404 para perfil ou vaga inexistente;
- migration real em PostgreSQL;
- contrato OpenAPI gerado;
- build Svelte;
- smoke E2E do piloto.

## 8. Próxima slice — Resume Tailoring v1

A próxima etapa não deve começar escolhendo um provider por preferência.

Ela deve criar primeiro:

1. um contrato de `ResumeTailoringInput` baseado no `ApplicationDraft` aprovado;
2. uma representação estruturada do currículo-base;
3. saída estruturada com alterações rastreáveis;
4. diff entre base e versão direcionada;
5. eval de fidelidade factual e utilidade;
6. comparação de modelos/providers conforme ADR-0006;
7. revisão humana da versão gerada.

O rewriter poderá:

- reorganizar;
- resumir;
- destacar;
- adaptar vocabulário.

Ele não poderá:

- criar experiência;
- inventar métricas;
- aumentar senioridade;
- converter `UNKNOWN` em fato;
- usar evidência fora do snapshot aprovado.

Até que o gate do Resume Tailoring seja aprovado:

```text
AUTO SUBMIT = OFF
```
