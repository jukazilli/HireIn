# Match v1.5 — Fit separado de confiança

## Status

Implementação proposta a partir dos erros mensurados no Blind Holdout #3.

A v1.5 não recalibra pesos para fazer o benchmark parecer melhor. Ela corrige três problemas estruturais observados no v1.4:

1. ausência de evidência era confundida com posição ruim no ranking;
2. evidências profissionais confirmadas não eram recuperadas em alguns requisitos semanticamente próximos;
3. blocker de localização podia ser concluído sem modalidade presencial/híbrida explícita.

## 1. Fit e confiança são dimensões diferentes

`score` continua na escala 0–100, mas passa a representar aderência apenas entre os requisitos efetivamente avaliados.

`evaluation_coverage` representa a confiança/cobertura da leitura: quanto do peso relevante possui evidência suficiente para ser classificado como `MATCHED` ou `GAP`.

Exemplo:

```text
Aderência: 100
Confiança: 50
```

significa que toda a evidência que conseguimos avaliar foi favorável, mas metade da vaga ainda permanece incerta. Não significa 100% de chance de entrevista ou contratação.

Quando a confiança fica abaixo de 60%, a banda permanece `INSUFFICIENT_DATA`, mesmo que exista um score de aderência. Assim a interface não esconde o sinal disponível, mas também não finge precisão.

## 2. Ranking com incerteza neutra

O ranking não coloca mais automaticamente `score = null` abaixo de `score = 0`.

O sinal de ordenação reduz scores de baixa confiança em direção a um prior neutro de 50:

```text
ranking_signal = fit * confiança + 50 * (1 - confiança)
```

A confiança é usada na escala 0–1.

Um blocker algorítmico explícito continua prevalecendo e envia a vaga para o fim do ranking. A avaliação humana de blocker não influencia o algoritmo.

## 3. Pontes conceituais seguras

A v1.5 adiciona um conjunto pequeno, determinístico e auditável de conceitos profissionais para recuperar evidências já confirmadas no Candidate Core, incluindo:

- implantação / implementação / parametrização / onboarding;
- sistemas / ERP / SaaS / Protheus;
- treinamento / capacitação;
- levantamento e análise de requisitos;
- gestão / planejamento / acompanhamento de projetos.

Essas pontes não usam LLM nem embeddings.

### Guardrails

Uma ponte conceitual:

- não ignora `min_years`;
- não ignora nível mínimo estruturado;
- não ignora `context_qualifier`;
- não satisfaz sozinha um requisito composto `A e B` quando só uma parte foi comprovada;
- usa apenas evidência confirmada do perfil.

## 4. Formação

A ordem textual de alternativas deixa de importar. Expressões como:

```text
completo ou cursando
cursando ou completo
```

são tratadas de forma equivalente.

Engenharia de Software pode satisfazer uma família explicitamente tecnológica como `TI`, `Sistemas`, `Computação` ou `áreas correlatas de tecnologia`, desde que o status acadêmico também cumpra a exigência explícita.

Uma vaga que exige graduação concluída continua gerando `GAP` quando a formação confirmada está em andamento.

## 5. Localização

Blocker de localização só é criado quando existe evidência de presença obrigatória:

- `HYBRID`;
- `ONSITE`;
- ou texto inequívoco de híbrido/presencial sem indicação conflitante de remoto.

Cidade/estado conhecidos com modalidade desconhecida ficam como `UNKNOWN`, não como blocker.

Preferências em nível de estado também são reconhecidas. Exemplo: `Santa Catarina` é compatível com uma vaga presencial em Florianópolis/SC.

## 6. Validação

O Holdout #3 passa a ser conjunto de desenvolvimento/regressão. Ele não pode ser reutilizado como validação cega da v1.5.

Depois que a implementação estiver estável e o comportamento do Holdout #3 for analisado como regressão, a validação real da versão deverá usar um Blind Holdout #4 com vagas inéditas e avaliação humana feita antes da revelação do Match.
