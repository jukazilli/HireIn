# HireIn — Synthetic Live LLM Benchmark Runner

> **Status:** Fase 4 — slice 4.7  
> **Objetivo:** permitir chamadas reais somente contra fixtures sintéticas  
> **Dados reais do piloto:** proibidos  
> **Execução externa nesta implementação:** não realizada  
> **Prompt:** `v2`

## 1. Objetivo

A slice transforma os adapters sintéticos da 4.6 em um runner capaz de executar uma chamada real e mensurável, sem abrir ainda o gate de dados reais.

Fluxo:

```text
fixture sintética
  ↓
ResumeRewriteInput
  ↓
ProviderRequestTemplate
  ↓
secret somente em memória
  ↓
HTTPS provider
  ↓
response codec
  ↓
ResumeRewriteCandidate
  ↓
structural eval
  ↓
relatório local redacted
```

## 2. Travas de execução

O comando não executa rede sem:

```text
--execute-network
```

Também exige pelo menos um candidato explícito:

```text
--candidate provider/model
```

Exemplo:

```bash
uv run --package hirein-api python scripts/provider_benchmark.py \
  --execute-network \
  --candidate openai/gpt-6-luna
```

O runner não escolhe todos os modelos automaticamente.

## 3. Trava de dados

Tanto `--input` quanto `--preview` precisam estar dentro de:

```text
evals/tailoring/fixtures/
```

O runner rejeita caminhos externos a essa árvore.

Consequentemente, esta ferramenta não aceita `.local-data`, Candidate Core real ou currículo real.

## 4. Secrets

Os secrets são lidos somente no momento da execução:

| Provider | Variável |
|---|---|
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Google | `GEMINI_API_KEY` |

Eles:

- não entram no Git;
- não entram em `ProviderRequestTemplate`;
- não entram no relatório;
- não entram em logs;
- existem apenas em memória para compor o header HTTP.

## 5. Transporte

A implementação padrão usa `urllib` da biblioteca padrão.

Isso evita adicionar SDKs ou dependências apenas para o benchmark.

O transporte é definido por uma interface injetável:

```text
JsonTransport.post_json(...)
```

Nos testes, um transporte falso substitui completamente a rede.

## 6. Erros sanitizados

O runner não persiste body de erro retornado pelo provider.

Falhas de rede ou HTTP viram somente códigos genéricos, como:

```text
ProviderTransportError
```

Isso evita que um provider devolva conteúdo do prompt em uma mensagem de erro que depois seja gravada no relatório.

## 7. Métricas

Cada execução registra:

```text
provider
model
prompt_version
status
started_at
latency_ms
input_tokens
cached_input_tokens
output_tokens
reasoning_tokens
billable_output_tokens
estimated_uncached_equivalent_cost_usd
cache_observed
schema_valid
structural_pass
evidence_coverage
average_anchor_overlap
candidate
error_code
```

O relatório não guarda:

- request autenticado;
- prompt completo;
- secret;
- headers;
- resposta bruta do provider.

Como esta fase aceita apenas dados sintéticos, o `candidate` pode ser persistido para comparação.

## 8. Tokens de raciocínio

### OpenAI

`usage.output_tokens` já inclui tokens gerados pelo modelo; `reasoning_tokens` é uma decomposição observacional.

O custo usa `output_tokens` uma única vez.

### Anthropic

A documentação informa que `output_tokens` é o total autoritativo para billing e inclui thinking tokens.

O custo usa `output_tokens` uma única vez.

### Gemini

A Interactions API reporta separadamente:

```text
total_output_tokens
total_thought_tokens
```

A tabela de preços do Gemini 3.8 Flash informa que output pricing inclui thinking tokens.

Assim:

```text
billable_output_tokens =
  total_output_tokens + total_thought_tokens
```

## 9. Custo

A métrica chama-se:

```text
estimated_uncached_equivalent_cost_usd
```

Ela usa as tarifas padrão versionadas no registry e trata todos os tokens de entrada pela tarifa cheia.

Ela não é apresentada como valor faturado porque cache pode alterar pricing.

O runner registra `cached_input_tokens` e `cache_observed` separadamente.

## 10. Correção do gate de cache

A regra antiga:

```text
provider_caching_disabled = true
```

foi removida.

Ela era tecnicamente forte demais.

A documentação atual da OpenAI informa que Prompt Caching está habilitado por padrão nos modelos suportados. Em GPT-5.6+ o TTL mínimo documentado é 30 minutos.

A regra passa a ser:

```text
provider_cache_not_explicitly_enabled = true
provider_cache_behavior_must_be_recorded = true
```

Cada candidato agora possui `cache_behavior_note`.

O HireIn não habilita cache por conta própria, mas também não afirma controlar defaults que pertencem ao provider.

## 11. Fontes verificadas em 23/09/2026

OpenAI:

- https://developers.openai.com/api/docs/guides/prompt-caching
- https://developers.openai.com/api/reference/cli/resources/responses/methods/create
- https://developers.openai.com/api/docs/guides/reasoning

Anthropic:

- https://platform.claude.com/docs/en/api/typescript/messages

Google:

- https://ai.google.dev/gemini-api/docs/pricing
- https://ai.google.dev/api/interactions-api-v1

## 12. Próximo passo operacional

O código está pronto para a primeira execução sintética paga, mas ela depende de credenciais válidas fornecidas fora do repositório.

A sequência correta é:

1. configurar uma credencial comercial de um provider;
2. executar um único candidato sintético;
3. revisar o relatório;
4. confirmar schema, structural pass, tokens, latência e custo;
5. repetir para os demais candidatos;
6. comparar sem declarar vencedor automaticamente.

Somente depois disso faz sentido discutir Stage B com dados reais minimizados.

```text
LLM DEFAULT = UNDECIDED
REAL PILOT DATA SENT TO LLM = NO
AUTO SUBMIT = OFF
```
