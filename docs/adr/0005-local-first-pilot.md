# ADR-0005 — Execução local-first no piloto

- **Status:** Accepted
- **Data:** 2026-09-14
- **Escopo:** execução do piloto individual

## Contexto

O primeiro usuário do HireIn será o próprio criador do produto. Ainda não há necessidade de operar um SaaS público, autenticação multiusuário ou browser automation em nuvem.

O produto manipulará:

- currículo;
- dados pessoais;
- sessões de ATS;
- respostas de candidatura;
- documentos gerados;
- possivelmente cookies e estados de autenticação.

Enviar tudo isso para infraestrutura remota desde o primeiro dia aumentaria risco, custo e superfície operacional sem provar valor adicional.

## Alternativas consideradas

### Cloud-first desde o início

Vantagens:

- aproxima a arquitetura do futuro SaaS;
- facilita acesso remoto.

Desvantagens:

- autenticação e gestão de secrets antecipadas;
- storage remoto de dados sensíveis;
- custo e observabilidade adicionais;
- browser automation remota mais complexa;
- maior obrigação de segurança antes da validação do produto.

### Local-first

Executar frontend, API, browser agent e arquivos sensíveis localmente, usando somente serviços remotos mínimos quando houver benefício claro.

## Decisão

O piloto será **local-first**.

Inicialmente:

```text
máquina do usuário
├── SvelteKit
├── FastAPI
├── Playwright
├── arquivos temporários
├── browser/session state
└── logs locais higienizados

serviços remotos mínimos
└── PostgreSQL gerenciado gratuito, quando necessário
```

Sempre que for razoável, documentos e credenciais devem permanecer locais.

## Consequências positivas

- menor exposição de dados;
- custo inicial próximo de zero;
- debugging direto;
- possibilidade de observar o agente operando;
- evita construir prematuramente autenticação, tenancy e secret management distribuído.

## Trade-offs

- aplicação não estará disponível 24/7;
- automações dependem da máquina ligada;
- experiência ainda não representa um SaaS público;
- transição futura para infraestrutura remota exigirá trabalho arquitetural adicional.

## Gatilhos de revisão

Migrar componentes para cloud quando houver uma razão concreta, como:

- necessidade de execução agendada com máquina desligada;
- private beta com terceiros;
- sincronização entre dispositivos;
- necessidade de inbox contínua;
- processamento pesado incompatível com a máquina local;
- requisito de disponibilidade permanente.

## Regra

A futura migração para cloud deve acontecer componente por componente, não por uma reescrita completa sem necessidade.
