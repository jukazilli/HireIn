# Match v1.10 — Atomic Evidence Resolution

## Contexto

O Blind Holdout com cinco vagas inéditas confirmou dois sinais importantes:

1. o ranking relativo do Match v1.9 acompanhou a ordenação humana;
2. o Evidence Resolver ainda podia aprender conceitos compostos de forma ampla demais.

Exemplo observado:

```text
Requisito:
Bizagi, Visio ou Miro

Resposta:
Tenho
```

No v1.9, o Candidate Core podia armazenar o requisito composto inteiro. Isso é melhor do que texto livre, mas ainda não diz qual ferramenta o usuário realmente domina.

## Objetivo

Transformar confirmações compostas em evidências atômicas e reutilizáveis sem adicionar LLM, embeddings ou inferência automática.

## Escopo seguro

A decomposição automática v1.10 é deliberadamente conservadora e se aplica somente a:

- `SKILL`;
- `TOOL`.

Requisitos narrativos de `EXPERIENCE`, `DOMAIN` e `RESPONSIBILITY` continuam sendo tratados como conceitos inteiros porque quebrá-los automaticamente pode destruir contexto profissional.

## Operadores

### ANY

Exemplo:

```text
Bizagi, Visio ou Miro
```

O resolver apresenta:

```text
[ Bizagi ] [ Visio ] [ Miro ]
```

Um ou mais itens selecionados atendem o requisito.

Se o usuário selecionar apenas `Miro`, o Candidate Core aprende somente:

```text
Miro
```

Não aprende Bizagi nem Visio.

### ALL

Exemplo:

```text
Excel e PowerPoint
```

O resolver também apresenta cada item separadamente.

Se o usuário selecionar os dois:

```text
CONFIRMED
```

Se selecionar apenas Excel:

```text
PARTIAL
```

Nesse caso:

- o requisito composto fica como GAP;
- `Excel` é preservado como evidência positiva reutilizável;
- `PowerPoint` não é inventado nem inferido.

## Decisões humanas

O fluxo visível continua simples:

- **Tenho**
- **Não tenho**
- **Não sei**

Ao clicar em **Tenho** em um requisito composto, o usuário escolhe exatamente os itens verdadeiros.

Internamente, o v1.10 passa a suportar:

- `CONFIRMED`;
- `PARTIAL`;
- `NOT_HAVE`;
- `UNSURE`.

`PARTIAL` é resultado de uma seleção incompleta em requisito do tipo ALL.

## Candidate Core

Fatos atômicos continuam:

- `source_type = USER_CONFIRMED`;
- confiança 1.000;
- auditáveis por `source_ref = evidence-gap:<resolution>:atom:<n>`.

Exemplo:

```text
Vaga A:
Bizagi, Visio ou Miro

Usuário:
Miro

Candidate Core:
Miro
  source_type = USER_CONFIRMED
  source_ref = evidence-gap:<id>:atom:0
```

Uma vaga futura que pedir apenas Miro pode reutilizar essa evidência.

Uma vaga futura que pedir Bizagi não pode reutilizá-la.

## Migração de confirmações antigas

As confirmações compostas coletadas antes do v1.10 não são quebradas automaticamente.

Não sabemos qual alternativa o usuário quis confirmar originalmente.

Por isso a migração `0010_atomic_evidence`:

1. preserva a resolução humana original;
2. remove do Candidate Core apenas os fatos globais ambíguos de SKILL/TOOL compostos;
3. não inventa átomos;
4. permite que esses itens sejam confirmados novamente de forma atômica quando reaparecerem.

É uma migração conservadora: prefere perguntar outra vez a transformar uma confirmação ambígua em conhecimento falso.

## O que não muda

- pesos do Match não são recalibrados neste ciclo;
- Professional Fit continua separado de Opportunity Compatibility;
- Apply Intent continua pertencendo ao usuário;
- requisitos com anos, nível, idioma, formação ou contexto estruturado não passam pelo resolver simples;
- ausência de evidência não vira GAP automaticamente;
- nenhuma LLM ou embedding é adicionada.

## Por que ainda não usar embeddings

O erro medido neste ciclo não foi principalmente equivalência semântica profunda.

Foi granularidade da evidência.

Adicionar embeddings antes de corrigir a granularidade faria o matcher comparar representações ainda ambíguas com mais sofisticação, sem resolver a fonte do problema.

## Próximo experimento

Depois do deploy do v1.10, o próximo lote deve usar cinco vagas inéditas.

Para cada vaga:

```text
1. usuário avalia Professional Fit + Apply Intent
2. Match inicial é revelado
3. UNKNOWNs são resolvidos
4. Match enriquecido é recalculado
5. comparar:
   humano
   × Match inicial
   × Match enriquecido
```

As métricas principais serão:

- ordenação das cinco vagas;
- diferença entre Fit humano e score;
- cobertura antes/depois;
- quantidade de UNKNOWNs;
- quantidade de perguntas repetidas evitadas;
- falsos MATCHED;
- falsos GAP;
- casos reais de equivalência semântica ainda não reconhecida.

## Gate para v1.11

Só recalibrar pesos ou introduzir embeddings/LLM se o próximo holdout mostrar erro recorrente mensurável.

Em particular:

- score alto em vagas humanamente fracas pode justificar estudo de requisito central / role anchor;
- aliases simples podem justificar taxonomia determinística;
- equivalências semânticas reais e repetidas podem justificar benchmark de embeddings;
- perguntas redundantes podem justificar reutilização de evidência negativa mais granular.
