# Job Discovery Strategy — Search, Fit, Compatibility, Intent e Ranking

## Status

Direção de produto e arquitetura atualizada após o Blind Holdout #4 e a definição do Match v1.6.

O HireIn não deve depender de um único score para decidir o que procurar, o que a pessoa consegue fazer, quais oportunidades são viáveis e em quais vagas ela deseja tentar.

## 1. Princípio central

O HireIn opera em cinco camadas distintas:

```text
Search / Discovery
      ↓
Professional Fit
      ↓
Opportunity Compatibility
      ↓
Apply Intent
      ↓
Ranking / Recommendation
```

| Camada | Pergunta |
| --- | --- |
| Search / Discovery | Quais vagas vale a pena analisar para esta pessoa? |
| Professional Fit | Quanto o perfil profissional atual atende os requisitos da vaga? |
| Opportunity Compatibility | A oportunidade é compatível com localização, modalidade, salário, contrato e demais condições conhecidas? |
| Apply Intent | Quanto a própria pessoa deseja se candidatar? |
| Ranking / Recommendation | Quais oportunidades devem aparecer primeiro e por quê? |

Nenhuma dimensão pode substituir silenciosamente outra.

## 2. Não construir catálogo massivo no piloto

O HireIn não começará capturando milhões de vagas indiscriminadamente para depois personalizar um feed.

Isso adicionaria cedo demais crawling em massa, deduplicação em alto volume, expiração, indexação distribuída e custo operacional sem validar antes a qualidade da descoberta.

A estratégia continua sendo qualidade antes de volume.

## 3. Profile-guided retrieval

A descoberta futura será orientada pelo Candidate Core, sem limitar a busca a correspondência literal de cargo.

O `Search Profile` deriva de:

```text
quem a pessoa é hoje
+
para onde quer ir
+
quais condições aceita
```

Entradas esperadas:

- cargos e responsabilidades exercidos;
- skills e domínios confirmados;
- cargos e áreas desejados;
- transições profissionais desejadas;
- localização e modalidade;
- contrato;
- senioridade desejada;
- preferências explícitas.

O Search Profile é uma representação voltada à recuperação de oportunidades, não uma cópia do currículo.

## 4. Query Expansion

A busca deve considerar famílias de cargos.

Exemplo:

```text
perfil atual:
Analista / Consultor de Implantação ERP

objetivo:
Projetos e Produto
```

Famílias possíveis:

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

O retrieval busca alto recall sem criar uma bolha profissional estreita.

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
Professional Fit
      ↓
Opportunity Compatibility
      ↓
Apply Intent
      ↓
Ranking / Recommendation
      ↓
Opportunities
```

A ingestão existente continua sendo a fronteira entre descoberta externa e Job Core.

## 6. Professional Fit

Professional Fit mede somente aderência profissional explicável.

Pode usar:

- experiência;
- competências;
- responsabilidades;
- formação;
- idiomas;
- ferramentas;
- domínios;
- requisitos obrigatórios e desejáveis;
- evidência quantitativa quando exigida.

A saída mínima é:

```text
score
confidence
band
matched requirements
gaps
unknowns
evidence
```

Professional Fit não deve cair para zero porque a vaga fica em outra cidade, paga abaixo do desejado ou usa modalidade não aceita.

`score` não representa probabilidade de entrevista ou contratação.

## 7. Opportunity Compatibility

Opportunity Compatibility mede condições da oportunidade em relação às preferências e restrições da pessoa.

Inclui, quando houver dados:

- localização;
- modalidade;
- remuneração;
- tipo de contrato;
- senioridade desejada;
- título/carreira alvo;
- blockers objetivos.

A saída mínima é:

```text
score
coverage
blocked
blockers[]
preference results
```

No v1.6, blocker explícito de localização pode tornar `blocked = true`, mas não altera o Professional Fit.

Conflitos de preferência que não são blockers permanecem conflitos, sem impedir a candidatura automaticamente.

## 8. Apply Intent

Apply Intent é informação humana.

Pergunta:

> Quanto eu realmente gostaria de me candidatar?

No piloto, permanece em escala 0–4 e só existe quando informado pelo usuário.

O matcher não deve inferir Apply Intent automaticamente. Uma vaga pode ter:

```text
Professional Fit alto
Opportunity Compatibility baixa
Apply Intent alto
```

ou qualquer outra combinação válida.

## 9. Ranking / Recommendation

O ranking futuro não será simplesmente `score DESC`.

Ele poderá usar separadamente:

- Professional Fit;
- confiança da evidência;
- Opportunity Compatibility;
- blockers;
- Apply Intent;
- recência;
- qualidade da fonte;
- exploração de oportunidades adjacentes.

Pesos de recomendação só serão definidos após dataset próprio. Não serão calibrados para reproduzir um holdout já revelado.

## 10. Blind Holdout #4

O Holdout #4 validou o Match v1.5 antes da introdução da separação estrutural do v1.6.

Resultado público-safe:

- 5 vagas;
- 3 relevantes por Professional Fit >= 3;
- Recall@5 = 100%;
- NDCG@5 = 1,000;
- cobertura média = 15,8%.

O conjunto agora é somente regressão/desenvolvimento.

## 11. Match v1.6

O v1.6 formaliza:

```text
Professional Fit != Opportunity Compatibility != Apply Intent
```

Por compatibilidade, os campos legados `score`, `band`, `requirement_score` e `evaluation_coverage` continuam disponíveis, mas passam a representar Professional Fit.

`preference_score` permanece disponível como alias do score de Opportunity Compatibility.

O contrato novo também expõe objetos explícitos para as duas dimensões algorítmicas.

## 12. Próximo experimento

Depois da regressão técnica do v1.6, o próximo experimento continua sendo `Search Profile v0`:

```text
1 perfil
      ↓
queries expandidas
      ↓
20–50 oportunidades candidatas
      ↓
normalização + deduplicação
      ↓
Professional Fit + Opportunity Compatibility
      ↓
Top 5 para revisão humana
```

Pergunta principal:

> O HireIn consegue encontrar sozinho oportunidades que valem a pena o usuário analisar?

Isso é uma hipótese diferente da qualidade do Match.

## 13. Fora de escopo agora

- crawler massivo;
- milhões de vagas persistidas;
- Elasticsearch/OpenSearch;
- ranking comportamental por ML;
- treinamento de modelo personalizado;
- alteração automática de pesos por cliques;
- inferência automática de Apply Intent;
- candidatura automática baseada apenas no ranking.
