# HireIn — Roadmap orientado a validação

> **Status:** planejamento inicial  
> **Estratégia:** avançar por evidência, não por calendário  
> **Regra:** nenhuma fase existe apenas porque a anterior foi programada; ela existe quando a anterior foi validada.

---

## 1. Filosofia do roadmap

O HireIn não começará tentando ser um SaaS completo.

O projeto deverá provar, nesta ordem:

```text
1. entende o candidato?
2. entende a vaga?
3. consegue medir compatibilidade?
4. consegue preparar candidatura correta?
5. consegue preencher processo com segurança?
6. isso economiza tempo?
7. isso melhora resultados?
8. somente então: funciona para outras pessoas?
```

Essa ordem evita investir cedo em:

- multiusuário;
- billing;
- infraestrutura escalável;
- browser cloud;
- observabilidade complexa;
- integrações excessivas;
- marketing;
- funcionalidades sociais;

antes de comprovar o núcleo do produto.

---

# FASE 0 — Fundação

## Objetivo

Criar bases suficientes para começar o experimento sem gerar dívida estrutural desnecessária.

## Entregas

### Produto

- briefing;
- fluxos de produto;
- regras de verdade;
- definição do HireIn Match;
- definição da Answer Library;
- estratégia de candidatura assistida.

### Engenharia

- arquitetura;
- stack inicial;
- organização do repositório;
- padrões de código;
- estratégia de testes;
- observabilidade mínima;
- política de custos.

### Privacidade

- classificação de dados;
- local-first;
- regras de secrets;
- regras de IA;
- gate de abertura pública.

## Status

```text
DOCUMENTAÇÃO: EM ANDAMENTO / MAIOR PARTE CONCLUÍDA
CÓDIGO: NÃO INICIADO
```

## Gate de saída

Só iniciar implementação quando estiver claro:

- o que o MVP precisa provar;
- o que não será construído;
- quais dados serão necessários;
- qual será a primeira jornada real de teste.

---

# FASE 1 — Candidate Core

## Pergunta a responder

> O HireIn consegue representar corretamente uma pessoa profissionalmente sem depender apenas de um PDF de currículo?

## Escopo

Construir o núcleo do candidato.

### Candidate Profile

- identidade mínima;
- objetivos profissionais;
- cargos desejados;
- senioridade;
- localização;
- modalidade;
- tipo de contrato;
- expectativa salarial;
- experiências;
- formação;
- competências;
- certificações;
- idiomas.

### Resume Import

Importar currículo para sugerir estrutura inicial.

Fluxo:

```text
currículo
   ↓
parser
   ↓
extração
   ↓
CandidateFact sugerido
   ↓
revisão humana
   ↓
USER_CONFIRMED
```

A extração não é fonte final de verdade.

### Answer Library v0

Criar respostas reutilizáveis para perguntas frequentes.

Exemplos:

- disponibilidade;
- viagens;
- mudança;
- modelo de trabalho;
- pretensão salarial;
- CNH;
- formação;
- idiomas.

## Fora de escopo

- Auto Apply;
- scraping em massa;
- multiusuário;
- billing;
- dados sensíveis persistentes;
- IA decidindo fatos.

## Métricas

### Qualidade da extração

Medir:

```text
campos corretos
campos incompletos
campos errados
fatos inventados
```

### Gate

**Zero fato inventado aceito como informação confirmada.**

O perfil precisa representar corretamente o piloto antes de avançar.

---

# FASE 2 — Job Intelligence

## Pergunta

> O HireIn consegue transformar uma vaga real em informação estruturada e comparável?

## Entrada inicial

Não começar com crawler massivo.

O usuário poderá fornecer:

- URL da vaga;
- texto da vaga;
- importação por extensão futuramente.

## Job Normalizer

Transformar descrição em schema.

Exemplo:

```text
Job
- title
- company
- location
- work_mode
- contract_type
- seniority
- salary
- required_skills
- desired_skills
- required_experience
- education
- languages
- travel
- hard_requirements
- source
- ats
```

## Regras

- preservar texto original;
- separar requisito obrigatório de desejável;
- não inventar salário ausente;
- não inferir modalidade quando ambígua;
- registrar confiança da extração.

## Dataset inicial

Criar conjunto real de aproximadamente:

```text
30–50 vagas
```

relacionadas ao objetivo profissional do usuário piloto.

Esse conjunto será também o primeiro benchmark de matching.

## Gate

A representação estruturada deve ser considerada útil e confiável pelo usuário piloto na maioria das vagas avaliadas.

---

# FASE 3 — HireIn Match v1

## Pergunta

> Conseguimos ordenar vagas aproximadamente como o próprio candidato ordenaria?

## Arquitetura inicial

O Match não deve ser apenas LLM.

Proposta:

```text
hard filters
    ↓
structured rules
    ↓
semantic similarity
    ↓
LLM judge quando necessário
    ↓
explanation
```

## Hard filters

Exemplos:

- localidade incompatível;
- presencial fora da região aceita;
- idioma obrigatório ausente;
- certificação obrigatória ausente;
- regime não aceito;
- senioridade claramente incompatível.

Hard requirement não deve desaparecer dentro de uma média numérica.

## Benchmark de embeddings

Comparar modelos multilíngues com dataset PT-BR.

Critérios:

- ranking;
- Recall@K;
- NDCG@K;
- similaridade de cargos brasileiros;
- CPU/RAM;
- latência;
- possibilidade de uso local;
- licença;
- custo.

## Ground truth

O próprio usuário piloto classificará as vagas.

Exemplo:

```text
5 = excelente
4 = boa
3 = talvez
2 = baixa compatibilidade
1 = irrelevante
```

## Meta inicial proposta

Entre as vagas classificadas pelo sistema como Top 10:

```text
≥ 80% devem ser avaliadas pelo piloto como 4 ou 5
```

Essa meta pode ser ajustada após observação do primeiro dataset.

## Regra

Se o ranking for ruim:

**não avançar para automação de candidatura.**

Automatizar match ruim apenas produz candidaturas ruins mais rapidamente.

---

# FASE 4 — Application Studio

## Pergunta

> O HireIn consegue preparar uma candidatura melhor sem distorcer o histórico profissional?

## Funcionalidades

### Job Workspace

Para cada vaga:

- descrição;
- Match;
- requisitos;
- gaps;
- currículo recomendado;
- respostas necessárias;
- status.

### Resume Tailoring v1

Entrada:

```text
Candidate Facts confirmados
+
vaga
+
currículo base
```

Saída:

```text
currículo direcionado
```

Pode:

- reorganizar;
- resumir;
- destacar;
- adaptar vocabulário.

Não pode:

- inventar.

### Answer Assistant

Ordem de resolução:

```text
1. Answer Library
2. Candidate Facts
3. regra determinística
4. draft de IA
5. pedir usuário
```

## Métricas

Avaliar por candidatura:

```text
respostas corretas
respostas editadas
respostas rejeitadas
fatos inventados
tempo de preparação
```

## Gate

Meta desejada:

- 100% dos fatos objetivos corretos;
- 0 experiência inventada;
- drafts necessitando cada vez menos correção;
- redução perceptível do tempo de preparação.

---

# FASE 5 — Application Agent v0

## Pergunta

> O HireIn consegue preencher uma candidatura real corretamente sob supervisão humana?

## Regra

```text
AUTO SUBMIT = OFF
```

## Fluxo

```text
vaga escolhida
    ↓
usuário inicia aplicação
    ↓
agent abre ATS
    ↓
identifica adapter
    ↓
preenche
    ↓
encontra pergunta
    ↓
resolve / solicita resposta
    ↓
anexa currículo
    ↓
tela de revisão
    ↓
usuário envia
```

## Seleção do primeiro ATS

Não escolher apenas pela preferência da equipe.

Usar o dataset das vagas reais do piloto e medir:

```text
quantidade de vagas por ATS
complexidade
relevância das vagas
estabilidade
termos/integrabilidade
```

A Gupy é candidata natural por relevância no mercado brasileiro, porém a ordem final dos adapters deverá ser determinada pelos dados do piloto.

Greenhouse e Lever podem ser usados como referências técnicas para validar o padrão de adapters quando aparecerem nas vagas reais.

## Architecture Adapter Contract

Todo adapter deverá expor contrato semelhante a:

```text
detect()
start()
extract_form()
map_fields()
fill()
upload_resume()
validate()
prepare_submit()
```

`submit()` deverá permanecer bloqueado no piloto inicial.

## Métricas

- campos identificados;
- campos preenchidos corretamente;
- intervenção humana;
- falhas por ATS;
- tempo economizado;
- retries;
- perguntas desconhecidas.

## Meta de qualidade antes de considerar autonomia

Em um conjunto representativo de aplicações supervisionadas:

```text
≥ 95% dos campos conhecidos preenchidos corretamente
100% de revisão disponível
0 submissão duplicada
0 fato inventado
0 envio sem intenção do usuário
```

---

# FASE 6 — Pilot Loop

## Pergunta

> O HireIn realmente melhora a busca por emprego?

Esta fase deixa de medir apenas tecnologia.

Passamos a medir resultado.

## Funil

```text
vagas analisadas
      ↓
vagas recomendadas
      ↓
vagas aprovadas
      ↓
candidaturas preparadas
      ↓
candidaturas enviadas
      ↓
respostas
      ↓
assessments
      ↓
entrevistas
      ↓
propostas
```

## Métricas principais

### Eficiência

```text
tempo médio para avaliar vaga
tempo médio para preparar candidatura
tempo médio de preenchimento
intervenções humanas por candidatura
```

### Qualidade

```text
% recomendadas que usuário realmente queria
% candidaturas abandonadas
% respostas corrigidas
falhas de adapter
```

### Resultado

```text
response rate
interview rate
assessment rate
proposal rate
```

Não haverá promessa de que o HireIn sozinho causa entrevistas. Existem muitas variáveis externas.

O que buscamos é evidência de que ele melhora eficiência e qualidade do processo.

## Meta de economia de tempo

Hipótese inicial:

```text
≥ 50% de redução do tempo operacional por candidatura
```

A medição real determinará se essa hipótese é válida.

---

# FASE 7 — Tracking e Career CRM

## Objetivo

Parar de pensar apenas no momento da candidatura.

## Application Tracker

Estados possíveis:

```text
DISCOVERED
REVIEWED
SAVED
PREPARING
READY
APPLIED
CONFIRMED
ASSESSMENT
INTERVIEW
REJECTED
OFFER
HIRED
WITHDRAWN
```

## Eventos

Manter timeline:

```text
job found
match calculated
resume generated
application submitted
confirmation received
interview scheduled
rejected
```

## Inbox futura

Antes de criar uma caixa de e-mail própria, validar primeiro se tracking manual/integração de e-mail realmente é necessário.

Uma inbox dedicada é uma possibilidade futura, não requisito do MVP.

---

# FASE 8 — Learning Loop

## Pergunta

> O sistema consegue aprender com o resultado do próprio candidato?

Exemplo:

```text
Vagas Match 70–79 → baixa conversão
Vagas Match 80–89 → conversão média
Vagas Match 90+    → conversão alta
```

O sistema poderá comparar:

- cargo;
- empresa;
- setor;
- senioridade;
- skills;
- modalidade;
- faixa salarial;
- currículo utilizado;
- resultado.

## Regra

Não alterar pesos automaticamente sem explicação e controle.

Primeira abordagem:

```text
analytics
    ↓
recomendação de ajuste
    ↓
usuário aceita/rejeita
```

Antes de:

```text
modelo se reconfigura sozinho
```

---

# GATE A — Vale continuar?

Após o piloto completo, responder objetivamente:

### Produto

- o Match realmente ajuda?
- o tailoring melhora candidatura?
- o autofill funciona?
- o produto economiza tempo?
- o tracking agrega valor?

### Engenharia

- adapters são sustentáveis?
- manutenção está aceitável?
- IA está previsível?
- custo está controlado?

### Resultado

- o usuário está conseguindo se candidatar melhor?
- houve mais respostas relevantes?
- houve entrevistas?

Possíveis decisões:

```text
GO
CONTINUE PILOT
PIVOT
STOP
```

Encerrar ou pivotar também é resultado válido de experimento.

---

# FASE 9 — Preparação para terceiros

**Esta fase só começa depois do Gate A = GO.**

## Produto

- onboarding;
- conta;
- importação de currículo;
- edição de perfil;
- controles de automação;
- configurações de privacidade;
- exclusão/exportação.

## Engenharia

- autenticação;
- tenant isolation;
- storage privado;
- queue adequada ao volume;
- workers remotos quando necessários;
- staging;
- production;
- backups;
- observabilidade.

## Privacidade

Concluir todo o gate definido em:

```text
docs/07-PRIVACY-SECURITY-LGPD.md
```

## Grupo inicial

Não abrir publicamente.

Começar com grupo pequeno e controlado.

Exemplo conceitual:

```text
5 usuários
      ↓
20 usuários
      ↓
50 usuários
```

Cada expansão depende da estabilidade da fase anterior.

---

# FASE 10 — Private Beta

## Objetivo

Descobrir se o HireIn funciona fora do perfil do criador.

## Perguntas

- perfis diferentes quebram o schema?
- pessoas entendem o Match?
- Answer Library funciona para outros segmentos?
- extração de currículo é robusta?
- outros usuários confiam na automação?
- os adapters funcionam em combinações inesperadas?
- suporte operacional é sustentável?

## Não medir apenas crescimento

O beta precisa encontrar problemas.

Um beta que só mede cadastro perdeu sua função.

---

# FASE 11 — Auto Apply controlado

Auto Apply não será simplesmente um toggle liberado para todos.

## Pré-condições

- segurança aprovada;
- privacidade aprovada;
- adapter estável;
- usuário explicitamente opt-in;
- limites de frequência;
- score mínimo;
- regras de hard requirements;
- histórico de auditoria;
- kill switch;
- nenhuma pergunta desconhecida sem política definida.

## Modos

### Review

```text
HireIn prepara
usuário envia
```

### Assisted

```text
HireIn prepara
regras confiáveis são preenchidas
usuário revisa e envia
```

### Controlled Auto

```text
somente vagas que atendem políticas pré-definidas
```

Não haverá modo conceitualmente equivalente a:

```text
candidate-se em tudo
```

---

# FASE 12 — SaaS público

Somente depois de comprovar:

- valor;
- confiabilidade;
- privacidade;
- segurança;
- sustentabilidade técnica;
- custo por usuário;
- capacidade operacional.

## Só aqui passam a fazer sentido

- billing;
- planos;
- limites comerciais;
- marketing público;
- suporte estruturado;
- SLAs internos;
- otimização de aquisição.

---

# Estratégia de custos por fase

## Fases 0–8

Objetivo:

```text
infra fixa ≈ US$ 0/mês
```

Aceitar gasto pontual de IA somente quando necessário para benchmark ou qualidade.

## Fase 9+

Custos passam a ser modelados por unidade econômica:

```text
custo por usuário ativo
custo por vaga analisada
custo por currículo gerado
custo por candidatura
custo de browser worker
custo de storage
custo de LLM
```

Não otimizar custo por antecipação sem medir uso real.

---

# Dívidas que não aceitaremos

Mesmo no piloto, evitar:

- regras de negócio dentro de componentes de UI;
- prompts espalhados pelo código;
- provider de IA acoplado à regra de domínio;
- selectors de ATS espalhados fora dos adapters;
- secrets em código;
- fatos profissionais sem provenance;
- estado de candidatura sem eventos/auditoria;
- migrations manuais sem versionamento;
- testes dependentes de vagas reais que desaparecem.

---

# Fixtures e replay

Automação web precisa poder ser testada sem depender permanentemente do site vivo.

Sempre que permitido e seguro, manter fixtures sintéticas/estruturais para testar:

- parsing;
- field mapping;
- normalização;
- regras.

Nunca guardar em fixture pública:

- cookies reais;
- dados pessoais reais;
- candidaturas reais;
- respostas sensíveis.

---

# ADRs

Decisões importantes deverão ganhar Architecture Decision Records.

Exemplos futuros:

```text
ADR-001 frontend framework
ADR-002 backend language/framework
ADR-003 embedding model
ADR-004 LLM provider strategy
ADR-005 authentication
ADR-006 browser execution model
ADR-007 queue migration
```

Mudanças são permitidas.

Mudanças silenciosas sem registrar contexto não são.

---

# Próximo marco executável

Com a documentação atual, o próximo passo não é criar toda a plataforma.

É construir uma **vertical slice** mínima:

```text
1 perfil real
     ↓
1 vaga real
     ↓
normalização
     ↓
Match explicável
     ↓
currículo/respostas preparados
     ↓
sem Auto Apply
```

Depois ampliar para:

```text
10 vagas
↓
30–50 vagas
↓
primeiro adapter supervisionado
```

Esse caminho permite testar cada hipótese antes de adicionar a próxima camada de complexidade.

---

## Definição de sucesso do piloto

O piloto será considerado tecnicamente promissor se demonstrar conjuntamente:

1. **Relevância** — as melhores recomendações realmente fazem sentido;
2. **Verdade** — nenhum fato profissional é inventado;
3. **Eficiência** — redução relevante do trabalho operacional;
4. **Confiabilidade** — preenchimento assistido funciona de forma previsível;
5. **Controle** — o usuário entende e aprova o que será enviado;
6. **Aprendizado** — conseguimos medir quais oportunidades geram melhores resultados;
7. **Custo** — o experimento continua financeiramente leve.

Nenhuma quantidade bruta de candidaturas substitui esses critérios.