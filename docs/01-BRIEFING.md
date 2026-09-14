# HireIn — Briefing de Produto

> **Status:** Documento inicial de produto  
> **Fase:** Descoberta e piloto individual  
> **Mercado inicial:** Brasil  
> **Referência de categoria:** AIApply e ferramentas de job search / auto-apply  
> **Princípio central:** automatizar trabalho repetitivo sem perder controle, verdade ou contexto do candidato.

---

## 1. Visão do produto

O **HireIn** será um agente pessoal de carreira focado no mercado brasileiro.

Seu objetivo é reduzir o esforço operacional envolvido em procurar vagas, avaliar compatibilidade, adaptar materiais de candidatura, preencher processos seletivos e acompanhar resultados.

O produto nasce inspirado na categoria de ferramentas como AIApply, mas não terá como proposta principal “candidatar para o maior número possível de vagas”.

A proposta do HireIn será:

> **Encontrar as vagas certas, entender o quanto elas combinam com o candidato e tornar a candidatura muito mais rápida, consistente e inteligente.**

O HireIn deve evoluir gradualmente de um **copiloto de candidatura** para um **agente de carreira**, mantendo o usuário no controle das informações enviadas em seu nome.

---

## 2. Contexto e problema

Procurar emprego atualmente envolve várias tarefas repetitivas e fragmentadas:

- acessar diferentes portais de vagas;
- repetir buscas semelhantes;
- abrir dezenas de oportunidades para descobrir que muitas não fazem sentido;
- comparar requisitos da vaga com o próprio currículo;
- preencher repetidamente nome, telefone, endereço, experiência e formação;
- responder novamente perguntas já respondidas em outros processos;
- adaptar currículo para diferentes oportunidades;
- escrever cartas ou respostas abertas;
- lembrar em quais vagas já houve candidatura;
- acompanhar e-mails de confirmação, entrevistas e rejeições;
- entender quais tipos de vaga realmente estão gerando retorno.

O problema não é apenas encontrar vagas.

O problema é o **custo mental e operacional de transformar uma vaga interessante em uma candidatura bem feita e acompanhada**.

Esse atrito faz o candidato gastar tempo com tarefas administrativas em vez de investir energia em:

- melhorar sua formação;
- preparar entrevistas;
- estudar empresas;
- desenvolver portfólio;
- fortalecer networking;
- escolher melhores oportunidades.

---

## 3. Hipótese principal

Se o HireIn conseguir reunir o perfil profissional do usuário, compreender suas preferências, encontrar oportunidades relevantes e automatizar grande parte do trabalho repetitivo de candidatura, então será possível:

1. reduzir significativamente o tempo gasto procurando e preenchendo vagas;
2. aumentar a qualidade média das candidaturas;
3. aumentar a quantidade de candidaturas relevantes sem transformar o processo em spam;
4. melhorar a consistência das informações enviadas aos recrutadores;
5. aprender quais tipos de vaga geram mais entrevistas para cada pessoa.

A hipótese não será validada por quantidade de aplicações.

Será validada principalmente por **qualidade de match e conversão em respostas, entrevistas e oportunidades reais**.

---

## 4. Estratégia de validação

O HireIn não começará como um SaaS público.

A primeira versão será construída como um **piloto individual**, utilizando o próprio criador do produto como primeiro usuário real.

### Objetivo do piloto

Validar se o HireIn consegue executar de forma confiável o fluxo completo:

```text
Perfil do candidato
        ↓
Descoberta de vagas
        ↓
Análise de compatibilidade
        ↓
Priorização
        ↓
Preparação da candidatura
        ↓
Preenchimento / candidatura assistida
        ↓
Acompanhamento
        ↓
Resultado
        ↓
Aprendizado
```

### Regra de expansão

O produto somente deverá ser preparado para outros usuários após demonstrar, no piloto:

- boa qualidade de matching;
- consistência das respostas geradas;
- ausência de informações inventadas;
- baixa taxa de candidaturas irrelevantes;
- capacidade de acompanhar corretamente o status das vagas;
- ganho real de tempo;
- evidência de retorno em processos seletivos;
- estabilidade mínima das integrações e automações.

Antes de qualquer abertura para terceiros, deverão ser tratados formalmente:

- LGPD;
- política de privacidade;
- consentimento;
- retenção e exclusão de dados;
- segurança de credenciais;
- dados sensíveis;
- auditoria das ações realizadas pelo agente;
- termos de uso;
- limites de automação por plataforma.

---

## 5. Público-alvo

### Fase 0 — Piloto

Um único usuário.

O objetivo desta fase não é escalabilidade comercial, mas aprendizado.

### Público-alvo futuro

Pessoas no Brasil que:

- estão procurando emprego ativamente;
- querem mudar de carreira;
- enviam diversas candidaturas por semana;
- sentem dificuldade em organizar processos seletivos;
- perdem muito tempo preenchendo formulários;
- não sabem avaliar se uma vaga realmente combina com seu perfil;
- têm dificuldade em adaptar currículo para cada oportunidade;
- gostariam de usar IA para auxiliar a busca sem permitir que ela invente informações.

### Segmentos futuros possíveis

- profissionais de tecnologia;
- administrativos e analistas;
- profissionais em transição de carreira;
- estudantes e recém-formados;
- pessoas buscando estágio;
- profissionais de ERP / consultoria / implantação;
- pessoas desempregadas em busca ativa;
- profissionais empregados procurando novas oportunidades discretamente.

O produto não deverá assumir desde o início que todos esses públicos possuem os mesmos fluxos ou necessidades.

---

## 6. Job to Be Done

### Job principal

> “Quando eu estiver procurando uma nova oportunidade, quero que uma ferramenta encontre e organize vagas realmente compatíveis comigo, prepare a candidatura usando apenas informações verdadeiras e reduza ao máximo o trabalho repetitivo, para que eu possa focar nas oportunidades com maior chance de retorno.”

### Jobs secundários

- “Quero entender por que uma vaga combina ou não comigo.”
- “Quero saber quais competências estão faltando para determinadas vagas.”
- “Quero adaptar meu currículo sem precisar reescrevê-lo do zero.”
- “Quero responder uma pergunta de processo seletivo uma única vez e reutilizar essa informação.”
- “Quero saber onde já me candidatei.”
- “Quero acompanhar entrevistas, rejeições e retornos.”
- “Quero descobrir quais tipos de vaga estão trazendo melhores resultados.”

---

## 7. Posicionamento

O HireIn não será vendido conceitualmente como um “robô que se candidata em massa”.

O posicionamento desejado é:

> **Seu agente pessoal de carreira para encontrar, priorizar e conquistar melhores oportunidades no Brasil.**

### Diferencial desejado

**Qualidade antes de volume.**

O HireIn deve tentar responder:

> “Esta vaga faz sentido para mim?”

antes de responder:

> “Consigo me candidatar automaticamente?”

---

## 8. Princípios de produto

### 8.1 Verdade acima de otimização

A IA pode:

- reorganizar;
- resumir;
- destacar;
- adaptar linguagem;
- relacionar experiências reais com requisitos da vaga.

A IA não pode:

- inventar experiência;
- inventar certificações;
- inventar formação;
- inventar idiomas;
- inventar ferramentas utilizadas;
- inventar resultados profissionais;
- afirmar disponibilidade, salário ou condições pessoais sem informação registrada pelo usuário.

---

### 8.2 Automação progressiva

O HireIn deverá começar assistindo o usuário antes de agir sozinho.

Evolução desejada:

```text
Manual
  ↓
Assistido
  ↓
Semiautomático
  ↓
Automático controlado
```

A autonomia aumenta somente quando a confiabilidade estiver comprovada.

---

### 8.3 Explicabilidade

O usuário deverá conseguir entender por que determinada vaga recebeu uma pontuação alta ou baixa.

Exemplo:

```text
Compatibilidade: 89%

Experiência      95%
Competências     92%
Senioridade      100%
Localização      100%
Formação         80%
Idioma           65%
```

Além da pontuação, o HireIn deve explicar:

- pontos fortes;
- requisitos atendidos;
- requisitos parcialmente atendidos;
- gaps;
- possíveis impeditivos.

---

### 8.4 Controle do usuário

O usuário deve poder decidir:

- quais cargos deseja;
- onde deseja trabalhar;
- modelo presencial, híbrido ou remoto;
- faixa salarial;
- senioridade;
- tecnologias ou áreas desejadas;
- empresas indesejadas;
- distância aceitável;
- tipos de contrato;
- score mínimo para recomendação;
- score mínimo para automação futura;
- quais informações podem ser reutilizadas automaticamente.

---

### 8.5 Aprender com resultados

O HireIn não deve aprender apenas com descrição de vagas.

Deverá futuramente aprender com eventos reais:

```text
vaga encontrada
vaga ignorada
vaga salva
candidatura enviada
candidatura confirmada
rejeição
assessment
entrevista
proposta
contratação
```

Isso permitirá responder futuramente:

> “Quais características aparecem nas vagas que mais me chamam para entrevistas?”

---

## 9. Mercado brasileiro como requisito de produto

O HireIn deverá ser construído considerando particularidades brasileiras desde o início.

Exemplos:

### Relações de trabalho

- CLT;
- PJ;
- estágio;
- jovem aprendiz;
- temporário;
- cooperado quando aplicável;
- prestação de serviços.

### Modalidade

- presencial;
- híbrido;
- remoto.

### Dados e perguntas comuns

- pretensão salarial mensal;
- cidade e estado;
- disponibilidade para mudança;
- disponibilidade para viagens;
- CNH;
- disponibilidade de horário;
- benefícios;
- PCD quando voluntariamente informado;
- formação em andamento;
- previsão de conclusão;
- idiomas.

### Linguagem do mercado

O matching deverá compreender equivalências e proximidades entre cargos brasileiros.

Exemplo:

```text
Consultor de Implantação
Analista de Implantação
Analista de Sistemas
Consultor ERP
Analista ERP
Analista de Projetos
```

Esses títulos podem representar experiências altamente relacionadas dependendo da descrição da vaga.

O sistema não deverá utilizar somente comparação literal de títulos.

---

## 10. Perfil Profissional Universal

Um dos pilares do HireIn será um perfil estruturado e reutilizável do candidato.

O usuário deverá informar os dados uma vez e reutilizá-los em diferentes plataformas.

### Blocos esperados

#### Identidade e contato

- nome;
- e-mail;
- telefone;
- cidade;
- estado;
- links profissionais;
- LinkedIn;
- portfólio;
- GitHub quando aplicável.

#### Objetivos

- cargos desejados;
- áreas de interesse;
- senioridade;
- localização;
- modalidade;
- tipos de contrato;
- faixa salarial;
- disponibilidade.

#### Experiência

- empresas;
- cargos;
- períodos;
- atividades;
- projetos;
- tecnologias;
- resultados.

#### Formação

- curso;
- instituição;
- status;
- início;
- previsão de conclusão.

#### Competências

- ferramentas;
- tecnologias;
- processos;
- metodologias;
- idiomas;
- certificações.

---

## 11. Biblioteca de Respostas

O usuário não deveria responder repetidamente às mesmas perguntas em cada processo seletivo.

O HireIn deverá manter uma **Biblioteca de Respostas**.

Exemplos:

```text
Possui disponibilidade para viagens?
Sim.
```

```text
Possui CNH?
Sim, categoria B.
```

```text
Qual sua pretensão salarial?
R$ X.XXX,00
```

```text
Possui disponibilidade para trabalho presencial?
Sim, dentro das regiões definidas no meu perfil.
```

Cada resposta deverá possuir origem clara:

```text
USER_CONFIRMED
RESUME_EXTRACTED
AI_DRAFT
```

Respostas geradas por IA não devem se transformar automaticamente em fatos permanentes sem confirmação quando envolverem informação pessoal ou profissional objetiva.

---

## 12. HireIn Match

O HireIn deverá calcular compatibilidade entre candidato e vaga.

A pontuação não deverá depender apenas de palavras-chave.

Dimensões possíveis:

- cargo;
- área;
- senioridade;
- competências;
- experiência;
- formação;
- localização;
- modalidade;
- salário;
- idioma;
- disponibilidade;
- tipo de contrato;
- requisitos obrigatórios;
- requisitos desejáveis.

### Resultado esperado

```text
HireIn Match: 91%

Pontos fortes
+ experiência compatível com implantação
+ conhecimento de ERP
+ atendimento ao cliente
+ SQL
+ gestão de projetos

Gaps
- vaga pede Power BI avançado
- inglês B2 desejável

Impedimentos
Nenhum identificado
```

### Regra essencial

Um score alto não deve esconder um requisito eliminatório.

Exemplo:

```text
Match semântico: 93%
Requisito obrigatório: inglês fluente
Usuário: inglês básico

Resultado:
NÃO recomendado para candidatura automática.
```

---

## 13. Currículo adaptado por vaga

O HireIn poderá gerar uma versão direcionada do currículo para cada oportunidade.

Entrada:

```text
Currículo base
+
Perfil profissional
+
Descrição da vaga
```

Saída:

```text
Currículo adaptado
```

### O que pode mudar

- ordem de competências;
- resumo profissional;
- destaque de experiências relevantes;
- escolha de projetos relevantes;
- linguagem;
- palavras e conceitos coerentes com a vaga;
- tamanho e organização.

### O que não pode mudar

Fatos.

O currículo adaptado nunca poderá adicionar algo que o usuário não tenha realmente feito, estudado ou utilizado.

---

## 14. Modos de candidatura

O HireIn deverá evoluir para três níveis de automação.

### Modo 1 — Revisão

Nenhuma candidatura é enviada sem revisão do usuário.

Fluxo:

```text
HireIn encontra vaga
        ↓
analisa
        ↓
prepara candidatura
        ↓
usuário revisa
        ↓
usuário autoriza envio
```

Este será o modo inicial do piloto.

---

### Modo 2 — Assistido

O HireIn pode executar automaticamente partes de baixo risco.

Exemplo:

```text
Match ≥ limite configurado
+
nenhuma pergunta desconhecida
+
nenhum requisito eliminatório
+
dados suficientes
```

Ainda poderá existir uma etapa final de revisão.

---

### Modo 3 — Automático controlado

Somente deverá existir após validação suficiente.

Exemplo futuro:

```text
Match ≥ 88%
Cargo permitido
Faixa salarial permitida
Localização permitida
Contrato permitido
Sem respostas desconhecidas
Sem dados sensíveis pendentes
```

Somente então a candidatura poderá ser enviada sem revisão individual.

---

## 15. Estratégia de plataformas

O HireIn não deverá depender de automação indiscriminada em qualquer website.

Prioridade conceitual:

1. integrações oficiais quando disponíveis;
2. fluxos de candidatura externos e ATS suportados;
3. preenchimento assistido por extensão;
4. automação de navegador apenas quando tecnicamente e contratualmente apropriada;
5. fallback manual quando houver CAPTCHA, autenticação especial, pergunta desconhecida ou fluxo inseguro.

### Plataformas relevantes para investigação

- Gupy;
- Greenhouse;
- Lever;
- Workday;
- Sólides;
- Abler;
- Pandapé;
- outros ATSs relevantes no Brasil.

A ordem final deverá ser definida por cobertura real encontrada durante o piloto.

---

## 16. Escopo do primeiro MVP

O primeiro MVP deverá validar o núcleo de valor sem tentar automatizar todo o mercado.

### Deve existir

- perfil profissional estruturado;
- importação ou cadastro de currículo;
- preferências de vagas;
- cadastro / ingestão inicial de oportunidades;
- normalização básica de vagas;
- análise de compatibilidade;
- HireIn Match;
- explicação de match;
- identificação de gaps;
- currículo adaptado;
- biblioteca de respostas;
- registro de candidaturas;
- acompanhamento de status;
- revisão humana antes da candidatura.

### Pode existir no piloto

- extensão de navegador;
- preenchimento assistido de formulários;
- automação de um número muito pequeno de ATSs;
- integração experimental com e-mail;
- classificação automática de retornos.

### Não é requisito para o primeiro MVP

- multiusuário;
- billing;
- assinatura;
- marketplace;
- aplicativo mobile nativo;
- dezenas de ATSs;
- auto-apply irrestrito;
- candidatura em massa;
- painel corporativo;
- white label;
- planos comerciais.

---

## 17. Fora de escopo deliberado

O HireIn não deverá:

- enviar centenas de candidaturas irrelevantes apenas para aumentar volume;
- inventar qualificações;
- tentar burlar CAPTCHA;
- tentar esconder automação deliberadamente de mecanismos de segurança;
- depender de violação de termos de plataformas como estratégia de negócio;
- enviar respostas pessoais desconhecidas sem intervenção do usuário;
- tomar decisões sobre dados sensíveis sem consentimento explícito;
- automatizar qualquer plataforma apenas porque tecnicamente é possível.

---

## 18. Fluxo ideal do usuário

### Onboarding

```text
Criar perfil
    ↓
Importar currículo
    ↓
Revisar informações extraídas
    ↓
Definir objetivos profissionais
    ↓
Definir preferências
    ↓
Criar biblioteca inicial de respostas
```

### Rotina

```text
HireIn encontra vagas
        ↓
normaliza
        ↓
calcula Match
        ↓
prioriza
        ↓
usuário abre recomendação
        ↓
compreende pontos fortes / gaps
        ↓
HireIn prepara candidatura
        ↓
usuário revisa
        ↓
candidatura
        ↓
acompanhamento
```

---

## 19. Career Inbox

Uma evolução importante será centralizar comunicações de processos seletivos.

O HireIn poderá futuramente classificar mensagens como:

- candidatura recebida;
- candidatura em análise;
- rejeição;
- convite para entrevista;
- assessment;
- solicitação de informação;
- proposta;
- mensagem desconhecida.

Isso permitirá atualizar automaticamente o funil de cada candidatura.

### Exemplo

```text
Empresa A
Analista de Projetos

Encontrada      ✓
Analisada       ✓
Candidatura     ✓
Confirmada      ✓
Entrevista      ✓
Proposta        —
```

---

## 20. Funil de carreira

O HireIn deverá tratar a procura de emprego como um processo mensurável.

Estados conceituais:

```text
FOUND
SCORED
SAVED
IGNORED
PREPARING
READY_TO_APPLY
APPLIED
CONFIRMED
ASSESSMENT
INTERVIEW
REJECTED
OFFER
HIRED
WITHDRAWN
```

Esses estados permitirão analisar conversão.

Exemplo:

```text
100 vagas analisadas
45 recomendadas
30 candidaturas
8 retornos
5 entrevistas
1 proposta
```

---

## 21. Métricas do piloto

O piloto deverá responder se o produto realmente ajuda.

### Eficiência

- tempo médio para avaliar uma vaga;
- tempo médio para preparar candidatura;
- tempo médio economizado por candidatura;
- percentual de campos preenchidos automaticamente.

### Qualidade

- percentual de vagas recomendadas consideradas relevantes pelo usuário;
- percentual de recomendações rejeitadas pelo usuário;
- quantidade de correções feitas em respostas da IA;
- quantidade de fatos incorretos gerados;
- quantidade de candidaturas enviadas para vagas posteriormente consideradas inadequadas.

### Conversão

- candidaturas enviadas;
- confirmações;
- respostas;
- assessments;
- entrevistas;
- propostas;
- contratação.

### Indicador principal inicial

**Entrevistas geradas por candidaturas relevantes**, e não simplesmente número de candidaturas.

---

## 22. Critérios de sucesso do piloto

O piloto será considerado promissor quando houver evidências de que:

1. a maior parte das vagas recomendadas realmente faz sentido;
2. o sistema reduz significativamente o tempo de candidatura;
3. o usuário confia no currículo e nas respostas geradas;
4. o HireIn não inventa informações;
5. o rastreamento de candidaturas funciona;
6. as candidaturas produzem retorno real;
7. a manutenção da automação permanece viável.

Não será obrigatório atingir todos os critérios imediatamente.

O objetivo é descobrir quais partes possuem valor real antes de investir em escala.

---

## 23. Estratégia de custo

A premissa inicial será:

> **começar com custo zero ou o mais próximo possível de zero.**

Decisões de tecnologia deverão, sempre que possível, privilegiar:

- planos gratuitos;
- execução local durante o piloto;
- serviços serverless;
- bancos gratuitos dentro de limites adequados;
- armazenamento gratuito ou de baixo custo;
- modelos de IA econômicos para tarefas simples;
- uso de modelos mais capazes somente quando necessário;
- cache de análises;
- processamento sob demanda;
- ausência de infraestrutura preparada prematuramente para milhares de usuários.

A arquitetura, infraestrutura e estimativa detalhada de custos serão documentadas separadamente.

---

## 24. Privacidade por fase

### Piloto individual

A prioridade será evitar exposição desnecessária de dados e utilizar apenas o mínimo necessário.

Mesmo sendo um piloto, as decisões não devem criar uma arquitetura impossível de proteger futuramente.

### Antes do beta fechado

Obrigatório definir:

- classificação de dados;
- criptografia;
- autenticação;
- autorização;
- logs;
- auditoria;
- política de retenção;
- exclusão de conta;
- exportação de dados;
- consentimentos;
- tratamento de dados sensíveis;
- política de privacidade;
- termos de uso;
- bases legais aplicáveis.

### Antes da abertura pública

Deverá existir uma revisão formal de privacidade e LGPD.

---

## 25. Riscos de produto

### Matching ruim

**Risco:** recomendar muitas vagas irrelevantes.

**Mitigação:** feedback explícito, filtros e explicação do score.

---

### IA inventando informações

**Risco:** prejudicar a credibilidade do candidato.

**Mitigação:** fatos estruturados, rastreabilidade da origem e confirmação humana.

---

### Automação quebrando

**Risco:** ATSs alterarem telas ou fluxos.

**Mitigação:** adapters isolados, fallback manual e início com poucas plataformas.

---

### Volume acima da qualidade

**Risco:** transformar o produto em spam de candidatura.

**Mitigação:** limites, score mínimo e foco em conversão.

---

### Dependência de terceiros

**Risco:** mudanças de APIs, termos ou mecanismos de acesso.

**Mitigação:** múltiplas estratégias de integração e ausência de dependência crítica de uma única plataforma.

---

### Privacidade

**Risco:** o produto manipula dados profissionais e pessoais relevantes.

**Mitigação:** expansão somente depois de controles formais de segurança e LGPD.

---

## 26. Evolução de produto proposta

### Fase 0 — Descoberta

- briefing;
- benchmarking;
- definição da experiência;
- arquitetura inicial;
- engenharia;
- infraestrutura;
- custos.

### Fase 1 — Piloto pessoal

- um usuário;
- execução controlada;
- perfil;
- vagas;
- match;
- currículo;
- biblioteca de respostas;
- tracking;
- revisão antes da candidatura.

### Fase 2 — Copiloto

- extensão;
- autofill;
- candidatura assistida;
- primeiros adapters;
- coleta de métricas reais.

### Fase 3 — Agente controlado

- regras de auto-apply;
- filas;
- múltiplos ATSs;
- retries;
- inbox;
- automações baseadas em confiança.

### Fase 4 — Beta fechado

Somente após:

- segurança;
- privacidade;
- LGPD;
- termos;
- observabilidade;
- isolamento de usuários;
- controles de acesso;
- estabilidade mínima.

### Fase 5 — Produto público

- onboarding multiusuário;
- billing;
- planos;
- suporte;
- métricas de negócio;
- expansão de integrações.

---

## 27. Decisões já tomadas

| Tema | Decisão |
|---|---|
| Nome | HireIn |
| Mercado inicial | Brasil |
| Referência de categoria | AIApply |
| Estratégia inicial | Piloto individual |
| Prioridade | Qualidade de match > volume |
| Automação inicial | Revisada pelo usuário |
| IA | Assistir, interpretar e personalizar; nunca inventar fatos |
| Infraestrutura inicial | Custo zero ou mínimo |
| Escala | Somente após validação do piloto |
| Privacidade | Obrigatória antes da abertura para terceiros |
| Auto-apply irrestrito | Fora do MVP |
| Anti-bot | Não construir estratégia baseada em evasão de segurança |

---

## 28. Pergunta norteadora

Toda nova funcionalidade deverá responder:

> **Isto aumenta a chance de o usuário encontrar uma oportunidade adequada ou apenas aumenta o número de candidaturas?**

Se a resposta for apenas “aumenta o número”, a funcionalidade deve ser questionada.

---

## 29. North Star inicial

Durante o piloto, a North Star não será “applications sent”.

Será:

> **Quantidade de oportunidades realmente compatíveis que avançam para interação humana com recrutadores.**

Indicadores auxiliares:

```text
Relevant Jobs Found
        ↓
Qualified Applications
        ↓
Recruiter Responses
        ↓
Interviews
        ↓
Offers
```

---

## 30. Próximos documentos

Este briefing define **o que é o produto e por que ele existe**.

Os documentos seguintes deverão ser produzidos separadamente para evitar misturar decisões de produto com implementação:

1. `02-PRODUCT-FLOWS.md` — fluxos e comportamento funcional;
2. `03-ARCHITECTURE.md` — arquitetura técnica;
3. `04-ENGINEERING.md` — padrões de engenharia e implementação;
4. `05-INFRASTRUCTURE.md` — ambientes, serviços e deploy;
5. `06-COSTS.md` — custos por fase e gatilhos de escala;
6. `07-PRIVACY-SECURITY-LGPD.md` — privacidade, segurança e preparação para terceiros;
7. `08-ROADMAP.md` — sequência de entrega e critérios de passagem de fase.

Esses documentos deverão respeitar a premissa do projeto:

> **não projetar infraestrutura de escala antes de provar que o produto funciona para uma pessoa.**
