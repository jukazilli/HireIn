# HireIn — Matching Eval

Este diretório contém **somente documentação e fixtures sintéticas** do benchmark de Match.

Dados reais do piloto ficam em `.local-data/`, que é ignorado pelo Git.

## Objetivo

Medir se uma alteração no Match melhora ou piora a priorização das vagas antes de adicionar embeddings ou LLM.

A primeira baseline usa:

- relevância humana graduada de `0` a `4`;
- `Recall@5` e `Recall@10`, considerando relevantes as vagas com label `3` ou `4`;
- `NDCG@5` e `NDCG@10`, preservando toda a escala `0–4`;
- cobertura média da avaliação;
- quantidade de vagas que receberam score.

## Estrutura local

Crie somente na sua máquina:

```text
.local-data/
├─ jobs/
│  ├─ vaga-001.json
│  ├─ vaga-002.json
│  └─ ...
└─ evals/
   ├─ matching-labels.json
   ├─ import-manifest.json       # gerado pelo CLI
   ├─ matching-report.json       # gerado pelo CLI
   └─ matching-report.md         # gerado pelo CLI
```

Nada dentro de `.local-data/` deve ser commitado.

## Arquivo de vaga

Cada arquivo em `.local-data/jobs/*.json` usa exatamente o payload aceito por `POST /api/v1/jobs`.

Exemplo sintético:

```json
{
  "source_kind": "MANUAL",
  "company_name": "Empresa Fictícia",
  "title": "Analista de Implantação ERP",
  "location_text": "Cidade Exemplo - SC",
  "work_model": "REMOTE",
  "contract_type": "CLT",
  "seniority": "MID",
  "description_raw": "Exemplo sintético para documentação.",
  "salary_currency": "BRL",
  "requirements": [
    {
      "kind": "SKILL",
      "importance": "REQUIRED",
      "value": "SQL"
    }
  ]
}
```

## Labels humanas

Crie `.local-data/evals/matching-labels.json`:

```json
[
  {
    "job_file": "vaga-001.json",
    "relevance": 4,
    "blocker_real": false,
    "reason": "A vaga combina com o tipo de trabalho que eu buscaria."
  },
  {
    "job_file": "vaga-002.json",
    "relevance": 1,
    "blocker_real": true,
    "reason": "Exige uma condição que eu realmente não aceitaria."
  }
]
```

Escala:

```text
0 = irrelevante
1 = fraca
2 = razoável
3 = boa
4 = excelente
```

`blocker_real` é uma anotação humana para análise futura. O Match v0 não inventa blockers automaticamente.

## Execução

Com API e banco locais ativos:

```bash
uv run --package hirein-api python scripts/pilot_eval.py import
uv run --package hirein-api python scripts/pilot_eval.py evaluate
```

Ou em sequência:

```bash
uv run --package hirein-api python scripts/pilot_eval.py run
```

O comando `import` cria um manifesto local que associa cada nome de arquivo ao UUID retornado pela API. O comando `evaluate` usa esse manifesto, consulta `/api/v1/jobs/{id}/match`, junta o resultado às labels humanas e gera os relatórios.

## Reexecução segura

Se um arquivo já estiver presente no manifesto, o import não cria outra vaga.

Se a API retornar `409` para uma vaga sem entrada no manifesto, o CLI interrompe. Isso evita tentar adivinhar qual registro existente corresponde ao arquivo local. Nesse caso restaure o manifesto correto ou recrie o banco local do piloto antes de importar novamente.

## Critério para experimentar IA

Não escolher embeddings, reranker ou LLM apenas porque o ranking atual tem erros.

Primeiro classifique os erros das 30–50 vagas reais:

- sinônimo simples;
- ausência de evidência no perfil;
- requisito mal estruturado;
- regra de preferência inadequada;
- equivalência semântica real;
- erro de ordenação apesar de requisitos corretos.

Só então escolher a menor tecnologia que ataque o erro dominante.
