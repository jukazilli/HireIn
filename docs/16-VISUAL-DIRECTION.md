# HireIn — Visual Direction & Product UI Contract

> **Status:** normativa de produto — direção visual aprovada para o piloto  
> **Escopo:** marca, UI, UX, conteúdo, componentes e critérios de revisão visual  
> **Fonte primária:** moodboard aprovado + conceito “Conectado e Dinâmico” + Tinder como referência de comportamento de descoberta  
> **Objetivo principal:** impedir que o HireIn evolua para uma interface genérica de SaaS ou para uma “UI feita por IA” sem identidade própria.

---

## 1. Como este documento deve ser usado

Este arquivo é um **contrato visual**, não um moodboard descritivo.

Toda alteração que crie ou modifique uma tela do HireIn deve respeitar estas regras. Em caso de conflito entre uma implementação existente e este documento, a implementação deve ser revisada — salvo se houver decisão posterior explicitamente aprovada e documentada.

Antes de gerar uma nova tela, componente ou copy, o agente deve responder:

1. Isso parece **HireIn** ou poderia pertencer a qualquer SaaS?
2. A hierarquia visual ajuda uma decisão concreta do usuário?
3. A interface está leve, humana e dinâmica sem parecer infantil?
4. A cor está sendo usada com intenção ou apenas para decorar?
5. A copy informa algo específico ou está usando frases genéricas de IA/marketing?
6. O componente existe porque resolve um comportamento real ou porque “fica bonito em dashboard”?

Se uma resposta for fraca, a solução deve ser redesenhada antes de ser considerada pronta.

---

## 2. Essência visual

### 2.1. Conceito

**Conectado e Dinâmico.**

O HireIn deve transmitir que procurar oportunidades pode ser:

- simples;
- visual;
- rápido;
- humano;
- otimista;
- orientado a decisões;
- menos burocrático.

Não deve parecer:

- ERP de RH;
- ATS corporativo;
- portal de empregos dos anos 2010;
- dashboard B2B pesado;
- app infantil;
- clone do Tinder;
- template genérico de startup de IA.

### 2.2. Personalidade

A marca é:

- próxima, mas não informal demais;
- jovem, mas não adolescente;
- otimista, mas não ingênua;
- tecnológica, mas não fria;
- expressiva, mas não barulhenta;
- inteligente, mas não acadêmica;
- dinâmica, mas não ansiosa.

### 2.3. Frase de teste

Uma tela correta do HireIn deve conseguir sustentar esta sensação:

> **“Minha próxima oportunidade está mais clara e mais próxima.”**

---

## 3. Referências: o que absorver e o que rejeitar

### 3.1. Moodboard aprovado

Absorver:

- fundo claro e amplo;
- índigo como assinatura principal;
- lime como acento energético;
- contraste forte entre texto escuro e superfícies claras;
- tipografia expressiva em títulos;
- fotografia jovem e aspiracional;
- ilustração 3D soft usada com propósito;
- cards arredondados com pouco ruído;
- muito espaço em branco;
- chips leves;
- movimento e sensação de descoberta;
- mistura de produto real + marca humana.

Não absorver de forma literal:

- mockups de celular como elemento recorrente dentro do produto;
- excesso de personagens 3D;
- lime como cor dominante;
- slogans em toda tela;
- composição publicitária dentro de fluxos operacionais.

### 3.2. Tinder como referência de UX

Usar como referência para:

- foco em uma oportunidade por vez quando a tarefa for decidir;
- cards grandes e escaneáveis;
- swipe como gesto opcional e compreensível;
- ações binárias ou rápidas quando fizer sentido;
- feedback imediato após uma decisão;
- sensação de progressão;
- navegação centrada em descoberta.

Não copiar:

- linguagem romântica;
- estética rosa/vermelho;
- animações de “match” por espetáculo;
- gamificação que pressione o usuário;
- mecânicas manipulativas;
- swipe em situações que exigem análise detalhada;
- decisão escondida apenas atrás de gesto — sempre deve existir alternativa acessível por botão.

---

## 4. Anti-generic-AI UI — regra central

Esta é a seção mais importante deste documento.

O HireIn **não pode parecer uma interface montada por um gerador genérico de UI**.

### 4.1. Padrões proibidos por padrão

Evitar, salvo justificativa específica de produto:

- hero com grande blob gradiente abstrato sem função;
- todos os cards com o mesmo raio 16/24 px + sombra difusa;
- grid de quatro KPIs no topo de toda tela;
- excesso de “glassmorphism”;
- gradiente roxo-azul aplicado em qualquer coisa que precise de destaque;
- “bento grid” apenas porque está na moda;
- excesso de pills/chips para transformar qualquer texto em badge;
- ícone dentro de círculo colorido em cada título de seção;
- emoji usado como iconografia de produto;
- estrelinhas/sparkles como sinal visual de “IA”;
- ícones de robô/cérebro mágico para qualquer função inteligente;
- grandes headlines genéricas centralizadas em telas de trabalho;
- cards decorativos com números sem decisão associada;
- seções com texto do tipo “Eleve sua experiência”, “Potencialize seus resultados” ou “Desbloqueie seu potencial”;
- CTA universal “Começar agora” quando existe ação mais específica;
- componentes iguais para funções semanticamente diferentes;
- status representados por arco-íris de cores fortes;
- ilustrações aleatórias geradas por IA sem relação com o contexto;
- imagens de pessoas impecavelmente genéricas em escritórios genéricos;
- layout que dependa de lorem ipsum para parecer equilibrado;
- sidebars cheias de itens fictícios só para “parecer app completo”.

### 4.2. Sinais de que uma tela ficou genérica

Reprovar a tela se:

- o logo pudesse ser trocado e ela ainda parecesse pertencer a qualquer app;
- o título principal usa uma frase que qualquer startup poderia usar;
- a composição começa por “dashboard” em vez da tarefa do usuário;
- cores são aplicadas por estética, não por hierarquia;
- há mais cartões do que decisões;
- a tela tenta parecer sofisticada por sombras/gradientes em vez de clareza;
- o usuário precisa ler muitos rótulos para descobrir a próxima ação;
- componentes têm aparência premium, mas não reduzem carga cognitiva;
- todos os elementos têm bordas arredondadas exageradas e sombras;
- não existe nenhum elemento de marca além do `#6366F1`.

### 4.3. Regra de originalidade

Antes de criar um componente novo, definir qual comportamento do HireIn ele expressa.

Exemplos:

- **Opportunity Card:** decisão rápida sobre uma vaga.
- **Match Evidence:** mostrar por que a vaga combina ou não.
- **Gap Marker:** comunicar ausência de evidência sem punir visualmente o usuário.
- **Pilot Progress:** mostrar quanto do experimento já tem evidência real.

Não criar “Card”, “Stat Card”, “Feature Card” ou “AI Card” sem semântica de produto.

---

## 5. Sistema de cor

### 5.1. Princípio

A interface é majoritariamente **clara e neutra**. Índigo cria identidade. Lime cria energia e direção. Cores semânticas existem para estado e nunca disputam com a marca.

Distribuição visual aproximada:

- 70–80% neutros e branco;
- 15–20% índigo e variações;
- até 5–10% lime/acento;
- cores de status apenas quando houver estado real.

### 5.2. Tokens de marca

```css
:root {
  --color-brand-50:  #EEF0FF;
  --color-brand-100: #E0E3FF;
  --color-brand-200: #C7CBFF;
  --color-brand-300: #A5AAFF;
  --color-brand-400: #8187FA;
  --color-brand-500: #6366F1; /* assinatura HireIn */
  --color-brand-600: #5457DB;
  --color-brand-700: #4548B8;
  --color-brand-800: #383B93;
  --color-brand-900: #303276;

  --color-lime-50:  #F7FEE7;
  --color-lime-100: #ECFCCB;
  --color-lime-200: #D9F99D;
  --color-lime-300: #BEF264;
  --color-lime-400: #A3E635; /* acento principal */
  --color-lime-500: #84CC16;
  --color-lime-600: #65A30D;
  --color-lime-700: #4D7C0F;

  --color-neutral-0:   #FFFFFF;
  --color-neutral-50:  #FAFAFB;
  --color-neutral-100: #F4F4F5;
  --color-neutral-200: #E7E7EC;
  --color-neutral-300: #D4D4DC;
  --color-neutral-400: #A1A1AD;
  --color-neutral-500: #71717D;
  --color-neutral-600: #52525D;
  --color-neutral-700: #3F3F49;
  --color-neutral-800: #27272F;
  --color-neutral-900: #17171D;
  --color-neutral-950: #111827;
}
```

O lime `#A3E635` é a referência operacional inicial. Pode ser refinado após testes de contraste, mas não deve ser trocado casualmente por outro “verde neon”.

### 5.3. Tokens semânticos

```css
:root {
  --color-bg-page: #FAFAFB;
  --color-bg-surface: #FFFFFF;
  --color-bg-subtle: #F4F4F5;

  --color-text-primary: #111827;
  --color-text-secondary: #52525D;
  --color-text-muted: #71717D;
  --color-border-default: #E7E7EC;
  --color-border-strong: #D4D4DC;

  --color-action-primary: #6366F1;
  --color-action-primary-hover: #5457DB;
  --color-action-accent: #A3E635;

  --color-success: #22C55E;
  --color-warning: #F59E0B;
  --color-danger: #EF4444;
  --color-info: #6366F1;
}
```

### 5.4. Hierarquia de cor

1. **Texto e informação:** neutros.
2. **Ação principal:** índigo.
3. **Interesse/energia/destaque jovem:** lime.
4. **Status reais:** success/warning/danger/info.
5. **Decoração:** mínimo possível.

### 5.5. Regras do lime

**Do:**

- ação positiva de descoberta;
- marcador de destaque em campanha;
- detalhe em barra/progresso;
- chip especial;
- microfeedback de interesse.

**Don’t:**

- grandes fundos de leitura;
- texto pequeno lime sobre branco;
- todos os botões de sucesso;
- dezenas de elementos simultaneamente;
- substituir a cor semântica `success` apenas porque ambos são verdes.

---

## 6. Tipografia

### 6.1. Famílias

**Produto / títulos:** `Satoshi`  
**Produto / corpo e UI:** `General Sans`  
**Clash Display:** opcional para campanhas/hero de marca, nunca misturada sem necessidade dentro de telas operacionais.

Fallback do sistema existe apenas por robustez técnica; não é direção visual.

```css
--font-display: "Satoshi", "General Sans", ui-sans-serif, system-ui, sans-serif;
--font-body: "General Sans", ui-sans-serif, system-ui, sans-serif;
```

Não adotar Inter como fonte visual principal do HireIn.

### 6.2. Escala tipográfica

```css
--text-xs:   0.75rem;   /* 12 */
--text-sm:   0.875rem;  /* 14 */
--text-md:   1rem;      /* 16 */
--text-lg:   1.125rem;  /* 18 */
--text-xl:   1.375rem;  /* 22 */
--text-2xl:  1.75rem;   /* 28 */
--text-3xl:  2.25rem;   /* 36 */
--text-4xl:  3rem;      /* 48 */
--text-hero: clamp(2.5rem, 6vw, 4.75rem);
```

### 6.3. Pesos

- Display/hero: 650–750.
- Headings: 600–700.
- Corpo: 400–500.
- Labels: 500–600.
- Nunca usar bold em todo conteúdo para “dar personalidade”.

### 6.4. Hierarquia de texto

Cada tela deve ter, no máximo, uma sequência visual dominante:

```text
contexto curto / eyebrow
→ título de tarefa
→ explicação curta
→ conteúdo/decisão
```

Evitar quatro níveis de subtítulo antes da informação útil.

---

## 7. Voz da marca

### 7.1. Voz

O HireIn fala em **português brasileiro**, usando “você”.

A voz é:

- clara;
- próxima;
- otimista;
- adulta;
- confiante;
- simples;
- útil.

Não é:

- corporativês;
- engraçadinha;
- coach;
- adolescente;
- robótica;
- excessivamente entusiasmada;
- “IA falando sobre IA”.

### 7.2. Regra de copy

A copy deve descrever **a ação ou o benefício concreto daquele momento**.

Preferir:

- “Ver por que combina”
- “Salvar vaga”
- “Não é pra mim”
- “Revisar compatibilidade”
- “Faltam dados para avaliar esta vaga”
- “Você já confirmou 4 de 6 requisitos importantes”
- “Complete seu perfil para melhorar a análise”
- “Sua avaliação ajuda o HireIn a aprender o que importa para você”

Evitar:

- “Potencialize sua carreira”
- “Desbloqueie seu verdadeiro potencial”
- “Revolucione sua jornada profissional”
- “O futuro do recrutamento chegou”
- “Transforme sua carreira com IA”
- “Seu match perfeito está aqui”
- “Experiência inteligente e personalizada”
- “Começar agora” quando existe CTA específico.

### 7.3. Tom por situação

**Descoberta:** leve e curioso.  
“Essa vaga parece próxima do que você procura.”

**Match alto:** confiante sem prometer resultado.  
“Há boa compatibilidade com o que você já confirmou no perfil.”

**Gap:** objetivo, sem julgamento.  
“Não encontramos evidência de inglês avançado no seu perfil.”

**Dados insuficientes:** transparente.  
“Ainda não há informação suficiente para calcular uma compatibilidade confiável.”

**Erro:** calmo e acionável.  
“Não conseguimos salvar sua avaliação. Tente novamente.”

**Sucesso:** curto.  
“Vaga salva.” / “Avaliação registrada.”

### 7.4. Palavras preferidas

Usar mais:

- oportunidade;
- vaga;
- compatibilidade;
- evidência;
- interesse;
- descobrir;
- revisar;
- confirmar;
- salvar;
- candidatura;
- próximo passo.

Usar com cuidado:

- match;
- score;
- IA;
- algoritmo;
- automação.

Esses termos podem aparecer onde explicam o produto, mas não devem dominar a experiência.

---

## 8. Espaçamento e geometria

### 8.1. Spacing tokens

Base de 4 px, com preferência por respiro amplo.

```css
--space-1:  0.25rem; /* 4 */
--space-2:  0.5rem;  /* 8 */
--space-3:  0.75rem; /* 12 */
--space-4:  1rem;    /* 16 */
--space-5:  1.25rem; /* 20 */
--space-6:  1.5rem;  /* 24 */
--space-8:  2rem;    /* 32 */
--space-10: 2.5rem;  /* 40 */
--space-12: 3rem;    /* 48 */
--space-16: 4rem;    /* 64 */
--space-20: 5rem;    /* 80 */
```

### 8.2. Radius

Não arredondar tudo da mesma forma.

```css
--radius-sm: 8px;
--radius-md: 12px;
--radius-lg: 18px;
--radius-xl: 24px;
--radius-pill: 999px;
```

Uso:

- inputs/botões: `sm`/`md`;
- cards de vaga: `lg`;
- hero/marketing: `xl` quando fizer sentido;
- chips: `pill`.

### 8.3. Sombras

Sombras devem ser raras e leves.

```css
--shadow-subtle: 0 1px 2px rgba(17,24,39,.04), 0 4px 16px rgba(17,24,39,.04);
--shadow-card-focus: 0 12px 36px rgba(99,102,241,.10);
```

Evitar sombra em todos os containers. Preferir borda + diferença de superfície.

---

## 9. Iconografia

### 9.1. Estilo

- SVG;
- traço simples;
- mesma família visual;
- 1.5–2 px de stroke na maioria dos tamanhos;
- cantos suaves;
- sem emojis como substitutos.

### 9.2. Uso

Ícone deve:

- antecipar uma ação;
- reforçar uma informação;
- reduzir texto repetitivo.

Não deve existir apenas para “preencher” um card.

### 9.3. Ícones de IA

Não usar sparkles como shorthand universal para IA.

Quando um conteúdo for gerado/sugerido por IA, comunicar com texto claro, por exemplo:

> “Sugestão do HireIn — revise antes de usar.”

---

## 10. Componentes com identidade HireIn

### 10.1. Opportunity Card

É um componente central da marca.

Deve priorizar:

1. cargo;
2. empresa;
3. modalidade/localização;
4. contexto principal;
5. compatibilidade resumida;
6. decisão.

Não transformar em tabela condensada.

Em descoberta mobile, pode ocupar grande parte da viewport.

### 10.2. Match Evidence

Deve responder “por quê?”.

Estrutura preferida:

```text
Requisito
status humano e legível
↳ evidência encontrada no perfil
```

Não mostrar apenas barras e porcentagens.

### 10.3. Gap Marker

Gap não é “falha do candidato”.

Visual:

- neutro/âmbar leve;
- linguagem não punitiva;
- ação possível quando aplicável.

### 10.4. Quick Decision Actions

Na descoberta:

- “Não é pra mim”
- “Salvar”
- “Tenho interesse”

No mobile, podem ganhar gestos equivalentes.

Acessibilidade exige botão visível; swipe não é o único caminho.

### 10.5. Chips

Usar para atributos curtos e escaneáveis:

- Remoto
- Estágio
- Produto
- UX/UI
- CLT

Não transformar frases inteiras em pills.

### 10.6. Progressão do piloto

Progresso deve aparecer como jornada clara, não como “analytics dashboard”.

Exemplo:

```text
5 vagas — smoke test
30 vagas — baseline mínima
50 vagas — baseline estendida
```

---

## 11. Layout e navegação

### 11.1. Mobile-first

No mobile:

- uma tarefa principal por tela;
- CTAs acessíveis ao polegar;
- conteúdo principal antes de navegação secundária;
- evitar colunas estreitas múltiplas;
- cards de descoberta grandes;
- detalhes progressivos.

### 11.2. Desktop

Desktop não deve virar dashboard denso.

Pode expandir para:

- lista + detalhe;
- contexto lateral;
- filtros persistentes;
- painel de evidências;
- comparação moderada.

### 11.3. Navegação principal futura

Estrutura conceitual preferida:

```text
Descobrir
Salvos
Candidaturas
Perfil
```

Áreas de piloto/eval são ferramentas internas e não necessariamente fazem parte da navegação final do produto.

---

## 12. Imagens, fotografia e ilustrações

### 12.1. Fotografia

Preferir:

- pessoas reais;
- diversidade natural;
- ambientes reais de estudo/trabalho;
- luz natural ou neon sutil;
- cenas com ação e contexto;
- recortes espontâneos.

Evitar:

- banco de imagem corporativo óbvio;
- pessoas apontando para notebooks vazios;
- equipes sorrindo para a câmera sem contexto;
- estética artificialmente “startup feliz”.

### 12.2. Ilustração 3D

Pode ser usada em:

- onboarding;
- empty states importantes;
- campanha/landing;
- marcos positivos.

Não usar personagem 3D em toda página.

### 12.3. Geração por IA

Se imagens geradas forem usadas, devem seguir direção de arte específica. Nunca aceitar “jovens felizes trabalhando em escritório moderno” como prompt suficiente.

Toda imagem deve responder:

- qual mensagem comunica?
- qual relação tem com a etapa da jornada?
- ela parece pertencente ao mesmo universo visual das demais?

---

## 13. Motion e microinterações

### 13.1. Princípios

Movimento comunica:

- resposta;
- direção;
- progressão;
- sucesso.

Não comunica “sofisticação” por si só.

### 13.2. Tokens

```css
--motion-fast: 120ms;
--motion-base: 180ms;
--motion-slow: 280ms;
--ease-standard: cubic-bezier(.2,.8,.2,1);
--ease-enter: cubic-bezier(.16,1,.3,1);
```

### 13.3. Exemplos

- card desloca suavemente ao swipe;
- ação de interesse recebe microfeedback lime;
- conteúdo de detalhe entra sem salto;
- skeleton discreto no carregamento;
- sucesso breve, sem confete por padrão.

Respeitar `prefers-reduced-motion`.

---

## 14. Estados de interface

Toda tela relevante deve considerar:

- loading;
- empty;
- partial data;
- success;
- recoverable error;
- blocked/permission state;
- offline/indisponibilidade quando aplicável.

Empty state não deve virar propaganda. Deve explicar a próxima ação.

**Bom:**
> “Você ainda não salvou nenhuma vaga. Quando uma oportunidade chamar atenção, ela aparece aqui.”

**Ruim:**
> “Seu futuro começa agora! Explore infinitas possibilidades e transforme sua carreira.”

---

## 15. Do / Don’t

### Do

- use branco e neutros como base;
- reserve índigo para identidade e ação;
- use lime como energia pontual;
- dê espaço para a informação respirar;
- escreva CTAs específicos;
- explique scores com evidências;
- use uma tarefa dominante por tela;
- construa componentes com semântica HireIn;
- preserve personalidade em mobile e desktop;
- prefira clareza a decoração.

### Don’t

- não copie layouts de dashboards SaaS;
- não use um card para cada pedaço de texto;
- não pinte todas as superfícies de roxo;
- não use lime em excesso;
- não use gradientes só para “parecer tech”;
- não use emoji como iconografia;
- não use copy genérica de startup;
- não trate IA como espetáculo visual;
- não esconda tudo atrás de hover;
- não force swipe onde leitura cuidadosa é necessária;
- não transforme score em verdade absoluta;
- não use 3D/ilustração sem função;
- não invente uma nova linguagem visual por tela.

---

## 16. Checklist anti-UI-genérica para PR

Uma mudança de frontend não está pronta até responder “sim” às perguntas aplicáveis:

### Identidade

- [ ] A tela parece HireIn sem depender do logo?
- [ ] Índigo/lime foram usados de acordo com a hierarquia, não como decoração?
- [ ] Tipografia segue Satoshi + General Sans?
- [ ] Componentes reaproveitam padrões existentes antes de inventar novos?

### UX

- [ ] Existe uma ação ou decisão principal evidente?
- [ ] O usuário entende o que fazer em poucos segundos?
- [ ] O mobile não é apenas desktop comprimido?
- [ ] Gestos possuem alternativa acessível?
- [ ] Estados vazios/erro/loading foram tratados?

### Copy

- [ ] O CTA descreve a ação específica?
- [ ] Não há frases de “AI startup” genéricas?
- [ ] O texto fala em linguagem brasileira natural?
- [ ] O produto evita prometer emprego, entrevista ou compatibilidade “perfeita”?

### Anti-template

- [ ] A tela evita grid de KPIs sem necessidade?
- [ ] Não há bento/glass/gradientes apenas por moda?
- [ ] Não há excesso de cards, pills e sombras?
- [ ] Não há sparkles/robôs/emojis usados para representar IA?
- [ ] A composição nasceu da tarefa real e não de um template?

Se 2 ou mais itens críticos falharem, revisar a direção antes do merge.

---

## 17. Critérios de revisão por tipo de tela

### Descoberta de vagas

Deve ser:

- visual;
- rápida;
- centrada na oportunidade;
- com decisão clara;
- com contexto suficiente para não virar swipe cego.

### Detalhe de vaga

Deve priorizar:

- requisitos;
- compatibilidade explicável;
- gaps;
- empresa/local/modalidade;
- decisão de candidatura.

### Perfil

Deve parecer construção de identidade profissional, não formulário burocrático longo.

Usar:

- agrupamento progressivo;
- edição por blocos;
- exemplos úteis;
- feedback de completude apenas quando acionável.

### Candidaturas

Deve comunicar estágio e próxima ação. Evitar Kanban automático apenas porque “pipeline = Kanban”. Só usar Kanban se comparação/arraste realmente ajudar.

### Piloto / avaliação interna

Pode ser mais técnico que o produto final, mas ainda deve respeitar tipografia, cor e clareza. Não usar o visual de ferramenta interna como referência automática para a experiência pública.

---

## 18. Naming e independência da identidade

O nome **HireIn pode mudar**.

Por isso:

- tokens não devem usar o nome em cada variável (`--hirein-purple` etc.);
- componentes devem ter nomes de função (`OpportunityCard`, `MatchEvidence`);
- a identidade deve sobreviver a uma troca de wordmark;
- slogans não devem ser hardcoded em fluxos operacionais;
- símbolo atual é referência, não dependência estrutural do design system.

---

## 19. Implementação técnica

### 19.1. Fonte única de tokens

Criar tokens em uma camada central de CSS/custom properties e consumi-los em componentes.

Não espalhar hex codes pela aplicação.

### 19.2. Componentes

O design system deve crescer a partir de componentes reais do HireIn, por exemplo:

```text
Button
IconButton
Field
Select
Chip
OpportunityCard
MatchBadge
MatchEvidence
GapMarker
EmptyState
FeedbackMessage
BottomNavigation
TopNavigation
ProgressStep
```

Evitar criar uma biblioteca genérica enorme antes de haver uso real.

### 19.3. Responsividade

Pontos de quebra são consequência do conteúdo, não alvo de dispositivo específico. Como referência inicial:

```css
--bp-sm: 640px;
--bp-md: 768px;
--bp-lg: 1024px;
--bp-xl: 1280px;
```

### 19.4. Acessibilidade

- WCAG AA para texto e controles sempre que aplicável;
- foco visível;
- mínimo de área de toque confortável;
- não depender de cor isoladamente;
- lime com texto escuro, não branco por padrão;
- suporte a teclado;
- `prefers-reduced-motion`;
- labels e nomes acessíveis em ícones.

---

## 20. Copy base sugerida

### Marca / landing

- “Seu próximo desafio começa aqui.”
- “Oportunidades que fazem sentido para o seu momento.”
- “Menos vagas aleatórias. Mais oportunidades que combinam com você.”
- “Descubra, entenda e acompanhe suas próximas oportunidades.”

### Descoberta

- “Por que esta vaga apareceu para você”
- “Boa compatibilidade”
- “Vale olhar com atenção”
- “Poucos dados para avaliar”
- “Tenho interesse”
- “Salvar”
- “Não é pra mim”

### Perfil

- “Conte o que você já fez — o HireIn não inventa por você.”
- “Essas informações ajudam a explicar por que uma vaga combina ou não.”
- “Você controla o que é considerado verdade no seu perfil.”

### Match

- “Compatibilidade baseada no que você confirmou.”
- “O que combina”
- “O que ainda não encontramos”
- “Preferências em conflito”
- “Faltam dados para avaliar com confiança.”

### Avaliação do piloto

- “Sua opinião é a referência.”
- “O algoritmo não aprende sozinho com esta nota; primeiro medimos onde ele erra.”

---

## 21. Regra final para agentes de design/código

Quando houver dúvida entre uma solução “bonita e genérica” e uma solução “mais simples, específica e coerente com o HireIn”, escolher a segunda.

O objetivo não é produzir a interface mais parecida com Dribbble, Behance, Linear, Stripe, Notion, Tinder ou qualquer showcase de IA.

O objetivo é construir uma linguagem que, com o tempo, seja reconhecida como **HireIn**.

**Clareza + identidade + comportamento real > tendência visual.**
