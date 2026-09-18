# Match v1.7 — Evidence Recovery

## Status

Implementação proposta após o Match v1.6 revelar baixa confiança média no Blind Holdout #4.

## Objetivo

Aumentar a cobertura de evidência do Professional Fit usando somente informações já confirmadas no Candidate Core.

O v1.7 **não** altera:

- pesos REQUIRED/PREFERRED;
- limiar de confiança de 60%;
- separação Professional Fit / Opportunity Compatibility / Apply Intent;
- significado de GAP;
- regra de que ausência de evidência não é prova de lacuna;
- ranking de recomendação final.

## Problema observado

O Holdout #4 terminou com confiança média de aproximadamente 15,8%.

Exemplos:

- formação em Engenharia de Software não era reconhecida quando a vaga aceitava genericamente "Engenharia";
- experiência de implantação + gestão de projetos não era combinada quando a vaga pedia "metodologias de implantação de projetos";
- requisitos compostos perdiam evidências parciais em listas com vírgulas;
- interface explícita entre clientes, negócio e equipes técnicas não era usada para requisitos de articulação com stakeholders.

Esses casos reduziam a confiança mesmo quando existia evidência auditável no Candidate Core.

## Estratégia

### 1. Formação genérica em Engenharia

Somente uma opção explicitamente genérica como:

```text
Administração, Engenharia ou áreas afins
```

pode ser atendida por um curso confirmado cuja família começa por `Engenharia ...`.

Uma exigência específica como `Engenharia Civil` **não** é satisfeita por `Engenharia de Software`.

O status de formação continua respeitado.

### 2. Metodologia de implantação de projetos

Quando o requisito contém simultaneamente:

- metodologia/método;
- implantação/implementação;
- projeto;

o matcher pode combinar duas famílias independentes de evidência:

```text
evidência de implantação
+
evidência de gestão/planejamento de projetos
```

A regra continua respeitando `min_years`, nível e demais qualificadores estruturados.

### 3. Stakeholders

Requisitos de comunicação/articulação/interação com stakeholders só recebem bridge quando o Candidate Core possui evidência textual explícita de interface/interação com partes interessadas.

Exemplo válido:

```text
interface entre clientes, negócio e equipes técnicas
```

Se o requisito também pedir levantamento de requisitos, ambas as famílias de evidência precisam existir.

### 4. Requisitos compostos

Listas AND como:

```text
Treinamentos, testes funcionais, unitários e integrados
```

passam a ser decompostas em componentes auditáveis.

- todos comprovados -> MATCHED;
- apenas parte comprovada -> UNKNOWN com as evidências parciais preservadas;
- nenhum comprovado -> mantém o baseline.

O matcher não transforma evidência parcial em MATCHED.

### 5. Mapeamento/desenho/modelagem de processos

Os termos são tratados como uma família conceitual segura para evidência parcial ou completa dentro de requisitos compostos.

Isso não prova automaticamente documentação, BPMN ou qualquer ferramenta específica.

## Guardrails

1. nenhuma ponte pode ignorar `min_years`;
2. nenhuma ponte pode ignorar `required_level`;
3. curso genérico de Engenharia não satisfaz especialidade específica;
4. requisito composto exige todos os componentes para MATCHED;
5. ausência continua sendo UNKNOWN, salvo contraprova confirmada;
6. nenhuma inferência de Apply Intent;
7. nenhum ajuste de pesos usando holdouts revelados.

## Critérios de aceite

- suíte v1.1–v1.6 permanece verde;
- novos testes v1.7 cobrem as quatro famílias acima;
- contrato OpenAPI permanece compatível;
- E2E do piloto continua verde;
- a UI identifica a versão como v1.7;
- a regressão do Holdout #4 pode ser usada apenas para diagnóstico, nunca como validação cega.

## Próximo gate

Depois de publicar o v1.7:

1. rodar regressão técnica sobre os holdouts já revelados;
2. verificar se a confiança aumenta principalmente onde há evidência profissional real;
3. confirmar que nenhum requisito composto virou falso MATCHED;
4. só então decidir entre um novo blind holdout pequeno ou iniciar o Search Profile v0.
