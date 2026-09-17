# ADR-0012 — Profile-guided job discovery

## Status

Accepted

## Contexto

A documentação original do HireIn já separa Candidate Core, Job Core e Match, mas a estratégia futura de descoberta de vagas ainda não estava formalizada.

Duas alternativas extremas foram consideradas:

1. capturar e armazenar um catálogo massivo de vagas antes da personalização;
2. usar o perfil do candidato para executar buscas extremamente estreitas e só recuperar vagas quase idênticas ao histórico atual.

A primeira alternativa aumenta custo e complexidade antes de validar o núcleo do produto. A segunda reduz descoberta e pode impedir transições profissionais desejadas.

Os Blind Holdouts também mostraram que aderência profissional e vontade de candidatura são dimensões diferentes.

## Decisão

O HireIn adotará, quando iniciar o domínio de descoberta automatizada, uma estratégia de `profile-guided retrieval`.

O pipeline conceitual será:

```text
Candidate Core
      ↓
Search Profile
      ↓
Query Expansion
      ↓
Search Providers
      ↓
normalização + deduplicação
      ↓
Candidate Pool
      ↓
Professional Match
      ↓
Apply Intent / preferências
      ↓
Ranking
```

Search, Match, Intent e Ranking são responsabilidades independentes.

### Search

Prioriza recall e encontra possibilidades plausíveis. Usa histórico profissional, objetivos e preferências para orientar queries, mas deve incluir cargos adjacentes e transições desejadas.

### Professional Match

Mede aderência profissional explicável. Não representa vontade de aplicar nem probabilidade de entrevista/contratação.

### Apply Intent

Representa a vontade real do usuário de disputar a oportunidade. No piloto será coletado explicitamente e não será inferido automaticamente.

### Ranking

Decidirá futuramente a ordem de apresentação usando sinais separados. Não será definido como simples ordenação pelo score de Match.

## Consequências positivas

- evita crawler massivo antes de haver necessidade;
- preserva descoberta de oportunidades adjacentes;
- mantém responsabilidades de domínio claras;
- permite medir Search e Match separadamente;
- reduz o risco de confundir preferência pessoal com capacidade profissional;
- aproveita Candidate Core e Job Core existentes sem remodelagem estrutural.

## Trade-offs

- exige um Search Profile próprio antes de automatizar descoberta;
- query expansion precisará de eval específico;
- o ranking futuro terá mais de uma dimensão e exigirá dataset próprio;
- fontes diferentes continuarão exigindo adapters e normalização.

## Decisões adiadas

Este ADR não define:

- provedor de busca;
- modelo de embeddings;
- quantidade ideal de vagas candidatas;
- pesos do ranking;
- crawler próprio;
- infraestrutura de busca em escala;
- modelo automático de Apply Intent.

Essas decisões dependem de evidência posterior.

## Gate atual

Antes de implementar Search Profile v0, o Match v1.5 será validado no Blind Holdout #4 com 5 vagas inéditas, separando `Professional Fit` de `Apply Intent`.

## Gatilhos de revisão

Revisar esta decisão se dados reais demonstrarem que:

- consultas orientadas pelo perfil têm recall insuficiente;
- fontes acessíveis exigem catálogo central amplo;
- o custo de recuperação on-demand supera materialmente o de indexação central;
- usuários precisam explorar grandes catálogos fora de qualquer perfil;
- outra arquitetura produz melhora mensurável de qualidade e custo.
