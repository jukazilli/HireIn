# HireIn — LLM Provider Benchmark Gate

> **Status:** Fase 4 — slice 4.5  
> **Data verificada em:** 23/09/2026  
> **Objetivo:** preparar o primeiro benchmark de Resume Rewriter sem expor dados reais prematuramente  
> **Produção:** nenhum provider selecionado  
> **Auto Submit:** OFF

## 1. Decisão

O HireIn não escolherá um provider de LLM por reputação, preferência pessoal ou benchmark genérico.

A escolha do Resume Rewriter será feita com o harness criado na slice 4.4 e com a mesma tarefa realista, o mesmo schema e o mesmo prompt-base para todos os candidatos.

Primeiro executamos com dados sintéticos. Dados reais só entram depois de um gate explícito de privacidade.

## 2. Candidatos iniciais

Snapshot público em 23/09/2026:

| Provider | Modelo | Papel no benchmark | Entrada / 1M | Saída / 1M |
|---|---|---|---:|---:|
| OpenAI | `gpt-6-luna` | baseline de custo | US$ 0,10 | US$ 0,50 |
| OpenAI | `gpt-6-sol` | qualidade balanceada | US$ 2,00 | US$ 10,00 |
| Anthropic | `claude-sonnet-5` | qualidade balanceada | US$ 2,00 | US$ 10,00 |
| Google | `gemini-3.8-flash` | alternativa custo/qualidade | US$ 0,75* | US$ 3,75* |

`*` preço promocional do Gemini 3.8 Flash até 31/12/2026. O registro versionado em `evals/tailoring/providers.json` guarda a data de verificação e as fontes oficiais.

Nenhum modelo é tratado como favorito.

## 3. Por que não incluir modelos premium nesta primeira rodada

O primeiro benchmark deve descobrir se modelos de custo moderado já passam o gate factual.

Modelos premium só devem entrar se:

- todos os candidatos iniciais falharem no gate humano; ou
- a qualidade adicional puder reduzir de forma material o esforço de edição; ou
- surgir um requisito que os candidatos iniciais não atendam.

Isso evita comparar custo alto antes de sabermos se ele é necessário.

## 4. Requisitos mínimos do provider

Para entrar no benchmark real, o provider precisa oferecer:

- API comercial/paga;
- saída estruturada por schema;
- política pública clara sobre uso de dados;
- possibilidade de desabilitar persistência não necessária ao fluxo;
- uso single-turn sem ferramentas;
- identificação estável do modelo;
- métricas de tokens/uso suficientes para medir custo.

## 5. Gate de privacidade

### Stage A — sintético

Permitido imediatamente.

Usa apenas fixtures versionadas em:

```text
evals/tailoring/fixtures/
```

Não contém:

- nome real;
- e-mail;
- telefone;
- LinkedIn;
- empresa real do candidato;
- currículo real;
- conteúdo do piloto.

Objetivo:

- validar adapters;
- validar schema;
- validar prompt;
- medir parsing;
- medir custo/latência básica;
- garantir que o harness rejeita saída fora da fronteira.

### Stage B — real minimizado

Só pode começar depois de decisão explícita para executar o benchmark com dados reais.

Antes de enviar ao provider:

- remover e-mail;
- remover telefone;
- remover URLs pessoais;
- usar somente claims necessárias para a tarefa;
- não enviar histórico irrelevante;
- não enviar arquivos;
- não habilitar web/search/grounding;
- não habilitar ferramentas;
- não habilitar cache persistente;
- não habilitar estado de conversa;
- preferir `store=false` ou equivalente quando disponível.

O benchmark não necessita de nome real para medir qualidade de reescrita. O nome pode ser substituído por um marcador durante avaliação.

### Stage C — produção

Só depois de:

1. benchmark factual;
2. review humano;
3. avaliação de custo e latência;
4. verificação de data handling;
5. ADR escolhendo provider/modelo;
6. configuração segura de segredo;
7. logs sem conteúdo sensível;
8. mecanismo de desligamento/fallback.

## 6. Política por provider

### OpenAI API

Dados enviados à API não são usados para treinar modelos por padrão, salvo opt-in.

O fluxo inicial deve usar somente endpoint stateless, `store=false`, sem tools/files/search e sem background mode.

Abuse-monitoring logs podem conter conteúdo e, no padrão, podem ser retidos por até 30 dias. Zero Data Retention/Modified Abuse Monitoring depende de elegibilidade e configuração da organização.

### Anthropic API

Dados de produtos comerciais/API não são usados para treinamento por padrão.

Inputs e outputs da API são apagados automaticamente em até 30 dias no padrão, salvo exceções documentadas ou acordo diferente.

ZDR é uma configuração/acordo específico para clientes elegíveis; não deve ser presumido.

O benchmark não usará Files API.

### Gemini Developer API

Para Paid Services, prompts e respostas não são usados para melhorar os produtos do Google.

Mesmo no tier pago, pode existir logging limitado para abuse monitoring.

O tier gratuito não será usado com dados reais, porque a documentação de pricing distingue o free tier como conteúdo que pode ser usado para melhorar produtos e o paid tier como não.

Para perseguir ZDR, o adapter deve respeitar as restrições publicadas e evitar recursos que armazenem estado ou acionem serviços externos.

## 7. Regra de igualdade do benchmark

Na primeira rodada:

- mesmo dataset;
- mesmo `prompt-v1.md`;
- mesmo schema `ResumeRewriteCandidate`;
- mesma língua;
- mesma informação de vaga;
- mesmos `allowed_evidence_ids`;
- sem ferramentas;
- sem busca web;
- sem exemplos específicos por provider;
- uma chamada independente por amostra.

A única adaptação permitida é a tradução mecânica do schema para a API de structured output de cada provider.

Provider-specific prompting só pode ser testado em uma rodada posterior e deve ganhar nova `prompt_version`.

## 8. Dados registrados por execução

Registrar fora do Git quando houver dados reais:

```text
run_id
sample_id
provider
model
prompt_version
started_at
latency_ms
input_tokens
output_tokens
reasoning_tokens (quando exposto)
estimated_cost_usd
raw_schema_valid
structural_pass
evidence_coverage
average_anchor_overlap
human_review
```

Não registrar prompt completo com PII em logs de aplicação.

## 9. Critério de entrada na shortlist

Um candidato só permanece na shortlist se:

```text
schema válido
AND structural_pass = true
AND factual_precision = 5/5
AND unsupported_claims = 0
AND pt_br_quality >= 4/5
AND usefulness >= 4/5
```

Custo e latência desempacam candidatos que já passaram qualidade/factualidade; não compensam erro factual.

## 10. Regra de seleção

O sistema não calcula automaticamente um "vencedor".

A escolha final considera:

- factualidade;
- edição humana necessária;
- utilidade;
- estabilidade entre amostras;
- custo;
- latência;
- data handling;
- disponibilidade operacional.

A conclusão é registrada em ADR substituindo o ADR-0006.

## 11. Fontes oficiais usadas no snapshot

OpenAI:

- https://developers.openai.com/api/docs/changelog
- https://developers.openai.com/api/docs/pricing
- https://developers.openai.com/api/docs/models/gpt-6-luna
- https://platform.openai.com/docs/guides/your-data

Anthropic:

- https://www.anthropic.com/news/claude-sonnet-5
- https://privacy.claude.com/en/articles/7996868-is-my-data-used-for-model-training
- https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data

Google:

- https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash
- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/gemini-api/docs/zdr

## 12. Próxima implementação

Depois desta slice:

1. criar adapters de benchmark, não de produção;
2. começar pela fixture sintética;
3. registrar custo/latência;
4. confirmar que todos retornam `ResumeRewriteCandidate`;
5. rodar o harness;
6. só então decidir se o benchmark deve avançar para dados reais minimizados.

Até a conclusão:

```text
LLM DEFAULT = UNDECIDED
REAL PILOT DATA SENT TO LLM = NO
AUTO SUBMIT = OFF
```
