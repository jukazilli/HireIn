# Job Discovery Strategy — Search, Match, Intent e Ranking

## Status

Direção de produto e arquitetura aceita para a evolução pós-validação do Match v1.5.

O objetivo deste documento é separar responsabilidades que até aqui apareciam de forma implícita no HireIn. O produto não deve depender de um único score para decidir o que procurar, o que combina profissionalmente e o que o usuário deseja.

## 1. Princípio central

O HireIn deve operar em quatro camadas distintas:

```text
Search / Discovery
      ↓
Professional Match
      ↓
Apply Intent
      ↓
Ranking
```

Cada camada responde uma pergunta diferente.

| Camada | Pergunta |
| --- | --- |
| Search / Discovery | Quais vagas vale a pena analisar para esta pessoa? |
| Professional Match | Quanto o perfil profissional atual atende esta vaga? |
| Apply Intent | Quanto esta oportunidade combina com o que a pessoa quer agora? |
| Ranking | Quais oportunidades devem aparecer primeiro? |

Nenhuma dessas dimensões deve ser usada como substituta silenciosa das demais.

## 2. Não construir um catálogo massivo no piloto

O HireIn não começará capturando milhões de vagas indiscriminadamente para depois personalizar um feed.

Isso adicionaria cedo demais:

- crawling em massa;
- alto volume de deduplicação;
- atualização de vagas expiradas;
- indexação distribuída;
- custo de armazenamento e processamento;
- dependência de infraestrutura de busca em escala;
- grande quantidade de oportunidades que nenhum usuário analisaria.

A estratégia continua alinhada ao roadmap: qualidade antes de volume e validação antes de escala.

## 3. Profile-guided retrieval

A descoberta futura será orientada pelo Candidate Core, mas não limitada por correspondência literal de cargo.

O sistema deverá derivar um `Search Profile` a partir de três grupos:

```text
quem a pessoa é hoje
+
para onde quer ir
+
quais condições aceita
```

Entradas esperadas incluem:

- cargos e responsabilidades já exercidos;
- skills e domínios confirmados;
- cargos e áreas desejados;
- senioridade;
- localização e modalidade;
- contrato;
- preferências explícitas;
- transições profissionais desejadas.

O Search Profile não é uma cópia do currículo. Ele é uma representação voltada a recuperação de oportunidades.

## 4. Query Expansion

O motor de busca deve buscar além do título literal.

Exemplo conceitual:

```text
perfil atual:
Analista / Consultor de Implantação ERP

objetivo:
Projetos e Produto
```

O Search Profile pode gerar famílias como:

```text
alta proximidade
- Analista de Implantação
- Consultor de Implantação
- Analista ERP

adjacentes
- Analista de Projetos
- Implementation / Onboarding
- Customer Success técnico

transição desejada
- Product Owner
- Product Manager
- Product Operations
```

O objetivo do retrieval é alto recall: encontrar possibilidades plausíveis sem criar uma bolha profissional estreita.

## 5. Pipeline alvo

```text
Candidate Core
      ↓
Search Profile
      ↓
Query Expansion
      ↓
Search Providers / ATS / fontes permitidas
      ↓
coleta da vaga original
      ↓
normalização
      ↓
deduplicação
      ↓
Candidate Pool
      ↓
Professional Match
      ↓
Apply Intent / preferências
      ↓
Ranking
      ↓
Opportunities
```

O pipeline de ingestão existente continua sendo a fronteira entre descoberta externa e Job Core.

## 6. Professional Match

O Match continua responsável apenas por aderência profissional explicável.

Ele deve medir evidências como:

- experiência;
- competências;
- responsabilidades;
- formação;
- idiomas;
- requisitos obrigatórios;
- senioridade;
- blockers objetivos.

O Match não representa probabilidade de entrevista, contratação ou desejo pessoal de candidatura.

A saída continua separando:

```text
Aderência profissional
Confiança da análise
Blockers
Evidências
Gaps
Unknowns
```

## 7. Apply Intent

Apply Intent é uma dimensão humana diferente do Professional Match.

Pode considerar, por exemplo:

- vontade de atuar naquela função;
- empresa;
- modalidade;
- localização;
- remuneração conhecida;
- momento de carreira;
- interesse em transição;
- preferências pessoais declaradas.

Uma vaga pode ter alto Professional Fit e baixo Apply Intent, ou o inverso.

No piloto, Apply Intent é explicitamente informado pelo usuário. Não existe modelo automático de Intent nesta etapa.

## 8. Ranking futuro

O ranking final não deve ser simplesmente `Match DESC`.

Ele poderá futuramente combinar sinais como:

- Professional Fit;
- confiança;
- blockers;
- Apply Intent / preferências;
- recência;
- qualidade da fonte;
- exploração controlada de oportunidades adjacentes.

Os pesos não devem ser definidos antes de dataset e avaliação próprios.

## 9. Blind Holdout #4

Antes de construir o Search Profile v0, a prioridade continua sendo validar o Match v1.5.

O Holdout #4 será reduzido para 5 vagas inéditas e coletará, antes de revelar o Match:

```text
Professional Fit: 0–4
Apply Intent: 0–4
Blocker real: sim/não
Motivo: texto livre
```

A métrica de Match usa `Professional Fit` como ground truth. `Apply Intent` é analisado separadamente e não altera o score do Match.

## 10. Próximo experimento após o Holdout #4

Se a v1.5 demonstrar qualidade suficiente no conjunto cego, o próximo experimento será `Search Profile v0`.

Escopo inicial proposto:

```text
1 perfil
      ↓
queries expandidas
      ↓
20–50 oportunidades candidatas
      ↓
normalização + deduplicação
      ↓
Match
      ↓
Top 5 para revisão humana
```

A pergunta do experimento será:

> O HireIn consegue encontrar sozinho oportunidades que valem a pena o usuário analisar?

Isso é uma hipótese diferente da qualidade do Match e deve ser medida separadamente.

## 11. Fora do escopo neste momento

- crawler massivo;
- milhões de vagas persistidas;
- feed infinito;
- Elasticsearch/OpenSearch;
- ranking comportamental por ML;
- treinamento de modelo personalizado;
- alteração automática dos pesos a partir de cliques;
- inferência automática de Apply Intent sem avaliação própria;
- automação de candidatura baseada apenas no ranking.
