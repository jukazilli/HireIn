# Match v1.4 — Structured Evidence & Uncertainty

## Contexto

O `Match v1.3 — Blind Holdout #2` mostrou que o matcher estava conservador de uma forma indesejada: ele não superestimava vagas claramente inadequadas, mas tratava ausência de evidência exata no perfil como se fosse evidência negativa.

O problema principal estava antes do peso final do score. Por isso, a v1.4 mantém os pesos existentes e altera a interpretação dos requisitos e das evidências.

## Princípio central

A v1.4 distingue três situações:

- `MATCHED`: existe evidência confirmada suficiente;
- `GAP`: existe evidência confirmada que contradiz um mínimo explícito da vaga;
- `UNKNOWN`: o perfil atual não possui evidência suficiente para concluir.

A ausência de uma skill, ferramenta, domínio, experiência ou formação no perfil não é automaticamente tratada como prova de que o candidato não possui aquela competência.

## O que permanece igual

A v1.4 não altera os pesos do Match:

- requisito `REQUIRED`: peso 3;
- requisito `PREFERRED`: peso 1;
- preferências profissionais continuam com peso de 15% quando possuem cobertura suficiente;
- requisitos profissionais continuam com peso de 85% no score combinado;
- blocker real de localização continua zerando o Match;
- comparação explícita de proficiência de idioma da v1.3 continua ativa.

## Requisitos compostos

### ANY_OF

Listas explicitamente alternativas passam a ser tratadas como `ANY_OF`.

Exemplo:

```text
Jira, Trello, Zendesk ou Redmine
```

Se uma das alternativas possuir evidência confirmada, o requisito pode ser considerado atendido.

Outro exemplo:

```text
SaaS B2B, MDM, ERP ou CRM
```

A v1.4 pode validar uma alternativa literal confirmada sem exigir que a string inteira exista no perfil.

### ALL_OF

Requisitos curtos ligados explicitamente por `e`, em categorias de skill ou ferramenta, podem ser tratados como componentes obrigatórios.

Exemplo:

```text
Scrum e Kanban
```

Se somente Scrum estiver confirmado, o resultado é `UNKNOWN`, e não `GAP`: uma parte foi comprovada, mas ainda falta evidência sobre a outra.

## Formação acadêmica

A v1.4 passa a reconhecer cursos explicitamente listados dentro de uma exigência maior.

Exemplo:

```text
Formação superior em Computação, Engenharia de Software, ADS ou áreas correlatas
```

Um perfil com `Engenharia de Software` pode satisfazer o requisito mesmo que a string completa da vaga não coincida com o nome do curso.

Expressões como:

```text
Ensino superior completo ou cursando
```

aceitam formações confirmadas com status `COMPLETED` ou `IN_PROGRESS`.

Quando a vaga exige explicitamente `COMPLETED` e a formação confirmada está `IN_PROGRESS`, continua existindo um `GAP` real.

## Evidência em experiências

A experiência deixa de depender apenas do título literal do cargo.

A v1.4 também pode usar:

- descrição da experiência confirmada;
- responsabilidades confirmadas;
- projetos e realizações confirmados.

Exemplo:

```text
Vaga: Sustentação ou suporte de sistemas ERP
Perfil: atuação em implantação e sustentação do TOTVS Protheus
```

A palavra `sustentação` na descrição confirmada pode sustentar o requisito sem exigir que o cargo do candidato tenha exatamente o mesmo nome da exigência da vaga.

## Ausência de evidência

Na v1.3, diversos matchers retornavam `GAP` quando existia um conjunto de skills confirmado, mas a skill específica da vaga não estava presente.

Na v1.4, um `GAP` sem evidência negativa é convertido para `UNKNOWN` nos tipos baseados em evidência profissional.

Um `GAP` é preservado quando existe evidência concreta, por exemplo:

- idioma confirmado abaixo do nível mínimo;
- formação confirmada ainda em andamento quando a vaga exige conclusão;
- experiência encontrada, mas com duração inferior ao mínimo explícito;
- blocker de localização.

## Cobertura e risco não resolvido

Requisitos obrigatórios em estado `UNKNOWN` continuam penalizando o score como risco não resolvido. Eles não geram pontos positivos.

Entretanto, passam a contar para a cobertura de decisão. Isso evita que uma vaga inteira fique sem score apenas porque parte dos requisitos obrigatórios ainda precisa de confirmação no perfil.

Requisitos preferenciais `UNKNOWN` continuam neutros.

A interpretação é:

```text
MATCHED obrigatório  -> evidência positiva
GAP obrigatório      -> evidência negativa
UNKNOWN obrigatório  -> risco não resolvido
UNKNOWN preferencial -> neutro
```

## Match profissional não é decisão de candidatura

O Holdout #2 também revelou uma distinção de produto importante.

O Match mede quanto conseguimos comprovar entre o perfil profissional e a vaga. Ele não deve tomar sozinho a decisão de candidatura.

Uma vaga pode ter Match parcial e ainda assim ser uma oportunidade de interesse do usuário, por exemplo por representar uma transição de carreira ou uma chance de desenvolver competências nos primeiros meses.

A arquitetura futura deve separar pelo menos dois sinais:

1. **Professional Match** — compatibilidade comprovada entre evidências e requisitos;
2. **Apply Intent / Opportunity Interest** — interesse do usuário em tentar aquela oportunidade, mesmo quando há gaps ou incertezas.

O próximo holdout deve evitar misturar esses conceitos em uma única label humana. A recomendação é coletar duas avaliações independentes por vaga:

- `professional_fit`;
- `apply_intent`.

Isso permitirá avaliar o matcher profissional sem penalizá-lo por não reproduzir uma decisão aspiracional do usuário.

## Perfil progressivo

Quando um requisito obrigatório estiver `UNKNOWN`, a UI poderá futuramente oferecer uma ação de confirmação:

```text
Não encontramos evidência suficiente de SQL no seu perfil.
Você possui experiência com SQL?
```

A resposta nunca deve ser inferida automaticamente.

Se o usuário confirmar, a informação pode ser incorporada ao perfil como `USER_CONFIRMED` e beneficiar avaliações futuras.

## Critérios de aceite da v1.4

- pesos de scoring permanecem congelados;
- idioma e blocker geográfico da v1.3 continuam funcionando;
- uma lista `A, B ou C` pode ser satisfeita por uma alternativa confirmada;
- `A e B` não é considerado atendido quando apenas um componente está comprovado;
- formação explicitamente listada é reconhecida dentro de frases maiores;
- `completo ou cursando` aceita formação em andamento;
- exigência explícita de formação concluída continua gerando gap quando o perfil está em andamento;
- descrições de experiências confirmadas podem sustentar requisitos de experiência;
- ausência de evidência sem contraponto confirmado vira `UNKNOWN`, não `GAP`;
- `UNKNOWN` obrigatório continua penalizando o score como risco;
- o matcher usado pelo relatório de avaliação é o mesmo matcher canônico usado pelo produto.

## Validação

As 10 vagas do Blind Holdout #2 agora são dados de desenvolvimento e podem ser usadas para testes de regressão da v1.4.

Elas não podem ser reutilizadas como holdout cego para validar generalização.

Depois da estabilização da v1.4, deve ser criado o `Blind Holdout #3` com vagas reais e inéditas. Nesse teste, além da relevância profissional, recomenda-se registrar separadamente a intenção de candidatura.
