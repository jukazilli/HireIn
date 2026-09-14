# HireIn

**HireIn** é um agente pessoal de carreira focado no mercado brasileiro.

A proposta é ajudar o candidato a encontrar vagas relevantes, entender sua compatibilidade, preparar candidaturas melhores e reduzir o trabalho repetitivo de processos seletivos.

> **Fase atual:** documentação-base concluída e preparação da primeira vertical slice do piloto individual.

O projeto começa pequeno: um único usuário, custo recorrente próximo de zero e revisão humana das candidaturas. A expansão para terceiros somente deverá acontecer após validação real do produto e tratamento formal de privacidade, segurança e LGPD.

## Princípios

- qualidade de match antes de volume;
- automação progressiva;
- usuário no controle;
- IA não pode inventar fatos profissionais;
- começar com custo zero ou mínimo;
- tecnologia escolhida por adequação técnica, não por popularidade ou facilidade de codificação;
- evitar dependência de estratégias de evasão de mecanismos anti-bot;
- infraestrutura local-first durante o piloto;
- preparar escala somente depois de provar valor.

## Documentação

1. [Briefing de Produto](docs/01-BRIEFING.md)
2. [Product Flows](docs/02-PRODUCT-FLOWS.md)
3. [Arquitetura](docs/03-ARCHITECTURE.md)
4. [Engenharia](docs/04-ENGINEERING.md)
5. [Infraestrutura](docs/05-INFRASTRUCTURE.md)
6. [Custos](docs/06-COSTS.md)
7. [Privacy, Security & LGPD](docs/07-PRIVACY-SECURITY-LGPD.md)
8. [Roadmap orientado a validação](docs/08-ROADMAP.md)
9. [Architecture Decision Records](docs/adr/README.md)

## Decisões técnicas atuais

| Camada | Direção atual |
|---|---|
| Web | SvelteKit + TypeScript |
| Extensão futura | WXT + Svelte + Manifest V3 |
| Core API | Python + FastAPI |
| Banco | PostgreSQL + pgvector |
| Banco hospedado no piloto | Neon Free |
| ORM / migrations | SQLAlchemy 2 + Alembic |
| Browser automation | Playwright Python |
| Queue do piloto | PostgreSQL |
| Embeddings | modelo multilíngue a escolher por benchmark PT-BR |
| LLM | provider-agnostic, escolha por tarefa/eval |
| Execução do piloto | local-first |

As decisões estruturais possuem ADRs com contexto, alternativas, trade-offs e gatilhos de revisão. LLM e embeddings permanecem propositalmente sem escolha definitiva até existirem evals com dados PT-BR representativos.

## Orçamento do piloto

Meta inicial:

```text
Infraestrutura fixa: US$ 0/mês
IA:                   US$ 0/mês como alvo
Teto experimental IA: até US$ 5/mês somente se necessário
```

O objetivo é pagar somente depois que um gargalo ou ganho de qualidade estiver comprovado.

## Gate de expansão

O HireIn não será aberto a terceiros apenas porque o piloto funciona tecnicamente.

A sequência definida é:

```text
piloto individual
      ↓
validar valor e confiabilidade
      ↓
formalizar privacy/security/LGPD
      ↓
private beta pequeno
      ↓
validar segurança operacional
      ↓
escalar
```

O checklist completo está em `docs/07-PRIVACY-SECURITY-LGPD.md`.

## Próximo marco

A primeira implementação deverá ser uma vertical slice pequena:

```text
1 perfil real
     ↓
1 vaga real
     ↓
normalização
     ↓
Match explicável
     ↓
currículo/respostas preparados
     ↓
revisão humana
```

Depois o experimento cresce para aproximadamente 30–50 vagas, criando o primeiro dataset brasileiro para avaliar matching e orientar a escolha de embeddings.

Não haverá Auto Apply irrestrito no primeiro marco.

## Governança técnica

Antes de alterar uma decisão estrutural, consulte `docs/adr/README.md`.

Novas decisões relevantes devem ser registradas como ADRs. Em especial, ainda deverão receber ADRs futuros quando houver evidência suficiente:

- modelo de embeddings;
- LLM default por tarefa;
- autenticação futura;
- execução remota do browser;
- eventual migração de queue;
- storage remoto de documentos.
