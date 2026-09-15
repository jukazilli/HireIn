# ADR-0005 — Execução local-first no piloto

- **Status:** Superseded by ADR-0009
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

## Decisão original

O piloto foi inicialmente definido como **local-first**.

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

## Por que foi substituída

Durante a preparação do piloto real surgiu uma restrição concreta: a máquina do piloto não possui espaço disponível suficiente para manter Docker, PostgreSQL e a toolchain local sem atrito operacional.

Forçar a execução local passou a impedir a própria validação do produto. Esse é um dos tipos de evidência que justificam rever uma decisão arquitetural.

A execução ativa do piloto passa a seguir o [ADR-0009](0009-private-cloud-single-user-pilot.md), preservando o mesmo core e movendo apenas o runtime necessário para a nuvem.

## Consequências históricas positivas

A decisão local-first ajudou a:

- minimizar exposição prematura de dados;
- provar o core antes de criar autenticação;
- validar frontend, FastAPI, PostgreSQL, migrations, OpenAPI e E2E antes do hosting remoto;
- evitar uma reescrita orientada ao provedor.

## Regra preservada

Mesmo após o ADR-0009, a migração para cloud continua acontecendo componente por componente. Browser automation, storage de documentos e autenticação multiusuário não entram automaticamente apenas porque web/API/banco foram hospedados.
