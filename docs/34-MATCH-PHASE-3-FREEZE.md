# Match — Holdout final #7 e congelamento da Fase 3

- Data: 2026-09-20
- Status: `FROZEN`
- Baseline funcional do Match: `07271119e05895d21e62736bb2379bb33270239a`
- Escopo: Professional Fit determinístico + confidence-aware ranking + Evidence Resolver + Job Quality Gate
- Próxima fase: Fase 4 — Application Studio

## Objetivo

Executar o último holdout cego previsto pelo Match v1.14 e decidir se ainda existe evidência de erro estrutural que justifique nova calibração do Professional Fit.

O gate segue os critérios definidos em `33-MATCH-V1-14-JOB-QUALITY-GATE.md`:

1. não alterar pesos durante o holdout;
2. capturar Match inicial somente depois da avaliação humana;
3. validar o Job Quality Gate;
4. enriquecer evidências sem inventar fatos profissionais;
5. classificar divergências pela origem;
6. congelar o Match se o erro dominante não for `RANKING_WEIGHT`.

## Protocolo

O lote foi mantido cego até a conclusão das avaliações humanas.

As cinco vagas inéditas finais foram:

| Empresa | Vaga | Fit humano | Apply Intent | Blocker |
| --- | --- | ---: | ---: | --- |
| Asaas | Analista Funcional Sênior de Sistema Financeiro (ERP) | 1 | 1 | não |
| Nasajon | Product Manager — Folha de Pagamento | 2 | 3 | não |
| Squid | Engenheiro de Dados Pleno (Engenheiro de Dados II) | 1 | 0 | não |
| Saque e Pague | Analista de Processos I | 2 | 2 | não |
| Tempo | Analista de Projetos Pleno | 2 | 3 | sim |

A avaliação da Tempo foi inicialmente registrada sem blocker. Depois do snapshot inicial, o usuário confirmou que poderia ter esquecido essa marcação. A checagem das preferências estruturadas mostrou que a vaga exige presença de segunda a quinta enquanto o perfil aceita Joinville/SC, Santa Catarina ou remoto Brasil, sem mudança e sem viagens. O rótulo humano foi corrigido para blocker real.

## Snapshot inicial

Nenhuma Evidence Resolution existia para estas vagas no momento da captura.

| Vaga | Score observado | Cobertura | Ranking | Faixa | UNKNOWNs | Job quality |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Asaas | 100 | 32% | 66 | 32–100 | 12 | OK |
| Saque e Pague | 100 | 26% | 63 | 26–100 | 11 | OK |
| Tempo | 67 | 27% | 55 | 18–91 | 8 | OK |
| Nasajon | 100 | 8% | 54 | 8–100 | 17 | OK |
| Squid | 100 | 7% | 54 | 7–100 | 16 | OK |

Cobertura média inicial: **20,0%**.

UNKNOWNs iniciais: **64**.

O NDCG@5 inicial foi aproximadamente **0,842**.

O confidence-aware ranking funcionou como planejado: scores observados de 100 com pouca evidência não foram tratados como certeza de 100 no ranking.

## Evidence Resolution

O usuário autorizou a execução assistida do enriquecimento porque o Candidate Core já possuía histórico amplo de fatos `USER_CONFIRMED` e respostas humanas anteriores.

Foram persistidas **59 resoluções**:

- 16 `CONFIRMED`;
- 3 `PARTIAL`;
- 34 `NOT_HAVE`;
- 6 `UNSURE`.

Somente evidências previamente confirmadas ou respostas humanas anteriores foram reutilizadas. Ausência de evidência não foi convertida automaticamente em experiência.

Os 6 `UNSURE` permaneceram UNKNOWN. Outros 5 UNKNOWNs dependem de dados estruturados/profile-only e não podem ser resolvidos pelo Evidence Resolver simples.

Resultado:

- UNKNOWNs: **64 → 11**;
- cobertura média: **20,0% → 87,2%**.

## Defeito encontrado durante o holdout

Antes do congelamento foi detectado um falso positivo real na Nasajon.

Requisito:

```text
Construção e priorização de roadmap de produto
```

O parser atômico não preservava corretamente o complemento compartilhado. Isso permitia que evidências de contextos diferentes, como construção de processos To-Be e priorização de backlog/projetos, fossem combinadas para produzir `MATCHED`.

Classificação:

```text
SEMANTIC_EQUIVALENCE / ATOMIC_CONTEXT_LOSS
```

A correção foi implementada no PR #60.

O parser agora preserva:

```text
Construção de roadmap de produto
priorização de roadmap de produto
```

sem elevar globalmente o limite conservador de tamanho dos átomos.

Validação do PR #60:

- `python`: success;
- `web`: success;
- `contract`: success;
- `e2e`: success;
- Vercel preview: success.

Commit de produção:

```text
07271119e05895d21e62736bb2379bb33270239a
```

Depois da correção, o requisito de roadmap passou corretamente de falso `MATCHED` para `GAP`.

## Snapshot enriquecido final

| Vaga | Fit humano | Score | Cobertura | Ranking | Faixa | UNKNOWNs | Job quality |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Asaas | 1 | 79 | 89% | 76 | 71–82 | 2 | OK |
| Saque e Pague | 2 | 50 | 97% | 50 | 48–52 | 1 | OK |
| Tempo | 2 | 50 | 73% | 50 | 36–64 | 3 | OK |
| Nasajon | 2 | 39 | 87% | 40 | 34–47 | 3 | OK |
| Squid | 1 | 8 | 90% | 12 | 7–17 | 2 | OK |

O NDCG@5 oficial final permanece aproximadamente **0,842**.

Ele não é recalculado removendo casos difíceis; o benchmark continua end-to-end.

## Análise das divergências

### Squid

A vaga deliberadamente distante caiu de ranking 54 para 12 após o enriquecimento.

O resultado é coerente com o Fit humano 1 e confirma que o Evidence Resolver consegue transformar ausência explicitamente confirmada em GAP sem tratar UNKNOWN como ausência.

### Saque e Pague e Tempo

As duas vagas com Fit humano 2 ficaram em 50.

A Tempo manteve blocker de localização apenas em Opportunity Compatibility, sem contaminar o benchmark de Professional Fit.

### Nasajon

Depois da correção do parser, o ranking caiu de 48 para 40.

A vaga possui vários requisitos centrais de Product Management que foram explicitamente classificados como GAP, incluindo experiência sólida como PM, roadmap, user stories/critérios de aceite e atuação conjunta com Engenharia/Design/Dados.

O falso positivo semântico foi eliminado antes do congelamento.

### Asaas

A Asaas permanece como a principal divergência do lote:

```text
Fit humano = 1
ranking = 76
```

Não foi encontrado um padrão de peso capaz de explicar o caso.

A vaga está estruturada como `SENIOR`, mas o Candidate Core atual não possui uma dimensão objetiva de senioridade profissional do candidato. A senioridade existente no agregado é uma preferência de carreira, e o perfil piloto não possui níveis de senioridade preferidos preenchidos.

A única experiência profissional confirmada no Candidate Core está registrada como:

```text
Analista de Implantação e Suporte
TSC Tecnologia
desde 2023-06
```

Por isso, o matcher consegue reconhecer corretamente os requisitos ERP/fiscal/processos já confirmados, mas não possui dado estruturado autorizado para concluir incompatibilidade de senioridade.

Classificação:

```text
MISSING_PROFILE_EVIDENCE / MISSING_MATCH_DIMENSION
```

e não:

```text
RANKING_WEIGHT
```

Como diagnóstico, retirando somente esse caso de dimensão ausente, as quatro vagas restantes ficam perfeitamente ordenadas pelas classes humanas deste lote. Esse diagnóstico não substitui o NDCG oficial.

## Job Quality Gate

As cinco vagas terminaram com:

```text
job_quality.status = OK
rankable = true
```

Nenhum novo caso `BAD_JOB_NORMALIZATION` apareceu.

## Volume do benchmark

Ao final deste gate, o banco possui:

- **84** vagas com label de Professional Fit;
- **84** labels de blocker;
- **44** labels de Apply Intent.

O projeto já ultrapassa o mínimo de 30–50 labels previsto no Match v1.12/v1.13.

## Taxonomia final do holdout

| Categoria | Resultado |
| --- | --- |
| `RANKING_WEIGHT` | nenhum novo padrão identificado |
| `SEMANTIC_EQUIVALENCE` | 1 caso real, corrigido no PR #60 |
| `BAD_JOB_NORMALIZATION` | 0 neste lote |
| `MISSING_PROFILE_EVIDENCE / MISSING_MATCH_DIMENSION` | Asaas / senioridade |
| `OPPORTUNITY_COMPATIBILITY` | Tempo / localização, funcionando como esperado |

## Decisão

**A Fase 3 está encerrada e o Match determinístico está congelado.**

O congelamento significa:

1. pesos REQUIRED/PREFERRED não devem ser recalibrados sem novo benchmark explícito;
2. regras de Match não devem ser ajustadas para corrigir uma vaga isolada;
3. novas mudanças no matcher exigem regressão contra o dataset rotulado;
4. Professional Fit continua separado de Opportunity Compatibility e Apply Intent;
5. o commit `07271119e05895d21e62736bb2379bb33270239a` é a baseline funcional congelada;
6. a ausência de senioridade profissional estruturada deve permanecer registrada como limitação conhecida, não ser compensada por inferência;
7. embeddings e LLM continuam fora do scorer determinístico até benchmark próprio justificar sua entrada.

## Próximo marco

O roadmap avança para:

# Fase 4 — Application Studio

A próxima implementação deve trabalhar sobre o Match congelado, começando pela geração controlada de Application Drafts com:

- seleção apenas de fatos existentes no Candidate Core;
- tailoring sem invenção;
- explicação de quais fatos foram usados;
- revisão humana obrigatória;
- nenhuma aplicação irrestrita automática nesta etapa.
