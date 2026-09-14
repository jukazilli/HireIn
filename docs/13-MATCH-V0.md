# HireIn Match v0

## Objetivo

O HireIn Match v0 conecta as duas fontes de verdade já validadas no piloto:

```text
Candidate Core
      +
Job Core
      ↓
HireIn Match
```

O objetivo inicial não é produzir um número “inteligente” por similaridade textual. É responder de forma auditável:

- quais requisitos possuem evidência profissional confirmada;
- quais requisitos ainda aparecem como gaps;
- quais pontos o motor não consegue avaliar com segurança;
- quais preferências estão alinhadas ou em conflito;
- quanto da vaga foi realmente avaliável pelo motor v0.

O Match v0 não usa embeddings nem LLM.

---

## Princípio central

**Texto parecido não é experiência comprovada.**

Um requisito só pode ser marcado como atendido quando existe evidência estruturada no Candidate Core compatível com ele.

Além disso, somente evidência confirmada pelo usuário pode aumentar o score no v0.

```text
USER_CONFIRMED → pode contar como evidência
AI_DRAFT       → não pode aumentar score
SYSTEM_INFERRED → não pode aumentar score
RESUME_EXTRACTED sem confirmação → não pode aumentar score
```

Alta confiança de modelo não substitui confirmação humana.

---

## Semântica do resultado

Cada requisito pode receber um dos estados:

### MATCHED

Existe evidência confirmada e determinística suficiente.

### GAP

O motor sabe como avaliar aquele tipo de requisito, existe informação suficiente no perfil, mas não encontrou evidência compatível.

### UNKNOWN

O motor não possui evidência suficiente ou o requisito não é avaliável com segurança pelo algoritmo atual.

`UNKNOWN` não deve ser apresentado como ausência de competência.

### INFO

O requisito foi marcado como informativo e não participa do score.

---

## O que é comparado no v0

O Match v0 usa comparação normalizada exata.

### SKILL

Compara contra `CandidateSkill.normalized_name` confirmado.

Se o requisito possui `min_years`, a skill só é considerada atendida quando `years_experience` está informado e é suficiente.

Caso a skill exista, mas os anos não estejam informados, o resultado é `UNKNOWN`, não `MATCHED`.

### TOOL

Pode ser atendido por:

- skill confirmada de mesmo nome;
- `CandidateFact(kind=TOOL)` confirmado.

### DOMAIN

Compara com `CandidateFact(kind=DOMAIN)` confirmado.

### LANGUAGE

Compara com idioma confirmado pelo nome normalizado.

A comparação de nível/proficiência detalhada fica para uma evolução posterior, pois o JobRequirement v0 ainda não modela nível linguístico como campo separado.

### CERTIFICATION

Compara com certificações confirmadas pelo nome normalizado.

### EDUCATION

Compara deterministicamente com curso ou tipo de graduação confirmados.

### EXPERIENCE

Compara deterministicamente com títulos das experiências confirmadas.

Não tenta inferir equivalência entre cargos no v0.

### RESPONSIBILITY

Compara com fatos confirmados do tipo `RESPONSIBILITY`.

### OTHER

Permanece `UNKNOWN` no v0.

### LOCATION / WORK_MODEL / CONTRACT

Não são tratados como experiência profissional. São avaliados na camada de **preferências**, quando houver dados suficientes.

---

## Normalização

A comparação usa a mesma ideia determinística já adotada no Job Core:

- case folding;
- remoção de espaços redundantes.

Exemplo:

```text
"  TOTVS   Protheus "
         ↓
"totvs protheus"
```

Isso deliberadamente não resolve sinônimos.

```text
Analista de Implantação ≠ Consultor de Implantação
```

no Match v0, a menos que o perfil contenha evidência estruturada exatamente compatível.

Essa limitação deverá ser medida no dataset antes de introduzir taxonomias, embeddings ou LLM.

---

## Pesos de requisitos

O score de evidência usa pesos simples e transparentes:

| Importância | Peso |
|---|---:|
| `REQUIRED` | 3 |
| `PREFERRED` | 1 |
| `INFO` | 0 |

`UNKNOWN` não entra no numerador nem no denominador de requisitos avaliados, mas reduz a **cobertura da avaliação**.

### Requirement score

```text
peso dos requisitos MATCHED avaliados
────────────────────────────────────── × 100
peso total dos requisitos avaliados
```

### Evaluation coverage

```text
peso de requisitos MATCHED ou GAP
────────────────────────────────── × 100
peso total de REQUIRED + PREFERRED
```

O score só deve ser tratado como suficiente para classificação quando a cobertura for de pelo menos **60%**.

Esse limite é experimental e deverá ser revisado com o dataset do piloto.

---

## Preferências

Preferências são avaliadas separadamente da experiência profissional.

O v0 considera, quando ambos os lados possuem informação:

- modalidade de trabalho;
- tipo de contrato;
- senioridade;
- faixa salarial.

Também pode reconhecer alinhamento exato de título e localização, mas uma não correspondência textual nesses dois campos é `UNKNOWN`, porque equivalências de cargo e geografia ainda não estão modeladas adequadamente.

### Regra importante

Uma preferência comum **não é blocker**.

Exemplo:

```text
usuário prefere REMOTE
vaga = HYBRID
```

Resultado:

```text
preference conflict
```

Não:

```text
candidato inelegível
```

Para existir blocker real no futuro, o Candidate Core deverá modelar explicitamente uma restrição rígida, por exemplo:

```text
aceito_apenas_remoto = true
```

O Match não irá inferir rigidez onde ela não foi declarada.

---

## Score geral

Quando a cobertura dos requisitos é suficiente:

```text
requirements = 85%
preferences  = 15%
```

Se não houver preferências avaliáveis, o score geral usa apenas os requisitos.

Se não houver requisitos avaliáveis suficientes, o resultado não deve fingir precisão:

```text
score = null
band = INSUFFICIENT_DATA
```

O score é arredondado para número inteiro. Não haverá casas decimais que sugiram precisão inexistente.

---

## Bands

Faixas iniciais experimentais:

| Score | Band |
|---|---|
| 80–100 | `STRONG` |
| 65–79 | `GOOD` |
| 45–64 | `PARTIAL` |
| 0–44 | `LOW` |
| sem cobertura suficiente | `INSUFFICIENT_DATA` |

Esses thresholds não representam probabilidade de contratação ou entrevista.

Eles representam apenas compatibilidade segundo o algoritmo documentado desta versão.

---

## Explicabilidade

A resposta do Match deve conter:

```text
score
band
requirement_score
preference_score
evaluation_coverage
matched_required
missing_required
matched_preferred
missing_preferred
unknown_requirements
requirement_results[]
preference_results[]
warnings[]
```

Cada requisito marcado como `MATCHED` deve apontar para evidência do Candidate Core.

Exemplo:

```text
Requisito: TOTVS Protheus
Status: MATCHED
Evidência:
  tipo: SKILL
  valor: TOTVS Protheus
  origem: USER_CONFIRMED
```

---

## Warnings obrigatórios do v0

A resposta deve deixar explícito pelo menos:

- `exact_matching_only`;
- `unconfirmed_candidate_data_excluded`;
- `score_is_not_hiring_probability`.

Isso evita que o score seja interpretado como garantia ou decisão de recrutamento.

---

## API proposta

```http
GET /api/v1/jobs/{job_id}/match
```

O endpoint utiliza:

- o perfil `primary` do piloto;
- a vaga solicitada.

Erros:

```text
404 → perfil ainda não criado
404 → vaga inexistente
```

O Match v0 é calculado sob demanda e **não é persistido**.

Persistir avaliações antes de sabermos quais métricas realmente importam só adicionaria estado e migrations prematuramente.

---

## O que o score não significa

O score não é:

- probabilidade de contratação;
- probabilidade de entrevista;
- avaliação psicológica;
- recomendação para recrutador;
- julgamento da qualidade da pessoa;
- garantia de compatibilidade cultural;
- decisão automatizada sobre elegibilidade.

Ele é uma ferramenta pessoal para priorização de oportunidades.

---

## Dados não confirmados

Dados não confirmados podem aparecer futuramente como sugestões na interface, mas não aumentam score.

Exemplo:

```text
Skill: SAP
source = AI_DRAFT
confidence = 0.98
```

Para o Match v0:

```text
não conta como evidência
```

Depois que o usuário confirmar explicitamente:

```text
source = USER_CONFIRMED
```

ela poderá contar.

---

## Sem blockers automáticos no v0

O Match v0 não possui um motor genérico de blockers.

Isso é intencional.

Antes de introduzir blockers precisamos diferenciar formalmente:

- preferência;
- requisito da vaga;
- restrição legal/operacional;
- restrição rígida declarada pelo usuário.

Misturar esses conceitos faria o sistema descartar boas oportunidades incorretamente.

---

## Testes necessários

O Match v0 deverá possuir cenários sintéticos cobrindo:

1. requisitos obrigatórios totalmente atendidos;
2. requisito obrigatório ausente;
3. desejável ausente com peso menor;
4. informação `AI_DRAFT` que não pode aumentar score;
5. requisito com anos mínimos sem evidência quantitativa;
6. conflito de modalidade sem transformar em blocker;
7. ausência de dados suficiente → `INSUFFICIENT_DATA`;
8. vaga ou perfil inexistente.

---

## Dataset do piloto

Após o motor estar funcional, o objetivo passa a ser registrar aproximadamente 30–50 vagas reais e marcar manualmente:

- se a vaga realmente interessa;
- quais requisitos consideramos corretamente identificados;
- quais matches o algoritmo acertou;
- quais gaps são falsos negativos por sinônimo/contexto;
- quais vagas o score ordenou incorretamente.

Esse dataset definirá se o próximo ganho deve vir de:

- taxonomia brasileira;
- aliases curados;
- embeddings;
- reranker;
- LLM judge;
- ou simplesmente regras melhores.

Não escolheremos o mecanismo antes de medir o problema.

---

## Fora do escopo

O Match v0 não inclui:

- embeddings;
- vector similarity;
- LLM judge;
- parsing de currículo;
- parsing automático de vaga;
- scraping;
- ATS adapters;
- Resume Tailoring;
- candidatura;
- Auto Apply;
- aprendizado automático de pesos.

---

## Gate seguinte

O Match v0 passa pelo gate quando:

```text
Candidate Core real
       +
Job Core real
       ↓
score reproduzível
       ↓
explicação auditável
       ↓
nenhum fato inventado
       ↓
30–50 vagas avaliadas pelo usuário
```

Somente depois dos dados do piloto decidiremos se o Match precisa de embeddings/IA e qual tecnologia merece entrar na arquitetura.
