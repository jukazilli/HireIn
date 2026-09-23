# HireIn — Synthetic Provider Adapters

> **Status:** Fase 4 — slice 4.6  
> **Objetivo:** congelar o formato de requests/responses dos providers antes de qualquer chamada externa  
> **Rede:** desabilitada nesta slice  
> **Dados reais:** proibidos  
> **Prompt ativo do benchmark sintético:** `v2`

## 1. Escopo

Esta slice implementa somente componentes puros:

```text
ResumeRewriteInput
      ↓
provider request builder
      ↓
ProviderRequestTemplate
      ↓
[nenhuma chamada de rede]
      ↓
provider response codec
      ↓
JSON textual
      ↓
parse_provider_output()
      ↓
ResumeRewriteCandidate
```

Não existe cliente HTTP, retry, secret loader ou integração de produção.

## 2. Por que o modelo não gera metadata do benchmark

O schema enviado aos modelos contém somente:

```text
blocks[]
  section
  text
  source_evidence_ids
  target_experience_id
```

Os campos abaixo são injetados depois pelo adapter:

```text
provider
model
prompt_version
```

Isso impede que a própria resposta do modelo altere a identidade do provider/modelo ou a versão do prompt usada no benchmark.

## 3. Schema comum

Todos os providers recebem o mesmo schema lógico.

Cada bloco exige:

- `section`;
- `text`;
- pelo menos uma referência validável depois por Pydantic/harness;
- `target_experience_id`, que pode ser `null` fora de bullets de experiência.

Os objetos usam `additionalProperties: false`.

A validação semântica continua depois do parse:

- IDs precisam ser UUIDs;
- `source_evidence_ids` precisam permanecer dentro de `allowed_evidence_ids`;
- bullets precisam apontar para experiência válida;
- factualidade humana continua obrigatória para escolha de modelo.

## 4. OpenAI adapter

Endpoint previsto:

```text
POST https://api.openai.com/v1/responses
```

Formato:

- `instructions = prompt-v2`;
- `input = ResumeRewriteInput serializado`;
- `store = false`;
- nenhuma ferramenta;
- Structured Outputs em `text.format`;
- `strict = true`.

O codec percorre todo o array `output` e extrai somente blocos:

```text
type = output_text
```

Ele não presume que o texto está no primeiro item do array.

Fonte oficial verificada em 23/09/2026:

- https://developers.openai.com/api/docs/guides/structured-outputs
- https://developers.openai.com/api/docs/guides/text

## 5. Anthropic adapter

Endpoint previsto:

```text
POST https://api.anthropic.com/v1/messages
```

Formato:

- `system = prompt-v2`;
- uma única mensagem `user`;
- nenhuma ferramenta;
- sem cache control;
- Structured Outputs em `output_config.format`.

O codec extrai somente blocos de conteúdo:

```text
type = text
```

Fonte oficial verificada em 23/09/2026:

- https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- https://platform.claude.com/docs/en/api/messages/create

## 6. Gemini adapter

Endpoint previsto:

```text
POST https://generativelanguage.googleapis.com/v1/interactions
```

A Interactions API é a interface recomendada pelo Google para novos projetos desde junho de 2026.

Formato:

- `system_instruction = prompt-v2`;
- `input = ResumeRewriteInput serializado`;
- `store = false`;
- nenhuma ferramenta;
- nenhuma interação anterior;
- Structured Outputs em `response_format`.

O uso explícito de `store=false` é obrigatório porque a Interactions API armazena interações por padrão quando esse campo não é desabilitado.

O codec percorre:

```text
steps[]
  type = model_output
    content[]
      type = text
```

Fontes oficiais verificadas em 23/09/2026:

- https://ai.google.dev/gemini-api/docs/interactions-overview
- https://ai.google.dev/gemini-api/docs/structured-output
- https://ai.google.dev/api/interactions-api-v1

## 7. Prompt v2

O `prompt-v1.md` permanece preservado.

A slice cria `prompt-v2.md` porque o contrato mudou de:

```text
modelo gera ResumeRewriteCandidate inteiro
```

para:

```text
modelo gera apenas blocks
adapter injeta metadata do benchmark
```

Nenhum benchmark real havia sido executado com v1, mas manter o arquivo antigo evita mutação silenciosa de artefatos versionados.

## 8. Dry-run CLI

Comando:

```bash
uv run --package hirein-api python scripts/provider_request_preview.py
```

Saída padrão:

```text
.local-data/evals/tailoring/provider-requests/
├─ openai-gpt-6-luna.json
├─ openai-gpt-6-sol.json
├─ anthropic-claude-sonnet-5.json
└─ google-gemini-3.8-flash.json
```

Os arquivos contêm:

- endpoint;
- nome do header de autenticação esperado;
- body completo e sintético.

Eles não contêm:

- chave;
- token;
- header de autenticação preenchido;
- dado real;
- código capaz de enviar o request.

## 9. Trava contra dados reais

O CLI aceita entrada somente dentro de:

```text
evals/tailoring/fixtures/
```

Qualquer tentativa de apontar `--input` para outro local falha com erro.

Isso significa que a ferramenta desta slice não pode ser usada acidentalmente para preparar um request com o conteúdo de `.local-data`.

## 10. Testes

A suíte valida:

- mesmo schema nos três providers;
- mesmo prompt;
- `store=false` onde o provider suporta estado;
- ausência de tools/search/files/context externo;
- ausência de secrets;
- endpoints esperados;
- metadata injetada após o parse;
- codecs dos três envelopes;
- erro quando a resposta não contém texto;
- quatro previews gerados pelo registry;
- rejeição de input fora das fixtures sintéticas.

## 11. O que continua bloqueado

Ainda não existe:

- SDK de OpenAI;
- SDK de Anthropic;
- SDK de Google;
- cliente HTTP genérico para LLM;
- leitura de `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` ou `GEMINI_API_KEY`;
- chamada de rede;
- benchmark de custo real;
- benchmark de latência real;
- envio do Candidate Core;
- provider default.

## 12. Próximo gate

A próxima slice pode implementar um **benchmark runner externo**, ainda iniciado apenas com fixture sintética.

Antes da primeira chamada paga, precisamos:

1. definir armazenamento local de métricas de execução;
2. garantir redaction de logs;
3. carregar segredos apenas por ambiente;
4. nunca persistir secrets no report;
5. executar uma chamada por provider/modelo;
6. validar schema e structural gate;
7. registrar tokens, latência e custo.

Dados reais continuam separados por um gate posterior.

```text
LLM DEFAULT = UNDECIDED
REAL PILOT DATA SENT TO LLM = NO
AUTO SUBMIT = OFF
```
