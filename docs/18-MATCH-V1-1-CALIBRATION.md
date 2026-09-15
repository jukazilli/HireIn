# HireIn Match v1.1 — calibração do piloto

## Objetivo

A versão v1.1 nasce das primeiras 10 avaliações humanas do piloto privado. O objetivo não é tornar o motor "mais inteligente" de forma genérica, e sim corrigir erros observados com evidência real antes de introduzir embeddings ou LLM no ranking.

O Match v0 permanece no repositório como baseline auditável. A rota produtiva passa a usar uma camada `service_v11.py`, permitindo comparar comportamento antes/depois sem apagar o histórico.

## Evidências do primeiro ciclo

O piloto mostrou quatro padrões principais:

1. **Perfil incompleto reduz score mesmo quando a vaga é plausível.** Durante a revisão humana foram confirmadas experiências/skills que não estavam estruturadas no perfil, como implantação de sistemas SaaS, onboarding, Excel, cronogramas e planejamento de projetos.
2. **Localização pode ser um blocker real.** Vagas presenciais ou híbridas fora das localidades desejadas não devem permanecer relevantes quando o candidato declara que não aceita mudança.
3. **Preferências esparsas não podem produzir 100%.** Um único aspecto alinhado não é evidência suficiente para atribuir `preference_score=100`.
4. **Algumas equivalências são seguras sem IA.** Exemplos: `Scrum` satisfaz um requisito genérico de `Metodologias ágeis`; ClickUp/Monday.com podem satisfazer um requisito genérico de `Ferramentas de gestão de projetos`.

## Regras da v1.1

### 1. Proveniência continua obrigatória

Somente dados `USER_CONFIRMED` podem aumentar o score. A calibração não autoriza inferir experiência profissional a partir de texto gerado por IA.

### 2. Normalização ortográfica segura

Antes de declarar GAP, a v1.1 tenta equivalência removendo apenas diferenças que não alteram significado:

- caixa;
- acentos;
- hífens;
- pontuação;
- espaços repetidos.

Isso cobre variações como `Go-Live` vs `Go Live` sem usar modelo semântico.

### 3. Alias genérico pequeno e auditável

A v1.1 possui uma tabela explícita de equivalências dirigidas. Ela é intencionalmente pequena e deve crescer apenas a partir de casos revisados.

Inicialmente:

- `Metodologias ágeis` aceita evidência confirmada de `Scrum` ou `Kanban`;
- `Ferramentas de gestão de projetos` aceita `ClickUp`, `Monday.com`, `MS Project` ou `Microsoft Project`.

Essas regras não são sinônimos universais; são relações de satisfação de um requisito genérico por uma evidência específica.

### 4. Anos mínimos continuam conservadores

Uma equivalência textual/semântica não ignora `min_years`. Se a skill equivalente existe mas o perfil não possui quantidade confirmada, o resultado permanece `UNKNOWN` para esse requisito.

### 5. Regra de localização

A localização passa a distinguir `UNKNOWN` de conflito real.

Quando:

- a vaga exige presença (híbrida ou presencial; ou possui cidade específica sem indicação de remoto),
- a localização não corresponde às localidades desejadas,
- e `willing_to_relocate=false`,

então `LOCATION=CONFLICT` e o Match final recebe o warning `location_preference_blocker`.

Neste caso:

- `requirement_score` continua preservado para explicar aderência técnica;
- `score` final é `0`;
- `band=LOW`;
- a interface pode explicar que a oportunidade foi descartada por preferência, não por falta de capacidade técnica.

Vagas explicitamente remotas não recebem esse blocker.

### 6. Cobertura mínima das preferências

O `preference_score` só participa do score final quando pelo menos 50% dos seis aspectos de preferência são avaliáveis:

- título;
- localização;
- modelo de trabalho;
- tipo de contrato;
- senioridade;
- salário.

Abaixo desse limite, `preference_score=null` e o score técnico não é artificialmente alterado por uma única preferência conhecida.

### 7. Score continua explicável

Quando não há blocker de localização:

- requisitos continuam com peso `REQUIRED=3`, `PREFERRED=1`, `INFO=0`;
- cobertura mínima de requisitos continua em 60%;
- se as preferências atingirem cobertura mínima, combinação permanece 85% requisitos + 15% preferências;
- se preferências forem insuficientes, o score final usa apenas requisitos.

## Dados confirmados no piloto após as 10 revisões

O perfil privado foi enriquecido apenas com informações explicitamente confirmadas pelo candidato durante as avaliações:

- Implantação de sistemas SaaS;
- Onboarding;
- Excel;
- Cronogramas;
- Planejamento de projetos;
- `willing_to_relocate=false`;
- localidades-alvo: Joinville/SC, Santa Catarina e Remoto - Brasil.

Nenhum nível, senioridade ou quantidade de anos foi inventado.

## O que a v1.1 deliberadamente não faz

- embeddings;
- LLM como juiz de Match;
- inferência automática de anos de experiência;
- expansão ampla de sinônimos;
- preencher gaps do perfil sem confirmação humana;
- converter preferência em requisito técnico.

## Critério de sucesso

Após deploy, as mesmas 10 vagas do primeiro ciclo devem ser recalculadas. O objetivo é verificar:

1. aumento de score em vagas que o humano marcou como boas por falta de evidência estruturada;
2. descarte correto das vagas fora da localização aceita;
3. eliminação do `preference_score=100` com cobertura mínima insuficiente;
4. preservação das vagas realmente fracas em posições baixas.

Depois disso, um novo conjunto de vagas deve ser usado como validação fora da amostra de calibração para evitar overfitting do piloto.
