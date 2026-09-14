# ADR-0006 — Adiar escolha definitiva de LLM e embeddings

- **Status:** Deferred
- **Data:** 2026-09-14
- **Escopo:** modelos generativos e de embeddings

## Contexto

O HireIn precisa de IA para tarefas diferentes, com requisitos diferentes:

- extração estruturada de currículo;
- normalização de vagas;
- identificação de requisitos obrigatórios;
- matching semântico;
- explicação do match;
- adaptação de currículo;
- respostas abertas;
- classificação de e-mails e eventos futuros.

Escolher um único modelo antes de medir essas tarefas criaria lock-in baseado em reputação ou conveniência, não em evidência.

## Problema

"Qual é o melhor modelo?" não é uma pergunta suficiente.

Precisamos responder:

```text
qual modelo
para qual tarefa
com qual qualidade
com qual latência
com qual custo
com quais garantias de privacidade
```

## Decisão

Não fixar agora um LLM ou embedding model definitivo.

A arquitetura deverá expor interfaces como:

```text
EmbeddingProvider
TextGenerator
StructuredExtractor
StructuredJudge
```

Adapters concretos poderão ser trocados sem alterar domínio ou casos de uso.

## Benchmark de embeddings

Antes da decisão, criar dataset PT-BR usando vagas reais do piloto e avaliar candidatos multilíngues.

Métricas mínimas:

- Recall@K;
- NDCG@K;
- avaliação humana do Top K;
- latência local/remota;
- uso de RAM;
- tamanho do modelo;
- custo por volume;
- capacidade com títulos/cargos brasileiros.

Exemplos de relações que o benchmark deve entender:

```text
Consultor ERP
Analista ERP
Analista de Implantação
Consultor de Implantação
Analista de Sistemas
```

sem assumir equivalência absoluta quando a descrição da vaga demonstrar diferenças.

## Benchmark de LLM

Criar um eval por tarefa.

Critérios:

- fidelidade aos fatos;
- aderência a schema;
- hallucination rate;
- qualidade em PT-BR;
- latência;
- custo;
- política de uso de dados;
- capacidade de execução local quando aplicável.

## Regra de privacidade

Nenhum provider gratuito deve receber dados pessoais reais apenas por ser gratuito.

Antes de enviar dados reais a um provider, revisar:

- política de retenção;
- treinamento com prompts/dados;
- subprocessadores;
- localização/transferência de dados;
- configuração de opt-out quando existir;
- termos aplicáveis à API.

## Consequências positivas

- menor lock-in;
- escolha baseada em evidência;
- possibilidade de usar modelos diferentes por tarefa;
- capacidade de trocar provider por custo, qualidade ou privacidade.

## Trade-offs

- exige camada de abstração;
- exige manutenção de evals;
- pode haver diferenças de comportamento entre providers.

## Gatilho para encerrar este ADR

Criar ADR substituto quando o primeiro benchmark real do piloto produzir evidência suficiente para escolher:

1. embedding default;
2. LLM default por tarefa;
3. fallback, se necessário.
