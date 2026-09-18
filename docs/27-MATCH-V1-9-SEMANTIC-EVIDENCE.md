# Match v1.9 — Semantic Evidence Persistence

## Contexto

O ciclo manual do Match v1.8 mostrou um padrão importante: muitos `UNKNOWN` eram ausência de evidência no Candidate Core, não ausência real de experiência.

O v1.8 também revelou uma falha de persistência: ao confirmar um requisito, o Candidate Core armazenava o texto livre digitado pelo usuário. Exemplo:

- requisito: `Faturamento`
- resposta livre: `eu já implantei esse módulo`
- fato persistido: `eu já implantei esse módulo`

Esse fato é auditável, mas é semanticamente fraco para reutilização em vagas futuras.

## Decisão v1.9

O resolver passa a ser uma confirmação estruturada:

- **Tenho**
- **Não tenho**
- **Não sei**

Não há campo aberto obrigatório.

Quando o usuário escolhe **Tenho**, o HireIn persiste como conhecimento reutilizável o próprio conceito normalizado da vaga:

- requisito: `Faturamento`
- decisão: `CONFIRMED`
- Candidate Core: `Faturamento`
- origem: `USER_CONFIRMED`
- source ref: resolução que originou o conhecimento

O texto livre legado continua preservado na tabela de resoluções para auditoria, mas deixa de ser a chave semântica do matcher.

## Por que não usar LLM ou embeddings agora

O requisito da própria vaga já fornece o primeiro conceito canônico necessário para este ciclo. Portanto, a v1.9 é determinística e auditável.

LLM/embeddings só devem entrar caso o próximo holdout mostre falhas mensuráveis de equivalência semântica, por exemplo:

`Faturamento` ↔ `módulo de faturamento TOTVS Protheus`

Até existir esse erro medido, adicionar uma camada semântica probabilística aumentaria custo e complexidade sem evidência de necessidade.

## Reutilização entre vagas

Um conceito confirmado em uma vaga passa a participar das análises futuras. Para `SKILL`, o Candidate Core usa um fato semântico gerenciado pelo resolver e o matcher só aceita esse caminho quando:

1. a evidência é `USER_CONFIRMED`;
2. o fato veio de `evidence-gap:`;
3. o conceito da nova vaga possui correspondência literal segura.

Isso evita transformar qualquer texto genérico do perfil em skill.

## Regras preservadas

- pesos do Match não mudam;
- Professional Fit continua separado de Opportunity Compatibility;
- `NOT_HAVE` continua produzindo GAP somente para o requisito respondido;
- `UNSURE` continua UNKNOWN;
- requisitos com qualificadores estruturados (anos, nível, idioma, formação ou contexto) não podem ser resolvidos por uma confirmação simples;
- uma resolução humana não substitui MATCHED/GAP objetivo já existente.

## Backfill

A migração `0009_semantic_evidence` normaliza fatos criados pelo v1.8 usando o `job_requirement.value` original. Assim, as confirmações já coletadas no piloto não são perdidas.

## Próximo gate

Depois do deploy:

1. confirmar que as respostas já coletadas foram normalizadas;
2. verificar que uma nova vaga reutiliza conhecimento sem perguntar novamente;
3. iniciar um novo lote cego de vagas;
4. medir principalmente:
   - redução de UNKNOWN repetido;
   - falsos MATCHED;
   - falsos GAP;
   - equivalências semânticas ainda não reconhecidas.

Somente os erros observados nesse novo holdout devem orientar v1.10, embeddings ou LLM.
