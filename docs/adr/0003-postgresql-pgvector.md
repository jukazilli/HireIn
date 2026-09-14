# ADR-0003 — PostgreSQL + pgvector como camada de dados

- **Status:** Accepted
- **Data:** 2026-09-14
- **Escopo:** persistência transacional, busca relacional e vetorial

## Contexto

O HireIn precisa persistir entidades fortemente relacionais:

- candidato;
- experiências;
- formação;
- competências;
- vagas;
- empresas;
- candidaturas;
- respostas;
- eventos;
- estados de processamento;
- resultados de matching.

Também precisa de busca por similaridade semântica para vagas e competências.

No piloto, operar um banco relacional e um banco vetorial separados aumentaria custo e complexidade sem evidência de necessidade.

## Alternativas consideradas

### PostgreSQL puro sem vetores

Insuficiente para experimentos de matching semântico sem adicionar outra solução posteriormente.

### PostgreSQL + pgvector

Permite combinar:

- dados relacionais;
- filtros SQL;
- transações;
- vetores;
- busca por similaridade;
- índices vetoriais quando necessários.

### Banco vetorial dedicado

Exemplos: Qdrant, Pinecone, Weaviate.

Podem oferecer vantagens em escala e recursos especializados, mas adicionariam:

- outro serviço;
- sincronização entre bancos;
- custo operacional;
- maior superfície de falha;
- possível custo financeiro.

### Elasticsearch/OpenSearch

Poderosos para busca textual e analytics, mas excessivos para o estágio atual e não substituem nossa necessidade transacional.

## Decisão

Adotar **PostgreSQL como fonte principal de verdade** e **pgvector** para embeddings no piloto.

No ambiente remoto inicial, utilizar PostgreSQL gerenciado compatível com pgvector, mantendo SQL e schema portáveis.

## Consequências positivas

- uma única fonte de verdade;
- transações consistentes;
- filtros relacionais combinados com similaridade;
- baixo custo operacional;
- portabilidade entre provedores PostgreSQL;
- possibilidade de evoluir índices conforme volume real.

## Trade-offs

- pgvector pode não ser a solução ideal para volumes vetoriais muito grandes;
- workloads analíticos e de busca muito específicos podem exigir ferramenta especializada no futuro;
- tuning de índices será necessário conforme o dataset crescer.

## Gatilhos de revisão

Avaliar banco vetorial dedicado apenas se medições mostrarem:

- latência inadequada;
- escala de vetores incompatível;
- necessidade de filtros/recall que pgvector não atenda bem;
- custo operacional menor em solução dedicada;
- necessidade de separar workload transacional do vetorial.

Avaliar mecanismo de busca dedicado se busca textual/facetada se tornar um gargalo real.

## Regra

Não introduzir nova tecnologia de dados para resolver um problema ainda não medido.
