# Candidate Core v0

## Objetivo

O Candidate Core é o primeiro domínio funcional do HireIn.

Ele transforma o candidato de um conjunto de documentos soltos em um **perfil profissional estruturado**, que poderá ser usado posteriormente por Job Core, HireIn Match, Resume Tailoring e Application Draft.

Nesta etapa não existe IA operando sobre o perfil, não existe importação automática de currículo e não existe candidatura automática.

O objetivo é primeiro criar uma fonte de verdade profissional confiável.

---

## Princípio central

O currículo não é o candidato.

Um PDF é apenas uma representação parcial e temporal da carreira. O HireIn precisa conhecer separadamente:

- identidade profissional;
- objetivos atuais;
- experiências;
- formação;
- competências;
- certificações;
- idiomas;
- fatos profissionais verificáveis;
- origem e confiança de cada informação.

Essa separação é necessária para que, futuramente, o sistema consiga adaptar um currículo para uma vaga sem inventar informação.

---

## Escopo do piloto

O Candidate Core v0 assume explicitamente:

- um único usuário;
- um único perfil primário;
- execução local-first;
- entrada manual pela interface;
- dados profissionais não sensíveis;
- revisão humana total;
- `USER_CONFIRMED` como origem dos dados inseridos manualmente.

Não existe autenticação pública nem separação por tenant nesta fase.

A singularidade do perfil é implementada por um `profile_slot = "primary"` único.

---

## Agregado CandidateProfile

```text
CandidateProfile
│
├── identidade profissional
│   ├── nome
│   ├── headline
│   ├── contato
│   ├── localização
│   ├── links profissionais
│   └── resumo
│
├── CareerPreferences
│   ├── cargos desejados
│   ├── áreas desejadas
│   ├── senioridade
│   ├── remoto / híbrido / presencial
│   ├── tipos de contrato
│   ├── localidades alvo
│   ├── faixa salarial
│   ├── disponibilidade para mudança
│   └── disponibilidade para viagens
│
├── Experiences[]
│   └── Facts[]
│
├── Education[]
├── Skills[]
├── Certifications[]
└── Languages[]
```

O perfil é salvo como um agregado único. Uma atualização substitui o conjunto de filhos em uma única transação.

Isso é intencional no piloto: reduz estados parciais e mantém a fonte de verdade coerente.

---

## Fatos versus preferências

O Candidate Core distingue dados objetivos de intenções atuais.

### Fato profissional

Exemplo:

```text
"Trabalhei com TOTVS Protheus"
```

É algo que precisa de origem, confiança e eventualmente evidência.

### Preferência profissional

Exemplo:

```text
"Quero vagas híbridas"
```

É uma intenção atual e pode mudar sem invalidar o histórico profissional.

Essa separação será fundamental no Match.

Uma vaga não deve ser considerada incompatível porque o candidato nunca trabalhou em formato híbrido; modalidade é preferência, não evidência de experiência.

---

## Proveniência

Todos os dados de carreira que poderão ser usados como evidência carregam proveniência.

Fontes atuais previstas:

| Fonte | Significado |
|---|---|
| `USER_CONFIRMED` | informação declarada/confirmada pelo usuário |
| `RESUME_EXTRACTED` | extraída futuramente de currículo |
| `ATS_IMPORTED` | importada futuramente de ATS |
| `AI_DRAFT` | interpretação ou sugestão gerada por IA |
| `SYSTEM_INFERRED` | inferência determinística do sistema |

A proveniência possui:

```text
source_type
source_ref
confidence
confirmed_at
```

### Regra de confirmação

Dados inseridos manualmente pela interface são persistidos como:

```text
source_type = USER_CONFIRMED
confidence = 1.0
confirmed_at = timestamp da confirmação
```

Uma informação gerada futuramente por IA não poderá receber automaticamente o mesmo status.

Exemplo:

```text
AI_DRAFT
confidence = 0.91
confirmed_at = null
```

Alta confiança do modelo **não equivale a confirmação humana**.

---

## Candidate Facts

Experiências podem possuir fatos menores e reutilizáveis.

Tipos atuais:

- `RESPONSIBILITY`;
- `ACHIEVEMENT`;
- `TOOL`;
- `DOMAIN`;
- `PROJECT`;
- `OTHER`.

Exemplo:

```text
Experiência
└── Analista de Implantação
    ├── TOOL: TOTVS Protheus
    ├── DOMAIN: ERP
    ├── RESPONSIBILITY: implantação em clientes
    └── ACHIEVEMENT: redução de retrabalho...
```

Futuramente o Resume Tailoring deverá selecionar fatos compatíveis com a vaga em vez de gerar experiências livres.

---

## Tipos controlados

O domínio possui enums para evitar texto livre onde semântica consistente é importante.

### Modalidade

- `REMOTE`
- `HYBRID`
- `ONSITE`

### Contrato

- `CLT`
- `PJ`
- `INTERNSHIP`
- `APPRENTICE`
- `TEMPORARY`
- `CONTRACTOR`
- `OTHER`

### Senioridade

De `INTERN` até `EXECUTIVE`, incluindo `TRAINEE`, `JUNIOR`, `MID`, `SENIOR`, `SPECIALIST`, `LEAD`, `MANAGER` e `DIRECTOR`.

### Formação

- `IN_PROGRESS`
- `COMPLETED`
- `PAUSED`
- `DROPPED`

### Skill

- `BEGINNER`
- `INTERMEDIATE`
- `ADVANCED`
- `EXPERT`

### Idioma

De `BASIC` até `NATIVE`.

---

## Persistência

Migration:

```text
0002_candidate_core
```

Tabelas:

```text
candidate_profiles
career_preferences
candidate_experiences
candidate_education
candidate_skills
candidate_certifications
candidate_languages
candidate_facts
```

PostgreSQL continua sendo a fonte de persistência.

Skills e idiomas possuem nome normalizado para impedir duplicidades case-insensitive dentro do perfil.

As tabelas filhas usam `ON DELETE CASCADE` para preservar integridade do agregado.

---

## API

### Ler perfil

```http
GET /api/v1/profile
```

Enquanto nenhum perfil existir:

```http
404 candidate profile not created yet
```

### Criar ou substituir perfil

```http
PUT /api/v1/profile
```

O endpoint funciona como upsert do perfil primário.

O ID do perfil permanece estável entre edições; os objetos filhos são substituídos transacionalmente.

OpenAPI continua sendo a fonte de verdade para geração dos tipos TypeScript.

---

## Invariantes

A API e o banco defendem invariantes importantes.

Exemplos:

- data fim de experiência não pode ser anterior à data inicial;
- experiência atual não pode possuir data fim;
- conclusão de formação não pode anteceder início;
- expiração de certificação não pode anteceder emissão;
- salário máximo não pode ser menor que salário mínimo;
- confiança deve estar entre `0` e `1`;
- país usa código de duas letras;
- skills duplicadas são rejeitadas;
- idiomas duplicados são rejeitados;
- enums desconhecidos são rejeitados.

Validações de payload devem produzir erro de entrada (`422`) e não erro interno (`500`).

---

## Interface v0

A primeira interface existe para validar o domínio, não para estabelecer ainda o design system definitivo do HireIn.

Ela permite editar manualmente:

- identidade profissional;
- cargos/áreas desejados;
- senioridade;
- modalidade;
- contrato;
- localização alvo;
- faixa salarial;
- experiências;
- fatos/evidências;
- formação;
- skills;
- certificações;
- idiomas.

A interface deixa explícito que:

```text
IA = desligada
Auto Apply = desligado
```

Nesta etapa o usuário é a autoridade sobre os dados.

---

## Dados deliberadamente excluídos

O Candidate Core v0 não coleta por padrão:

- CPF;
- RG;
- dados bancários;
- raça/etnia;
- religião;
- saúde;
- deficiência/PCD;
- orientação sexual;
- opinião política;
- biometria;
- credenciais de ATS.

Se algum desses dados se tornar realmente necessário no futuro, a necessidade deverá ser analisada no gate de Privacy/Security/LGPD antes de implementação.

---

## Testes

A suíte cobre pelo menos:

- perfil inexistente;
- criação do perfil;
- leitura após persistência;
- atualização mantendo o mesmo perfil primário;
- proveniência manual confirmada;
- invariantes de payload;
- duplicidade de skills/idiomas;
- migrations em PostgreSQL real no CI.

A geração OpenAPI → TypeScript também continua sendo validada pelo pipeline.

---

## Fora do escopo

O Candidate Core v0 **não** inclui:

- parser de PDF/DOCX;
- importação de LinkedIn;
- OCR;
- IA de extração;
- embeddings;
- enriquecimento automático;
- Job Core;
- ranking de vagas;
- HireIn Match;
- currículo adaptado;
- extensão;
- Playwright;
- ATS adapters;
- Auto Apply;
- multiusuário;
- autenticação pública.

---

## Próximo gate

A Etapa B é considerada concluída quando:

```text
perfil manual completo
        ↓
persistência confiável
        ↓
round trip API
        ↓
proveniência preservada
        ↓
CI verde
```

Somente depois disso começamos o **Job Core**.

O Job Core deverá fazer pelo lado da oportunidade o mesmo que o Candidate Core fez pelo candidato:

```text
vaga bruta
   ↓
JobPosting normalizada
   ↓
requisitos estruturados
   ↓
blockers / preferências / evidências
```

Ainda sem LLM como dependência obrigatória no primeiro corte.
