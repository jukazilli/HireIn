# ADR-0001 — Frontend com SvelteKit + TypeScript

- **Status:** Accepted
- **Data:** 2026-09-14
- **Escopo:** interface web do HireIn

## Contexto

O HireIn terá um backend principal em Python para matching, parsing, IA, workers e automação. Portanto, o frontend não precisa assumir também o papel de backend principal.

A interface precisa ser:

- rápida;
- simples de manter;
- adequada para aplicações ricas em formulários e estados;
- compatível com futura extensão de navegador;
- com baixo custo de hospedagem;
- fortemente tipada.

## Alternativas consideradas

### Next.js + React

Vantagens:

- ecossistema muito amplo;
- grande disponibilidade de bibliotecas;
- bom suporte comercial e de hosting;
- alta familiaridade do mercado.

Desvantagens para o HireIn:

- parte relevante do valor do Next está em seu modelo full-stack, enquanto o núcleo do produto estará em Python;
- adicionaria uma segunda camada backend sem necessidade imediata;
- maior superfície conceitual para um piloto pequeno;
- risco de acoplamento entre decisões de UI e infraestrutura da aplicação.

### Nuxt + Vue

Boa alternativa e tecnicamente adequada, mas não demonstrou vantagem concreta sobre SvelteKit para o escopo atual.

### SvelteKit

Vantagens:

- modelo de componentes enxuto;
- boa ergonomia para aplicações orientadas a estado;
- TypeScript;
- SSR/SPA/prerender disponíveis quando necessário;
- adapters para diferentes ambientes;
- integração futura coerente com WXT/Svelte na extensão;
- baixo overhead conceitual para uma UI que não precisa ser o backend central.

## Decisão

Adotar **SvelteKit + TypeScript** para a aplicação web.

O frontend será cliente da API FastAPI. Regras de negócio centrais não devem ser duplicadas no SvelteKit.

## Consequências positivas

- separação clara entre interface e core;
- menor duplicação de responsabilidades;
- tipagem no frontend;
- possibilidade de compartilhar componentes/conhecimento com a futura extensão;
- liberdade de hospedar a UI separadamente do core.

## Trade-offs

- ecossistema menor que React;
- menor disponibilidade de profissionais no mercado;
- algumas bibliotecas podem exigir integração manual.

Esses trade-offs são aceitáveis no piloto e devem ser avaliados novamente antes de uma expansão significativa da equipe.

## Gatilhos de revisão

Revisar esta decisão se:

- uma dependência essencial do produto não possuir alternativa viável em Svelte;
- a contratação de equipe tornar-se materialmente prejudicada;
- a extensão exigir uma arquitetura incompatível;
- benchmarks reais mostrarem problema relevante de desempenho ou manutenção;
- o frontend passar a precisar assumir responsabilidades que justifiquem outro framework.

## Regra

Não migrar para React/Next apenas por popularidade ou familiaridade.
