# Job Normalization v1.1

## Objetivo

Preservar qualificadores explícitos do anúncio antes de evoluir o Match com embeddings ou LLM. A normalização não pode transformar requisitos mais fortes em requisitos genéricos.

Exemplos que precisam permanecer diferentes:

- `Excel` != `Excel avançado`;
- `Gestão de projetos` != `Gestão de projetos de alta complexidade`;
- `Graduação cursando` != `Graduação completa`;
- `ERP` != domínio específico `TMS` ou `WMS`.

## Campos estruturados

Cada `JobRequirement` passa a poder registrar:

- `required_level`: nível mínimo explícito (`BEGINNER`, `INTERMEDIATE`, `ADVANCED`, `EXPERT`) para `SKILL`/`TOOL`;
- `required_education_status`: status educacional explícito, como `COMPLETED`;
- `context_qualifier`: escopo textual relevante que não deve ser descartado, por exemplo `alta complexidade`.

Os campos são opcionais para preservar compatibilidade com o Job Core existente.

## Backfill seguro do piloto

A migration `0005_job_requirement_qualifiers` só estrutura qualificadores que já estão literalmente presentes em `source_text`:

- `avançado/avançada` -> `required_level=ADVANCED`;
- `intermediário/intermediária` -> `required_level=INTERMEDIATE`;
- `graduação completa`, `superior completo`, `ensino superior completo` -> `required_education_status=COMPLETED`;
- `alta complexidade` -> `context_qualifier=alta complexidade`.

Não existe inferência sem evidência do anúncio.

## Match

O Match v1.1 continua auditável e conservador:

1. primeiro encontra a competência-base;
2. depois valida os qualificadores estruturados;
3. se a competência existe mas o nível do candidato não foi confirmado, retorna `UNKNOWN`, não `MATCHED`;
4. se a vaga exige graduação completa e o candidato só possui graduação em andamento confirmada, retorna `GAP`;
5. se existe um qualificador de contexto sem evidência confirmada no perfil, retorna `UNKNOWN`;
6. domínio específico continua representado por requisito `DOMAIN` separado.

Isso reduz falsos positivos sem inventar falsos negativos.

## Gate do piloto

Depois do deploy:

1. manter as 10 avaliações humanas como ground truth;
2. recalcular as mesmas vagas;
3. verificar especialmente WMS, TMS e vagas com formação completa;
4. medir ranking e cobertura novamente;
5. só então buscar 10 vagas novas como conjunto de validação fora da amostra usada para calibração.
