# Match v1.8 — Human Evidence Resolution

## Status

Implementação do Evidence Gap Resolver após o Match v1.7 demonstrar que o principal gargalo restante é cobertura de evidência, não peso de scoring.

## Objetivo

Transformar UNKNOWNs relevantes em informação auditável com participação explícita do usuário, sem:

- inferir experiência;
- transformar ausência em gap;
- recalibrar pesos;
- sobrescrever evidência objetiva;
- misturar Professional Fit com Apply Intent.

## Princípio

O Match continua avaliando primeiro sozinho.

O resolver só pode atuar quando o **Match v1.7** termina com:

```text
status = UNKNOWN
```

Se o requisito já está `MATCHED` ou `GAP`, a decisão humana do resolver não pode sobrescrever o resultado.

## Decisões

### CONFIRMED

O usuário declara que possui a experiência/competência e precisa registrar uma evidência profissional concreta.

Exemplo:

```text
Organizei e priorizei de 30 a 50 demandas mensais,
acompanhando prazos e detalhes de implantação.
```

Efeitos:

1. cria/atualiza a resolução ligada ao requisito;
2. registra a descrição no Candidate Core como fato `USER_CONFIRMED`;
3. o requisito passa de `UNKNOWN` para `MATCHED`;
4. o Professional Fit é recalculado.

Um simples “sim” não é aceito.

### NOT_HAVE

O usuário declara explicitamente não possuir a experiência/competência para aquele requisito.

Efeito:

```text
UNKNOWN -> GAP
```

Esse gap é específico do requisito da vaga e não cria uma afirmação negativa global no Candidate Core.

### UNSURE

O usuário não consegue confirmar nem negar.

Efeito:

```text
UNKNOWN -> UNKNOWN
```

Não há ponto positivo e não há gap artificial.

## Requisitos elegíveis no v0

O fluxo humano aceita apenas requisitos sem qualificadores estruturados dos tipos:

- SKILL;
- TOOL;
- DOMAIN;
- EXPERIENCE;
- RESPONSIBILITY.

Não são resolvidos por texto livre:

- LANGUAGE;
- EDUCATION;
- CERTIFICATION;
- requisitos com `min_years`;
- requisitos com nível mínimo;
- requisitos com status de formação;
- requisitos com proficiência mínima;
- requisitos com `context_qualifier`;
- demais tipos não suportados.

Esses itens devem ser corrigidos no perfil estruturado.

## Persistência

Nova tabela:

```text
candidate_evidence_resolutions
```

Chave semântica:

```text
(profile_id, job_requirement_id)
```

Campos principais:

- decision;
- evidence_text;
- created_at;
- updated_at.

Decisões válidas:

```text
CONFIRMED
NOT_HAVE
UNSURE
```

Uma confirmação positiva também cria um `CandidateFact` com:

```text
source_type = USER_CONFIRMED
source_ref  = evidence-gap:<resolution_id>
confidence  = 1.000
```

Esses fatos são gerenciados pelo resolver e não aparecem no textarea manual do perfil para evitar duplicação acidental.

## API

### Listar lacunas

```http
GET /api/v1/jobs/{job_id}/evidence-gaps
```

Retorna:

- confiança atual;
- UNKNOWNs do baseline v1.7;
- UNKNOWNs resolvíveis;
- UNKNOWNs que exigem perfil estruturado;
- impacto estimado de cada item na cobertura;
- evidências parciais já encontradas;
- resolução humana existente, quando houver.

### Resolver lacuna

```http
PUT /api/v1/jobs/{job_id}/evidence-gaps/{requirement_id}
```

Exemplo:

```json
{
  "decision": "CONFIRMED",
  "evidence_text": "Conduzi treinamentos funcionais para usuários-chave em implantações."
}
```

## Scoring

O v1.8 mantém exatamente o scoring do v1.7.

A única mudança é o estado de requisitos originalmente UNKNOWN:

```text
CONFIRMED -> MATCHED
NOT_HAVE  -> GAP
UNSURE    -> UNKNOWN
```

Pesos continuam congelados.

## Guardrails

1. resolução humana não sobrescreve MATCHED;
2. resolução humana não sobrescreve GAP;
3. CONFIRMED exige descrição concreta;
4. requisito com qualificador estruturado não pode ser resolvido por texto livre;
5. NOT_HAVE é requisito-específico;
6. fatos positivos são USER_CONFIRMED e auditáveis;
7. resolver não infere Apply Intent;
8. resolver não é usado para recalibrar holdouts já revelados.

## UI

O Evidence Gap Resolver fica dentro da tela de Match.

Cada cartão mostra:

- requisito;
- obrigatoriedade;
- impacto máximo aproximado na cobertura;
- pergunta objetiva;
- evidência parcial existente;
- decisão humana atual.

A intenção é reduzir carga cognitiva: o usuário responde somente aos UNKNOWNs que podem realmente alterar a confiança.

## Validação

Critérios de aceite:

- migrations 0001–0008 aplicam em sequência;
- Match v1.1–v1.7 permanece verde;
- CONFIRMED aumenta cobertura somente no requisito resolvido;
- NOT_HAVE produz GAP explícito;
- UNSURE mantém UNKNOWN;
- perfil completo pode ser salvo sem apagar fatos gerenciados pelo resolver;
- OpenAPI e TypeScript permanecem sincronizados;
- E2E principal permanece verde.

## Próximo gate

Depois do deploy:

1. usar o resolver manualmente em poucas vagas já conhecidas;
2. observar quais categorias de UNKNOWN aparecem repetidamente;
3. promover evidências recorrentes para estruturas mais específicas apenas quando fizer sentido;
4. então iniciar novo blind holdout sem usar decisões coletadas a partir das vagas desse holdout antes da avaliação humana.
