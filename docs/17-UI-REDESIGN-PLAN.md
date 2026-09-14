# HireIn — UI Redesign Plan

> **Status:** plano de execução da primeira rodada visual
> **Fonte normativa:** `docs/16-VISUAL-DIRECTION.md`
> **Objetivo:** redesenhar a UI navegável existente sem alterar regras de produto ou introduzir novas funcionalidades.

## Escopo desta rodada

Rotas atuais que serão redesenhadas:

- `/` — Candidate Profile;
- `/jobs` — cadastro e gestão manual de vagas;
- `/jobs/match` — leitura explicável do Match;
- `/jobs/review` — avaliação humana do piloto;
- `/pilot` — acompanhamento do experimento.

## Princípios de execução

1. Não criar dashboard genérico para substituir tarefas.
2. A navegação deve parecer um produto único, não cinco protótipos isolados.
3. Índigo cria reconhecimento; lime aparece como acento de energia e decisão positiva.
4. Cards devem ser semânticos: Opportunity, Match Evidence, Gap, Pilot Progress etc.
5. Copy deve ser específica à tarefa atual.
6. Nenhuma tela deve depender de gradientes, glassmorphism ou grids de KPIs para parecer sofisticada.
7. Tinder inspira a mecânica de descoberta e decisão rápida, não a estética.
8. Mobile-first; desktop amplia contexto sem virar dashboard denso.
9. Acessibilidade: foco visível, contraste, navegação por teclado e alternativa a gestos.
10. Esta rodada não adiciona IA, scraping, ATS automation ou Auto Apply.

## Design foundation

A implementação deve extrair a direção visual para tokens reutilizáveis e um shell consistente, evitando CSS ad hoc por página.

### Tokens mínimos

- cor de marca e escalas de suporte;
- lime/acento;
- superfícies e bordas;
- cores semânticas suaves;
- tipografia display/body;
- escala de spacing;
- radius;
- sombras discretas;
- motion/duration;
- largura máxima de leitura e de workspace.

### Componentes semânticos prioritários

- `AppShell` / navegação principal;
- `BrandMark` / wordmark provisório;
- `PageIntro`;
- `OpportunityCard`;
- `QuickDecisionActions`;
- `MatchEvidence`;
- `GapMarker`;
- `ProgressStep`;
- `StatusNotice`;
- `EmptyState`.

## Direção por rota

### `/`

Transformar o formulário de perfil em uma experiência de construção de identidade profissional. A tela deve mostrar progresso e seções claras sem parecer formulário de ERP.

### `/jobs`

A vaga é o objeto principal. Cadastro manual deve ter uma composição editorial clara, com descrição e requisitos separados. Listagem deve priorizar cargo, empresa, modalidade e ação.

### `/jobs/match`

Esta é a tela de confiança do produto. O score não pode ser o único protagonista; evidências, gaps, itens desconhecidos e conflitos precisam ser visualmente legíveis.

### `/jobs/review`

A avaliação humana deve parecer uma sessão de calibração: vaga de um lado, leitura do Match e decisão do usuário. Menos formulário, mais julgamento assistido.

### `/pilot`

Deve orientar o próximo passo do experimento. Métricas existem para decisão, não como parede de cards. O fluxo 5 → 30 → 50 deve ser a espinha dorsal.

## Critério de aceite visual

A rodada só está pronta quando:

- as cinco rotas compartilham shell, tokens e linguagem;
- cada tela possui uma ação principal evidente;
- não há elementos genéricos adicionados só por estética;
- a UI funciona em mobile e desktop;
- o build e `svelte-check` permanecem verdes;
- não houve mudança de regra de domínio;
- o resultado poderia ser reconhecido como HireIn sem depender apenas do logo.
