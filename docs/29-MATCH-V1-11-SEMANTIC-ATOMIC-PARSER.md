# Match v1.11 — Semantic Atomic Requirement Parser

## Evidência que motivou a mudança

O experimento controlado com a vaga **Bild — Analista de Projetos** mostrou que o Match v1.10 reduziu corretamente cinco UNKNOWNs e levou a cobertura de 38% para 100%.

Ao mesmo tempo, o Candidate Core aprendeu átomos semanticamente fracos:

- `Levantamento e documentação de requisitos` virou:
  - `Levantamento`
  - `documentação de requisitos`
- `Comunicação verbal e escrita` virou:
  - `Comunicação verbal`
  - `escrita`

O problema não estava na confirmação humana, mas na perda de contexto linguístico ao dividir a frase.

## Objetivo

Preservar o contexto compartilhado quando um requisito composto é transformado em evidências atômicas.

O v1.11 continua determinístico e auditável. Não adiciona LLM, embeddings ou inferência probabilística.

## Exemplos

### Complemento compartilhado

```text
Levantamento e documentação de requisitos
```

Passa a produzir:

```text
Levantamento de requisitos
Documentação de requisitos
```

Outro exemplo:

```text
Gestão e planejamento de projetos
```

Produz:

```text
Gestão de projetos
Planejamento de projetos
```

### Prefixo compartilhado

```text
Comunicação verbal e escrita
```

Produz:

```text
Comunicação verbal
Comunicação escrita
```

Também:

```text
Testes funcionais, unitários e integrados
```

Produz:

```text
Testes funcionais
Testes unitários
Testes integrados
```

### Conceitos independentes permanecem independentes

```text
Organização e capacidade de aprendizado
```

Continua:

```text
Organização
Capacidade de aprendizado
```

```text
APIs e integrações de sistemas
```

Continua:

```text
APIs
Integrações de sistemas
```

```text
Scrum ou Kanban
```

Continua:

```text
Scrum
Kanban
```

## Parser conservador

A decomposição continua restrita a `SKILL` e `TOOL`.

Além disso, o v1.11 rejeita divisões que parecem frases narrativas em vez de uma lista de conceitos. Cada átomo precisa permanecer curto e reutilizável.

Exemplo que não deve ser atomizado automaticamente:

```text
Integrações via API com provedores de jogos e serviços terceirizados
```

Nesse caso, preservar a frase inteira é mais seguro do que transformar partes fora de contexto em fatos globais.

## Matching e Evidence Resolver usam a mesma semântica

O mesmo parser passa a ser reutilizado em dois pontos:

1. Evidence Resolver, para mostrar opções corretas ao usuário e persistir Candidate Facts;
2. matcher de requisitos compostos, para procurar evidência nos mesmos conceitos semânticos.

Isso elimina divergência entre o que a interface pergunta e o que o matcher considera um componente.

## Migração 0011

A migração `0011_semantic_atomic_parser` corrige fatos atômicos já gravados pelo v1.10 sem inventar novas respostas.

A ordem e cardinalidade dos itens são preservadas. Assim, escolhas antigas podem ser remapeadas pela posição original.

Exemplo:

```text
Antes:
confirmed_atoms = ["Comunicação verbal", "escrita"]

Depois:
confirmed_atoms = ["Comunicação verbal", "Comunicação escrita"]
```

E o `CandidateFact.value` correspondente também é atualizado.

Outro exemplo:

```text
Antes:
["Levantamento", "documentação de requisitos"]

Depois:
["Levantamento de requisitos", "documentação de requisitos"]
```

## O que não muda

- pesos do Professional Fit;
- Opportunity Compatibility;
- Apply Intent;
- regras de qualificadores estruturados;
- decisão humana CONFIRMED / PARTIAL / NOT_HAVE / UNSURE;
- origem `USER_CONFIRMED`;
- confiança 1.000 para evidência explicitamente confirmada;
- política de não transformar ausência de evidência em GAP.

## Próximo gate

Depois do deploy:

1. validar que os fatos da Bild foram reparados;
2. confirmar que o Match da Bild continua estável após a correção;
3. coletar um novo lote pequeno de vagas inéditas;
4. medir:
   - UNKNOWNs evitados automaticamente;
   - necessidade de cards;
   - falsos MATCHED;
   - qualidade dos conceitos persistidos;
   - repetição de perguntas;
   - novos casos reais de equivalência semântica.

LLM ou embeddings só entram se esse novo lote mostrar equivalências semanticamente corretas que regras determinísticas não consigam cobrir de forma segura.
