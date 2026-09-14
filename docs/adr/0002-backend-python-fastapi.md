# ADR-0002 — Core backend com Python + FastAPI

- **Status:** Accepted
- **Data:** 2026-09-14
- **Escopo:** API, matching, IA, parsing, workers e orquestração principal

## Contexto

O HireIn depende de capacidades que se concentram fortemente no ecossistema Python:

- NLP;
- embeddings;
- parsing de documentos;
- avaliações de modelos;
- automação com Playwright;
- processamento assíncrono;
- pipelines de IA;
- experimentação local.

O backend precisa expor contratos claros para a interface e permitir crescimento gradual sem exigir microserviços no início.

## Alternativas consideradas

### Node.js / NestJS

Vantagens:

- excelente tipagem com TypeScript;
- ecossistema web maduro;
- arquitetura modular clara.

Desvantagens:

- criaria uma fronteira adicional entre o backend web e os componentes de IA/Python;
- poderia exigir workers Python separados precocemente;
- aumentaria a complexidade operacional do piloto.

### Django

Vantagens:

- extremamente maduro;
- ORM e admin fortes;
- bom para sistemas CRUD complexos.

Desvantagens para o piloto:

- mais estrutura do que o core atual necessita;
- o admin não é um requisito relevante;
- FastAPI oferece uma fronteira de API mais direta para nosso desenho.

### FastAPI

Vantagens:

- integração natural com Pydantic;
- geração de OpenAPI;
- suporte a async;
- tipagem explícita;
- bom encaixe com serviços de IA e automação em Python;
- reduz necessidade de manter uma segunda stack de backend.

## Decisão

Adotar **Python + FastAPI** como core backend do HireIn.

O projeto deve começar como um **modular monolith**, e não como microserviços.

Domínios devem permanecer separados internamente, por exemplo:

```text
candidate
jobs
matching
applications
ai
browser
tracking
```

## Consequências positivas

- uma linguagem principal para core, IA e automação;
- menor custo operacional;
- experimentação mais rápida de modelos;
- contratos OpenAPI nativos;
- menos fronteiras de rede no piloto.

## Trade-offs

- Python não possui o mesmo desempenho bruto de linguagens compiladas em determinadas cargas;
- disciplina arquitetural será necessária para impedir que o monólito vire um conjunto acoplado de scripts;
- tarefas CPU-heavy poderão futuramente exigir processos/workers dedicados.

## Gatilhos de revisão

Revisar se:

- throughput medido se tornar incompatível com Python;
- uma parte do produto exigir isolamento operacional real;
- a equipe crescer e fronteiras organizacionais justificarem serviços separados;
- o browser agent precisar escalar independentemente;
- requisitos de latência justificarem implementação especializada.

## Regra

Não criar microserviços antes de existir uma necessidade operacional mensurável.
