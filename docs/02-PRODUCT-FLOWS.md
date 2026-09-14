# HireIn — Product Flows

> **Status:** baseline funcional para o piloto  
> **Fase:** piloto individual  
> **Escopo:** fluxo do produto antes da implementação técnica  
> **Documento anterior:** [01 — Briefing de Produto](01-BRIEFING.md)

---

## 1. Objetivo deste documento

Este documento descreve **como o HireIn deve se comportar** do ponto de vista do usuário e do domínio.

Ele deliberadamente evita transformar decisões de produto em decisões de framework. A arquitetura deve servir estes fluxos — e não o contrário.

O piloto deve provar uma cadeia simples:

```text
perfil verdadeiro
    ↓
vagas relevantes
    ↓
match explicável
    ↓
candidatura preparada
    ↓
revisão humana
    ↓
envio assistido
    ↓
acompanhamento
    ↓
aprendizado por resultado
```

---

## 2. Princípios transversais dos fluxos

Todos os fluxos devem respeitar as seguintes regras:

1. **verdade antes de otimização**;
2. **qualidade de match antes de volume**;
3. **nenhuma candidatura automática no piloto sem evidência de confiabilidade**;
4. **requisitos eliminatórios têm precedência sobre score agregado**;
5. **fatos pessoais e profissionais precisam de origem rastreável**;
6. **IA sugere; fatos objetivos não são promovidos sem confirmação**;
7. **ações externas precisam ser auditáveis**;
8. **quando uma plataforma bloquear automação, o fluxo deve degradar para modo manual/assistido — não tentar contornar a proteção**.

---

## 3. Jornada principal do piloto

### Etapa A — Construir o perfil

O primeiro uso do HireIn não começa procurando vagas. Começa criando uma fonte confiável de fatos sobre o candidato.

```text
Importar currículo
      ↓
Extrair informações
      ↓
Usuário revisa
      ↓
Completar preferências
      ↓
Completar respostas frequentes
      ↓
Perfil pronto
```

### Saída mínima

O perfil deve conter:

- dados de contato necessários à candidatura;
- cargos e áreas desejadas;
- senioridade;
- localização e modalidades aceitas;
- tipos de contrato;
- faixa salarial quando informada;
- experiências profissionais;
- formação;
- competências;
- idiomas;
- certificações;
- disponibilidade relevante;
- respostas frequentes confirmadas.

### Proveniência

Todo fato deve possuir origem, por exemplo:

```text
USER_CONFIRMED
RESUME_EXTRACTED
IMPORTED
AI_DRAFT
```

`AI_DRAFT` nunca equivale automaticamente a um fato confirmado.

---

## 4. Descoberta de vagas

O HireIn deve receber oportunidades por **fontes/adapters**, não por um código acoplado a um único portal.

```text
Fonte A ─┐
Fonte B ─┼─→ normalização → deduplicação → catálogo de vagas
Fonte C ─┘
```

### Para cada vaga normalizada

Devem existir, quando disponíveis:

- título;
- empresa;
- descrição;
- localidade;
- modalidade;
- senioridade;
- tipo de contrato;
- remuneração;
- data de publicação;
- URL original;
- ATS/origem;
- requisitos obrigatórios;
- requisitos desejáveis;
- idioma;
- status da oportunidade.

### Regra de deduplicação

A mesma vaga pode aparecer em mais de uma fonte. O HireIn deve tentar consolidar ocorrências equivalentes sem perder as URLs/origens encontradas.

---

## 5. Pipeline de compatibilidade — HireIn Match

O Match não deve ser uma única chamada de LLM.

Fluxo desejado:

```text
vaga normalizada
      ↓
filtros objetivos
      ↓
requisitos eliminatórios
      ↓
similaridade semântica
      ↓
análise contextual
      ↓
score por dimensão
      ↓
explicação
      ↓
recomendação
```

### 5.1 Filtros objetivos

Exemplos:

- cidade/região;
- remoto/híbrido/presencial;
- contrato;
- senioridade claramente incompatível;
- pretensão salarial quando a vaga informar salário;
- empresas bloqueadas pelo usuário.

### 5.2 Requisitos eliminatórios

Devem gerar um sinal independente do score.

Exemplo:

```text
similaridade semântica: 93%
idioma obrigatório: inglês fluente
perfil: inglês básico

resultado:
BLOCKER_IDENTIFIED
```

O sistema pode continuar mostrando a vaga, mas não deve escondê-la atrás de uma média alta nem elegê-la para automação.

### 5.3 Similaridade semântica

Deve avaliar proximidade real entre:

- experiências;
- competências;
- responsabilidades;
- domínio de negócio;
- cargos relacionados.

Comparação literal de palavras-chave é insuficiente.

### 5.4 Análise contextual

A IA pode ajudar a interpretar situações ambíguas, porém deve produzir uma saída estruturada e justificável.

### 5.5 Resultado

Exemplo:

```text
HireIn Match: 88%
Status: RECOMENDADA

Experiência       94%
Competências      91%
Senioridade      100%
Localização      100%
Formação          80%
Idiomas           65%

Pontos fortes
+ implantação de ERP
+ atendimento ao cliente
+ SQL

Gaps
- Power BI avançado desejável

Blockers
- nenhum
```

---

## 6. Revisão de oportunidade

A tela de detalhe deve responder rapidamente:

1. **o que é esta vaga?**
2. **por que ela combina comigo?**
3. **o que me falta?**
4. **há algum impeditivo?**
5. **o que o HireIn pretende enviar?**
6. **qual é o próximo passo?**

A interface não deve incentivar candidatura somente porque o botão existe.

### Ações do usuário

```text
Salvar
Ignorar
Marcar como não relevante
Preparar candidatura
Abrir vaga original
```

O motivo de `não relevante` deve alimentar avaliações futuras do matching.

---

## 7. Preparação da candidatura

Ao selecionar **Preparar candidatura**:

```text
vaga
+
perfil confirmado
+
currículo base
+
biblioteca de respostas
      ↓
Application Draft
```

### Application Draft

Deve reunir antes do envio:

- currículo recomendado;
- alterações propostas no currículo;
- carta, se necessária;
- respostas do formulário conhecidas;
- respostas abertas propostas;
- perguntas ainda sem resposta;
- possíveis riscos/ambiguidades;
- dados que exigem confirmação.

### Currículo adaptado

O sistema pode reordenar, resumir e destacar fatos existentes.

Não pode adicionar fatos inexistentes.

Toda frase nova que represente experiência deve conseguir apontar para fatos do perfil que a sustentam.

---

## 8. Fluxo de candidatura do piloto

O primeiro modo operacional será **assistido**.

```text
HireIn prepara
      ↓
usuário revisa
      ↓
HireIn abre/preenche
      ↓
usuário confere etapa final
      ↓
usuário envia
      ↓
HireIn registra confirmação
```

### Por que este modo vem primeiro

Antes de confiar ao sistema o `submit`, precisamos medir:

- qualidade das respostas;
- estabilidade de preenchimento;
- comportamento em diferentes ATS;
- tratamento de campos inesperados;
- taxa de erros;
- capacidade de reconhecer conclusão;
- capacidade de interromper sem corromper o processo.

---

## 9. Pergunta desconhecida durante a candidatura

Quando o formulário contiver algo não respondível com fatos existentes:

```text
pergunta detectada
      ↓
existe resposta confirmada?
  ├─ sim → reutilizar
  └─ não
       ↓
é possível elaborar sem inventar fato?
  ├─ sim → AI_DRAFT → pedir revisão
  └─ não → NEEDS_USER_INPUT
```

O agente deve pausar quando a resposta depender de decisão pessoal, fato não cadastrado ou informação sensível.

---

## 10. CAPTCHA, bloqueio ou proteção da plataforma

Fluxo obrigatório:

```text
proteção detectada
      ↓
PAUSED_FOR_USER
      ↓
usuário assume
      ↓
fluxo pode continuar depois
```

O produto **não terá como requisito** mascarar automação, falsificar fingerprint, resolver CAPTCHA por terceiros ou contornar controles técnicos da plataforma.

Se determinado portal não permitir uma automação confiável, o HireIn deve oferecer preenchimento assistido ou redirecionar ao processo manual.

---

## 11. Estados da candidatura

Estados iniciais sugeridos:

```text
DRAFT
READY_FOR_REVIEW
APPROVED
APPLYING
WAITING_USER
SUBMITTED
CONFIRMED
FAILED
WITHDRAWN
REJECTED
ASSESSMENT
INTERVIEW
OFFER
HIRED
```

### Regras

- transições devem gerar eventos;
- uma falha técnica não pode ser confundida com rejeição;
- `SUBMITTED` significa que houve ação de envio;
- `CONFIRMED` significa que existe evidência suficiente de recebimento;
- estados devem guardar data/hora e origem da mudança.

---

## 12. Evidência de candidatura

Quando possível, o HireIn deve guardar evidências leves do envio:

- URL final;
- texto/identificador de confirmação;
- timestamp;
- ATS;
- versão do currículo;
- respostas enviadas;
- versão do adapter;
- identificador da execução.

No piloto, screenshots podem ser usados para depuração, mas não devem virar retenção indiscriminada de páginas contendo dados pessoais.

---

## 13. Acompanhamento

O HireIn deve oferecer uma visão de pipeline:

```text
Preparando
Candidatado
Confirmado
Assessment
Entrevista
Proposta
Encerrado
```

Cada candidatura deve manter a linha do tempo de eventos.

### Atualização de status

No piloto, pode acontecer por:

- ação manual do usuário;
- confirmação observada no ATS;
- importação de e-mail em fase posterior.

Integração automática de e-mail não é requisito para validar o primeiro ciclo.

---

## 14. Feedback e aprendizado

O sistema deve guardar sinais explícitos:

```text
LIKE_MATCH
DISLIKE_MATCH
SAVE_JOB
IGNORE_JOB
APPLY
REJECTED
INTERVIEW
OFFER
```

Inicialmente esses sinais servem para **análise**, não para treinar silenciosamente um modelo personalizado.

O algoritmo somente deve mudar pesos automaticamente quando houver volume suficiente e uma estratégia de avaliação que demonstre melhora.

---

## 15. Métricas do piloto

### Qualidade

- precisão percebida das recomendações;
- percentual de vagas recomendadas consideradas realmente relevantes;
- número de blockers corretamente detectados;
- respostas corrigidas antes do envio;
- fatos incorretos gerados: meta **zero**.

### Eficiência

- tempo médio entre abrir vaga e ter candidatura pronta;
- tempo manual economizado;
- campos preenchidos automaticamente;
- perguntas reutilizadas da biblioteca.

### Resultado

- candidaturas relevantes;
- respostas de recrutadores;
- assessments;
- entrevistas;
- propostas.

O número bruto de candidaturas é uma métrica secundária.

---

## 16. Critérios para habilitar Auto Apply futuro

O envio sem revisão humana não deve ser consequência de simplesmente implementar um botão.

Antes disso, o piloto deverá demonstrar:

- nenhuma invenção factual em uma amostra significativa;
- baixo índice de correção manual;
- adapters estáveis por ATS;
- identificação consistente de blockers;
- idempotência no envio;
- capacidade de parar em perguntas desconhecidas;
- trilha de auditoria completa;
- política de privacidade e segurança apropriada à abertura para terceiros.

Mesmo após habilitado, Auto Apply deverá respeitar regras explícitas do usuário e limites por plataforma.

---

## 17. Fora do escopo inicial

Não fazem parte do primeiro piloto:

- candidatura massiva;
- múltiplos usuários;
- marketplace de recrutadores;
- app mobile nativo;
- treinamento de modelo próprio;
- scraping irrestrito de qualquer portal;
- bypass de CAPTCHA;
- técnicas de evasão de anti-bot;
- cobrança;
- white label;
- automação irreversível sem auditoria.

---

## 18. Fluxo mínimo que valida o produto

Consideraremos que o primeiro ciclo funcional existe quando for possível executar:

```text
1. cadastrar/importar perfil
2. obter uma vaga real
3. normalizar a vaga
4. calcular Match explicável
5. preparar currículo/respostas
6. revisar
7. preencher uma candidatura suportada
8. usuário enviar
9. registrar a candidatura
10. registrar seu resultado posteriormente
```

Tudo que não ajuda diretamente a validar esse ciclo deve disputar prioridade com muita cautela.
