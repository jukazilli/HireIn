# HireIn — Runtime Real do Piloto Local

## Objetivo

Esta etapa transforma a fundação técnica já validada pelo CI em um ambiente que pode ser usado pelo piloto individual com dados reais, sem publicar perfil, currículo, avaliações ou credenciais no repositório.

A separação é intencional:

```text
Vercel
└── preview visual com dados sintéticos

localhost
├── SvelteKit real
├── FastAPI real
└── PostgreSQL real
    └── dados do piloto
```

O ambiente publicado continua sendo demonstração visual. O piloto com dados pessoais roda em `localhost`.

---

## 1. Princípio de privacidade do P0

Por padrão, o runtime usa PostgreSQL local via `compose.yaml`.

Isso permite validar o produto sem enviar o Candidate Profile ou as avaliações para um banco remoto.

O projeto continua compatível com PostgreSQL remoto, inclusive Neon, através de `DATABASE_URL`. Porém isso é uma opção, não uma exigência para o piloto.

Nunca versionar:

- `.env`;
- currículo real;
- CPF, telefone ou endereço pessoal;
- exportações do banco;
- backups;
- cookies/sessões;
- HTML autenticado de ATS;
- tokens ou senhas.

`.env` e `.local-data/` já são ignorados pelo Git.

---

## 2. Pré-requisitos

Instalar na máquina:

- Git;
- Node.js 22;
- pnpm 12;
- Python gerenciado por `uv`;
- Docker Desktop / Docker Engine.

Verificação rápida:

```bash
pnpm pilot:doctor
```

O diagnóstico não lê nem publica dados pessoais. Ele apenas verifica ferramentas, `.env` e o modo de banco configurado.

---

## 3. Primeiro setup

Na raiz do repositório:

```bash
pnpm pilot:setup
```

Esse comando:

1. cria `.env` a partir de `.env.example` se ainda não existir;
2. instala dependências bloqueadas pelos lockfiles quando necessário;
3. inicia o PostgreSQL local;
4. espera o banco ficar saudável;
5. aplica `alembic upgrade head`;
6. cria `.local-data/` para artefatos privados locais.

Nenhum dado de candidato é criado automaticamente.

---

## 4. Executar o piloto real

Depois do setup:

```bash
pnpm pilot
```

O comando sobe:

```text
FastAPI   → http://127.0.0.1:8000
SvelteKit → http://127.0.0.1:5173
Piloto    → http://127.0.0.1:5173/pilot
```

O navegador é aberto automaticamente.

Para não abrir:

```bash
uv run python scripts/pilot_runtime.py run --no-open
```

Em `localhost` o interceptor de preview sintético fica desligado. As telas usam a API real em `127.0.0.1:8000` / `localhost:8000` e persistem no PostgreSQL.

Encerrar API e frontend com `Ctrl+C`.

O container PostgreSQL pode continuar ativo; o volume `hirein-postgres` preserva os dados entre execuções.

---

## 5. Como saber que não é a demo

O preview publicado usa dados sintéticos no navegador.

No piloto local:

- um perfil novo começa vazio;
- `GET /api/v1/profile` retorna `404` antes do primeiro salvamento;
- salvar e recarregar o perfil preserva seus dados;
- vagas cadastradas reaparecem após reload;
- avaliações humanas persistem no banco;
- o dashboard `/pilot` reflete o dataset real.

Esse mesmo caminho já é exercitado pelo E2E do CI com dados sintéticos, mas o runtime local permite executá-lo com o dataset privado do piloto.

---

## 6. Backup antes de acumular dataset

Para PostgreSQL local:

```bash
pnpm pilot:backup
```

O comando gera um `pg_dump` em:

```text
.local-data/backups/hirein-AAAAMMDDTHHMMSSZ.dump
```

Esse diretório é ignorado pelo Git.

Recomendação operacional:

- fazer backup antes de migrations relevantes;
- fazer backup a cada bloco de aproximadamente 10 vagas avaliadas;
- manter uma cópia privada fora da pasta do repositório se o dataset começar a ter valor significativo.

O comando atual não automatiza restore. Restauração deve continuar deliberada para reduzir risco de sobrescrever dados do piloto por engano.

---

## 7. PostgreSQL remoto opcional

Se houver motivo concreto para usar Neon ou outro PostgreSQL:

1. editar apenas o `.env` local;
2. trocar `DATABASE_URL`;
3. executar `pnpm pilot`.

Quando `DATABASE_URL` não aponta para `localhost`, o helper não inicia o container PostgreSQL e aplica as migrations no banco configurado.

Antes de colocar dados pessoais em um provedor remoto, revisar `docs/07-PRIVACY-SECURITY-LGPD.md` e as políticas atuais do fornecedor.

---

## 8. Fluxo do primeiro piloto real

Com o runtime funcionando, executar primeiro somente 5 oportunidades:

```text
1. preencher Candidate Profile real
2. revisar todos os fatos profissionais
3. cadastrar uma vaga real excelente
4. cadastrar uma vaga boa com gap real
5. cadastrar uma vaga razoável
6. cadastrar uma vaga claramente fraca
7. cadastrar uma vaga com linguagem/sinônimos diferentes
8. calcular Match
9. registrar avaliação humana 0–4
10. revisar relatório e categorias de erro
```

Nenhum currículo ou dado real deve entrar em fixture, commit, issue ou PR.

---

## 9. Gate para o próximo componente

Não avançar direto para Auto Apply ou automação de navegador só porque o runtime funciona.

O próximo risco de produto continua sendo entender a qualidade da preparação da candidatura e da ingestão.

A sequência aceita é:

```text
runtime real
→ 5 vagas reais
→ validar Candidate Core + Match + revisão
→ Application Draft
→ ampliar dataset 30–50 vagas
→ escolher melhoria de ingestão/matching pela evidência
→ só então adapter/assistência de candidatura
```

Se o smoke de 5 vagas revelar falhas graves de modelagem, corrigir antes de aumentar automação.

---

## 10. Comandos

```bash
pnpm pilot:doctor  # verifica pré-requisitos
pnpm pilot:setup   # prepara dependências, banco e migrations
pnpm pilot         # sobe API + web e abre /pilot
pnpm pilot:backup  # backup privado do PostgreSQL local
```

O helper está em `scripts/pilot_runtime.py` e usa apenas biblioteca padrão do Python para sua própria orquestração.
