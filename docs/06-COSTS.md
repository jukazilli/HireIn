# HireIn — Custos

> **Status:** orçamento arquitetural do piloto  
> **Data de referência:** 13/09/2026  
> **Objetivo:** validar o HireIn com custo recorrente de infraestrutura próximo de **US$ 0**  
> **Documento anterior:** [05 — Infraestrutura](05-INFRASTRUCTURE.md)

---

## 1. Princípio de custo

O HireIn não deve otimizar custo sacrificando qualidade de candidatura, privacidade ou confiabilidade.

Ao mesmo tempo, não faz sentido pagar por escala antes de existir evidência de valor.

A estratégia será:

```text
usar local/free tier
        ↓
medir consumo real
        ↓
pagar somente pelo primeiro gargalo comprovado
        ↓
reavaliar custo por resultado
```

A principal métrica econômica do produto não será “custo por request”.

Será progressivamente:

```text
custo por vaga analisada
custo por candidatura preparada
custo por candidatura enviada
custo por entrevista gerada
```

---

# 2. Meta do P0

## Custo mensal alvo

```text
Infraestrutura fixa: US$ 0
IA paga:             US$ 0 inicialmente
Domínio:             não necessário para validação local
Browser cloud:       US$ 0
Observabilidade:     US$ 0
```

O computador e a conexão já existentes do piloto são tratados como recursos disponíveis, não como infraestrutura contratada pelo produto.

---

# 3. Mapa de custos do piloto

| Componente | Escolha P0 | Custo alvo | Observação |
|---|---|---:|---|
| Repositório | GitHub público | US$ 0 | nunca versionar dados pessoais/segredos |
| Frontend | SvelteKit local | US$ 0 | Cloudflare somente quando necessário |
| API | FastAPI local | US$ 0 | sem servidor 24x7 |
| Browser agent | Playwright local | US$ 0 | usa máquina do piloto |
| Banco | Neon Free | US$ 0 | respeitar limites do plano |
| Vector store | pgvector no PostgreSQL | US$ 0 adicional | sem banco vetorial separado |
| Embeddings | modelo local inicialmente | US$ 0 | benchmark define modelo |
| Object storage | local | US$ 0 | R2 só quando necessário |
| Queue | PostgreSQL | US$ 0 adicional | sem Redis inicialmente |
| Logs | arquivos locais + audit DB | US$ 0 | retenção pequena |
| LLM | local/free tier aceitável | US$ 0 alvo | privacidade e qualidade vêm antes do preço |

---

# 4. Neon

Segundo a documentação consultada para o plano Free, o Neon disponibiliza uma camada suficiente para um piloto pequeno, incluindo aproximadamente:

- 50 CU-hours por projeto/mês;
- 0,5 GB de storage por projeto;
- 5 GB de egress por mês;
- autoscaling/scale-to-zero;
- suporte a pgvector.

Para um único usuário e algumas centenas ou poucos milhares de vagas normalizadas, o limite de storage deverá ser acompanhado, mas não justifica contratar banco pago antecipadamente.

### Como economizar storage

Não salvar indiscriminadamente:

- HTML completo de páginas;
- screenshots permanentes;
- versões duplicadas de descrições;
- embeddings de conteúdo descartado;
- logs extensos dentro do banco.

### Gatilho para plano pago ou migração

- storage se aproximando do limite;
- compute mensal insuficiente;
- necessidade de retenção/backup superior;
- necessidade de SLA;
- beta multiusuário.

---

# 5. Cloudflare Workers

Se o painel for hospedado, o plano Free atual documenta:

- 100.000 requests/dia;
- limite de CPU de 10 ms por invocação Free.

O volume é mais do que suficiente para um painel individual, mas o limite de CPU reforça nossa decisão:

> Cloudflare Workers não será o lugar para matching pesado, Playwright ou pipelines longos do HireIn.

Para frontend estático/prerenderizado e endpoints leves, o custo pode permanecer em US$ 0 no piloto.

O plano pago de Workers possui cobrança mínima/estrutura própria e só deve ser considerado quando houver necessidade concreta.

---

# 6. Cloudflare R2

R2 não é necessário no P0 porque arquivos podem ficar localmente.

Quando precisarmos de storage remoto, a tabela de preços consultada informa free tier mensal de:

- 10 GB-month de storage Standard;
- 1 milhão de operações Class A;
- 10 milhões de operações Class B;
- egress sem cobrança padrão.

Isso é amplo para currículos e documentos de um piloto ou beta pequeno.

### Não usar R2 só porque é gratuito

Adicionar storage remoto também adiciona:

- credenciais;
- política de acesso;
- retenção;
- risco de exposição;
- obrigação de deleção.

Por isso o ganho operacional precisa justificar a mudança.

---

# 7. Embeddings

## Preferência P0: local

Embedding de perfil e vaga pode ser processado localmente.

Vantagens econômicas:

- custo marginal zero;
- reprocessamento de corpus sem cobrança;
- liberdade para benchmark;
- sem custo de API por vaga.

### Custo real a observar

Mesmo sendo “gratuito”, modelos locais usam:

- CPU/GPU;
- RAM;
- tempo.

O benchmark deverá registrar latência e consumo para evitar escolher um modelo pesado cuja experiência seja ruim.

---

# 8. LLM generativo — onde custo pode aparecer primeiro

Este é o componente com maior chance de gerar custo variável antes dos demais.

Tarefas potenciais:

- interpretar requisitos ambíguos;
- gerar explicação do match;
- adaptar currículo;
- responder pergunta aberta;
- extrair dados em casos difíceis.

### Estratégia

Nem toda vaga deve chamar um LLM caro.

Pipeline econômico:

```text
regra determinística
      ↓
embedding / heurística
      ↓
LLM somente quando agrega valor
```

### Exemplo

Não usar LLM para descobrir que:

```text
vaga = presencial em Recife
usuário = somente remoto
```

Isso deve ser resolvido por regra barata e determinística.

---

# 9. Cloudflare Workers AI

A documentação atual informa:

- alocação gratuita de 10.000 neurons por dia;
- cobrança acima disso somente em plano pago;
- Customer Content não é utilizado pela Cloudflare para treinar modelos ou melhorar serviços sem consentimento explícito.

Isso torna Workers AI um candidato interessante para o piloto.

### Porém

**Free não significa aprovado.**

Antes de adotar, precisamos testar:

- português brasileiro;
- extração factual;
- tendência a alucinação;
- structured output;
- qualidade de tailoring;
- latência.

Se não atingir a qualidade necessária, não será escolhido apenas para preservar US$ 0.

---

# 10. Gemini Developer API Free

A página oficial consultada em setembro de 2026 informa que o tier gratuito possui tokens sem custo, porém também indica que conteúdo do Free Tier pode ser usado para melhorar produtos do Google; no tier pago essa indicação muda para conteúdo não utilizado para melhoria.

Por isso:

### Decisão

O Gemini Free **não será a opção padrão para processar currículo, identidade ou dados pessoais do HireIn**.

Pode ser usado em experimentos com:

- dados sintéticos;
- descrições de vaga públicas sem perfil do usuário;
- evals que não contenham informação pessoal.

Isso evita economizar poucos dólares criando uma decisão de privacidade ruim logo no piloto.

---

# 11. Orçamento de contingência para IA

Se nenhuma opção local/gratuita atingir a qualidade necessária, podemos autorizar um pequeno orçamento experimental.

### Envelope sugerido P0

```text
US$ 0/mês — alvo
US$ 5/mês — teto experimental inicial para IA
```

Esse valor é **orçamento interno**, não preço de um fornecedor específico.

Antes de elevar o teto, registrar:

- número de chamadas;
- tokens/units;
- custo por tarefa;
- qualidade comparativa;
- impacto sobre conversão/tempo.

---

# 12. Browser automation em cloud

## P0

```text
US$ 0
```

Playwright roda localmente.

### Por que não contratar browser cloud agora

Browser remoto costuma introduzir cobrança por:

- minuto;
- sessão;
- CPU/RAM;
- proxy;
- storage de sessão.

Além disso, para nosso piloto o navegador local oferece vantagem funcional: sessão real, observabilidade e takeover humano.

Cloud browser só entra quando tivermos um caso que local agent não resolve.

---

# 13. Search engine dedicado

Não usar Algolia, Elasticsearch/OpenSearch ou Meilisearch hospedado inicialmente.

PostgreSQL pode atender:

- filtros;
- full text básico;
- ordenação;
- vetores via pgvector.

### Gatilho

Adicionar engine de busca quando medidas reais indicarem:

- busca textual insuficiente;
- faceting complexo;
- latência problemática;
- catálogo grande o suficiente para justificar outra operação.

Até lá:

```text
custo = US$ 0 adicional
complexidade = menor
```

---

# 14. Redis / queue

Não haverá Redis gerenciado no P0.

PostgreSQL será utilizado para tarefas duráveis simples.

Economizamos:

- um serviço;
- credencial;
- observabilidade;
- custo;
- ponto de falha.

Redis entra somente quando throughput ou coordenação demonstrarem necessidade.

---

# 15. Observabilidade

P0:

```text
structured logs local
+
audit events no PostgreSQL
```

Sem custo.

Não contratar antecipadamente:

- Datadog;
- New Relic;
- Elastic Cloud;
- plataforma de traces paga.

P1/P2 poderão utilizar free tier de error tracking/analytics após análise de privacidade.

---

# 16. E-mail de candidatura

Uma inbox HireIn dedicada é uma ideia de produto válida, mas **não é necessária para provar o primeiro ciclo**.

No P0 o acompanhamento pode ser manual.

Isso evita neste momento:

- domínio;
- provedor de e-mail;
- DNS;
- parsing de inbound;
- segurança de caixa postal;
- retenção de mensagens.

A inbox deve ser avaliada somente depois que matching + candidatura assistida estiverem funcionando.

---

# 17. Domínio

Não comprar domínio é aceitável enquanto o produto roda localmente.

Quando P1 começar, domínio passa a fazer sentido para:

- painel;
- API;
- e-mail futuro;
- identidade do produto.

O custo varia por TLD e registrador e deverá ser cotado no momento da compra, não congelado neste documento.

---

# 18. Cenários de orçamento

## Cenário A — P0 ideal

```text
Neon Free              US$ 0
Local compute           US$ 0 contratado
Playwright              US$ 0
Embeddings local        US$ 0
LLM free/local          US$ 0
Storage local           US$ 0
Observability local     US$ 0
-----------------------------
TOTAL RECORRENTE        US$ 0/mês
```

## Cenário B — P0 com IA paga seletiva

```text
Infraestrutura          US$ 0
IA                      até US$ 5 orçamento
-----------------------------
TETO PLANEJADO          US$ 5/mês
```

## Cenário C — P1 privado hospedado

É plausível manter várias camadas em free tier, mas o orçamento não deve pressupor isso eternamente.

Planejamento inicial:

```text
Web/edge                US$ 0 enquanto dentro do Free
DB                      US$ 0 enquanto dentro do Free
Object storage          US$ 0 enquanto dentro do Free
Agent local             US$ 0 contratado
LLM                     variável
API container           TBD
Domain                  anual / TBD
```

Não escolheremos provedor de container antes de P1 porque preços e free tiers mudam rapidamente.

---

# 19. Gatilhos de gasto

Um serviço pago só deve ser adicionado quando responder claramente a uma destas perguntas:

### Receita/resultado

> Isso aumenta materialmente nossa chance de validar entrevistas/conversão?

### Confiabilidade

> O serviço gratuito/local está causando falhas reais?

### Segurança

> Precisamos pagar para obter controles de segurança adequados antes de abrir a terceiros?

### Escala

> O limite atual foi medido e atingido?

### Operação

> Estamos gastando mais tempo mantendo algo do que custaria usar um serviço gerenciado?

---

# 20. Custos que não devemos esconder

Mesmo no free tier existem custos não financeiros:

- tempo de desenvolvimento;
- manutenção de adapters;
- revisão de candidaturas;
- investigação de mudanças em ATS;
- criação de dataset de eval;
- gestão de prompts;
- compliance futuro.

Para o HireIn, provavelmente o maior custo estrutural no início será **engenharia e manutenção dos fluxos de candidatura**, e não banco de dados.

---

# 21. Controle de custo no código

Cada chamada de IA deve poder registrar:

```text
provider
model
operation
input_units
output_units
estimated_cost
latency
success
```

Isso permite responder:

> Qual feature está gastando dinheiro?

### Budget guards futuros

- limite diário;
- limite mensal;
- limite por usuário;
- modelo barato para classificação;
- modelo forte apenas para tarefas críticas;
- cache de resultados estáveis;
- batching quando suportado.

---

# 22. O que não comprar no piloto

Não contratar agora:

- Kubernetes;
- dedicated vector DB;
- Elastic Cloud;
- Redis Cloud pago;
- browser farm;
- proxies residenciais;
- CAPTCHA solver;
- APM enterprise;
- GPU dedicada;
- CDN paga;
- e-mail transacional de alto volume;
- plano de banco dimensionado para SaaS.

Se uma dessas necessidades aparecer, documentar o problema primeiro.

---

# 23. Referências oficiais de preço/política

Preços e limites mudam. Estes links devem ser reconsultados no momento de qualquer contratação:

- Cloudflare Workers: https://developers.cloudflare.com/workers/platform/pricing/
- Cloudflare R2: https://developers.cloudflare.com/r2/pricing/
- Cloudflare Workers AI: https://developers.cloudflare.com/workers-ai/platform/pricing/
- Cloudflare Workers AI data usage: https://developers.cloudflare.com/workers-ai/platform/data-usage/
- Neon: https://neon.com/pricing
- Gemini Developer API: https://ai.google.dev/gemini-api/docs/pricing

---

## 24. Conclusão

O HireIn deve tentar provar primeiro que consegue **encontrar vagas certas e produzir candidaturas melhores**.

Não precisamos provar que sabemos gastar infraestrutura.

A meta financeira inicial é simples:

> **US$ 0 de custo fixo sempre que tecnicamente sensato; até US$ 5/mês de orçamento experimental para IA somente se a qualidade justificar.**

Quando o piloto mostrar entrevistas e ganho de tempo, passaremos a otimizar custo por resultado e não apenas custo absoluto.
