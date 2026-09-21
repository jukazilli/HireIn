# Match v1.14 — Holdout final e congelamento da Fase 3

## Status

**FASE 3 CONCLUÍDA — NÚCLEO DETERMINÍSTICO CONGELADO**

Baseline de código congelada: 6961713ae95c874986ddc83ac3a949b5c452737a.

O congelamento significa que o Match determinístico não deve receber novos ajustes de pesos, aliases, pontes semânticas ou regras específicas sem que um novo benchmark demonstre uma falha mensurável. Ele não significa perfeição: as limitações restantes deste gate foram classificadas como incerteza/cobertura de evidência, não como padrão de erro de pesos.

## 1. Holdout final

| Empresa | Vaga | Fit humano | Apply Intent | Blocker real |
| --- | --- | ---: | ---: | --- |
| Asaas | Analista Funcional Sênior de Sistema Financeiro (ERP) | 1 | 1 | não |
| Nasajon | Product Manager — Folha de Pagamento | 2 | 3 | não |
| Squid | Engenheiro de Dados Pleno | 1 | 0 | não |
| Saque e Pague | Analista de Processos I | 2 | 2 | não |
| Tempo | Analista de Projetos Pleno | 2 | 3 | sim — LOCATION |

O blocker da Tempo foi corrigido após revisão: a vaga exige presença de segunda a quinta e isso conflita com as preferências de localização confirmadas do piloto. Opportunity Compatibility e Apply Intent permanecem fora do benchmark de Professional Fit.

## 2. Snapshot inicial cego

| Empresa | Fit humano | Score | Cobertura | Faixa |
| --- | ---: | ---: | ---: | --- |
| Asaas | 1 | 66 | 32% | 32–100 |
| Saque e Pague | 2 | 63 | 26% | 26–100 |
| Tempo | 2 | 55 | 27% | 18–91 |
| Nasajon | 2 | 54 | 8% | 8–100 |
| Squid | 1 | 54 | 7% | 7–100 |

## 3. Evidence Resolution final

Foram persistidas 59 resoluções para os cinco jobs:

- 13 CONFIRMED;
- 3 PARTIAL;
- 34 NOT_HAVE;
- 9 UNSURE.

Durante a auditoria, três confirmações inicialmente feitas pela execução assistida foram consideradas fortes demais e rebaixadas para UNSURE:

- validação de configurações, parametrizações e desenho funcional de ERP;
- modelagem de processos financeiros e integrações bancárias;
- NF-e e SPED Fiscal/Contribuições.

Os fatos derivados dessas três confirmações foram removidos do Candidate Core. Isso preserva a regra de que ausência de prova não é GAP e IA não transforma experiência relacionada em fato profissional específico.

## 4. Defeitos encontrados e corrigidos

### PR #60 — contexto compartilhado no parser atômico

“Construção e priorização de roadmap de produto” podia ser quebrado em conceitos genéricos e combinar evidências de contextos distintos. A correção preserva “Construção de roadmap de produto” e “priorização de roadmap de produto”.

### PR #61 — especificidade de evidência

Evidências amplas como “ERP” podiam satisfazer requisitos muito específicos como “ERP financeiro: GL, AP e AR”. Pontes conceituais também podiam ignorar qualificadores explícitos como “BBP, configuração e UAT”.

A correção exige evidência pelo menos tão específica quanto o requisito e impede pontes genéricas de satisfazer listas qualificadoras compostas. Nenhuma dessas correções alterou pesos.

## 5. Snapshot final

| Empresa | Fit humano | Score | Cobertura | Ranking | Faixa | Band | Quality |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| Asaas | 1 | 56 | 42% | 53 | 24–82 | INSUFFICIENT_DATA | OK |
| Tempo | 2 | 50 | 73% | 50 | 36–64 | PARTIAL | OK |
| Saque e Pague | 2 | 42 | 84% | 43 | 35–52 | LOW | OK |
| Nasajon | 2 | 39 | 87% | 40 | 34–47 | LOW | OK |
| Squid | 1 | 8 | 90% | 12 | 7–17 | LOW | OK |

Todas as cinco vagas passaram pelo job_quality com status OK e rankable=true. A Tempo continua corretamente bloqueada apenas em Opportunity Compatibility por LOCATION.

## 6. NDCG e interpretação

O NDCG@5 final permanece aproximadamente 0,842 porque a ordem relativa por label ainda começa com Asaas (Fit humano 1) antes das três vagas Fit 2.

A natureza do resultado, porém, mudou materialmente. Antes da auditoria, Asaas chegou a score 79, cobertura 89%, ranking 76 e band GOOD. Depois das correções terminou em score 56, cobertura 42%, ranking 53 e band INSUFFICIENT_DATA.

O sistema deixou de afirmar alta aderência sustentada por evidência excessivamente ampla. O ranking 53 restante decorre do prior neutro de 50 do Match confidence-aware diante de muita incerteza. A inversão remanescente é classificada como COVERAGE_FAILURE / MISSING_PROFILE_EVIDENCE, não RANKING_WEIGHT.

Não é correto reduzir pesos ou criar penalidade específica apenas para fazer este lote de cinco vagas produzir uma ordem perfeita.

## 7. Decisão do gate

Congelar o núcleo determinístico na baseline 6961713ae95c874986ddc83ac3a949b5c452737a, incluindo:

- regras determinísticas de evidência;
- MATCHED / GAP / UNKNOWN;
- Evidence Resolver;
- atomic evidence e parser semântico determinístico;
- separação Professional Fit / Opportunity Compatibility;
- confidence-aware ranking e faixa floor/ceiling;
- benchmark purity;
- job normalization quality gate.

Não fazer agora:

- recalibrar pesos pelo holdout;
- adicionar penalidade ad hoc para Asaas;
- converter UNKNOWN em GAP;
- adicionar embeddings apenas para melhorar NDCG;
- usar LLM como judge do Match.

## 8. Limitações conhecidas

1. Perfil com evidência estruturada insuficiente pode permanecer próximo do prior neutro no ranking.
2. Senioridade profissional ainda não possui evidência estruturada suficiente para virar penalidade automática de Professional Fit.
3. Requisitos compostos específicos permanecem UNKNOWN quando só existe experiência relacionada.
4. O Candidate Core continuará evoluindo com fatos reais confirmados mesmo com o algoritmo congelado.
5. Uma nova falha repetida e mensurável pode reabrir a Fase 3.

Uma futura mudança no Match deve nascer de novo benchmark, não de ajuste para um caso individual.

## 9. Próximo marco

Com a Fase 3 encerrada, o próximo marco é **FASE 4 — Application Studio**.

Primeira vertical slice:

vaga escolhida → Job Workspace → Candidate Facts confirmados → currículo base → Resume Tailoring v1 → Answer Assistant → revisão humana → candidatura preparada.

AUTO SUBMIT continua fora desta fase.

O Match permanece como infraestrutura de decisão para o Application Studio, mas deixa de ser o centro do ciclo de desenvolvimento até que dados futuros justifiquem sua reabertura.
