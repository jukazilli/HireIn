# Match v1.4 — Structured Evidence & Uncertainty

## Objetivo

O Blind Holdout #2 mostrou falsos negativos importantes no Match v1.3. Em vários casos, a ausência de uma evidência exata no perfil era tratada como `GAP`, mesmo sem existir prova de que o candidato não possuía aquela competência.

A v1.4 corrige a interpretação dos requisitos sem recalibrar os pesos.

## Estados

- `MATCHED`: existe evidência confirmada suficiente.
- `GAP`: existe evidência confirmada de que um mínimo explícito não foi atendido.
- `UNKNOWN`: os dados atuais não permitem concluir.

Ausência no perfil não é automaticamente evidência negativa.

## Pesos preservados

- `REQUIRED`: peso 3.
- `PREFERRED`: peso 1.
- requisitos profissionais: 85% do score combinado.
- preferências: 15% quando possuem cobertura suficiente.
- blocker geográfico continua ativo.
- proficiência de idioma da v1.3 continua ativa.

## Requisitos compostos

### ANY_OF

Alternativas explícitas podem ser satisfeitas por uma opção confirmada.

Exemplo: `Jira, Trello, Zendesk ou Redmine`.

Se `Zendesk` estiver confirmado, o requisito pode ser `MATCHED`.

### ALL_OF

Requisitos curtos unidos por `e`, em skills e ferramentas, são avaliados por componente.

Exemplo: `Scrum e Kanban`.

Se apenas Scrum estiver comprovado, o resultado é `UNKNOWN`, e não `GAP`.

## Formação acadêmica

A v1.4 reconhece cursos explicitamente citados dentro de frases maiores.

Exemplo: `Formação superior em Computação, Engenharia de Software, ADS ou áreas correlatas` pode ser atendido por uma formação confirmada em `Engenharia de Software`.

A condição `Ensino superior completo ou cursando` aceita `COMPLETED` e `IN_PROGRESS`. Quando a vaga exige explicitamente formação concluída e a formação confirmada ainda está em andamento, o resultado permanece `GAP`.

## Experiência profissional

A evidência de experiência não depende apenas do título do cargo. A v1.4 também consulta a descrição profissional confirmada e fatos confirmados de responsabilidade, projeto e realização.

Assim, uma exigência como `Sustentação ou suporte de sistemas ERP` pode ser sustentada por uma descrição confirmada que mencione sustentação de ERP, mesmo que o título do cargo seja diferente.

## Incerteza, score e cobertura

Um `GAP` sem evidência negativa é convertido para `UNKNOWN` nos tipos baseados em evidência profissional.

`UNKNOWN` não gera pontos positivos. Ele continua participando do denominador do score com o peso original do requisito, evitando que informação ausente aumente artificialmente o Match.

A cobertura permanece conservadora: apenas `MATCHED` e `GAP` contam como requisitos efetivamente avaliados. `UNKNOWN` reduz a cobertura. Se a cobertura ficar abaixo de 60%, a vaga permanece `INSUFFICIENT_DATA` e não recebe score numérico.

Isso evita dois erros:

1. declarar uma lacuna sem evidência;
2. premiar um perfil incompleto.

## Professional Match e Apply Intent

O Holdout #2 também mostrou que compatibilidade profissional e vontade de se candidatar são sinais diferentes.

Nos próximos experimentos, devem ser avaliados separadamente:

- `professional_fit`: compatibilidade sustentada pelas evidências profissionais;
- `apply_intent`: interesse do usuário em tentar a oportunidade, inclusive quando ela é aspiracional ou representa transição de carreira.

## Perfil progressivo

Quando um requisito ficar `UNKNOWN`, o produto poderá futuramente pedir confirmação ao usuário. A competência só poderá virar evidência após confirmação explícita; o Match não deve completar o perfil por inferência livre.

## Critérios de aceite

- pesos continuam congelados;
- blocker geográfico e proficiência de idioma continuam funcionando;
- `ANY_OF` reconhece uma alternativa confirmada;
- `ALL_OF` não é atendido por apenas um componente;
- cursos explicitamente aceitos são reconhecidos dentro de frases maiores;
- `completo ou cursando` aceita formação em andamento;
- formação concluída obrigatória preserva gap quando aplicável;
- descrição de experiência pode sustentar requisito;
- ausência sem contraponto vira `UNKNOWN`, não `GAP`;
- `UNKNOWN` não gera pontos e reduz cobertura;
- cobertura abaixo de 60% continua sem score numérico;
- produto e relatório de avaliação usam o mesmo matcher canônico.

## Validação

As 10 vagas do Blind Holdout #2 agora são dados de desenvolvimento e podem ser usadas para regressão da v1.4. Elas não podem ser reutilizadas como novo holdout cego.

Depois da estabilização, o Blind Holdout #3 deve usar vagas reais e inéditas, com `professional_fit` e `apply_intent` coletados separadamente.
