# Match v1.3 — Blind Holdout #2

> **Status:** concluído  
> **Data:** 16/09/2026  
> **Objetivo:** medir generalização do Match v1.3 em vagas reais e inéditas, sem reutilizar o conjunto que participou do desenvolvimento da v1.3.

---

## 1. Protocolo

O experimento preservou o fluxo cego:

1. dez vagas reais e inéditas foram descobertas fora do HireIn;
2. os anúncios foram normalizados e ingeridos pelo `POST /api/v1/jobs`;
3. nenhum endpoint de Match foi consultado durante a ingestão;
4. a avaliação humana foi concluída antes da revelação do ranking;
5. o Match v1.3 foi mantido congelado durante o experimento;
6. a comparação usa o matcher canônico de produção (`hirein_api.match.current`).

O limiar de relevância para Recall continua sendo `relevance >= 3`, conforme o módulo oficial de ranking/evals.

> **Privacidade:** este documento não versiona comentários humanos, perfil do piloto ou labels por vaga. O repositório é público; somente métricas agregadas e achados de engenharia são registrados aqui.

---

## 2. Resultado agregado

| Métrica | Holdout #2 |
|---|---:|
| Vagas avaliadas | 10 |
| Vagas humanas relevantes (`>= 3`) | 3 |
| Vagas com score numérico | 9 |
| Cobertura média de avaliação | 76,4% |
| Recall@5 | **33,3%** |
| Recall@10 | 100% |
| NDCG@5 | **0,394** |
| NDCG@10 | **0,662** |

`Recall@10` é pouco discriminativo em uma amostra de dez itens, pois todo o conjunto entra no corte. Para este holdout, `Recall@5` e `NDCG@5` são os sinais principais.

---

## 3. Leitura do experimento

O v1.3 mostrou comportamento conservador: vagas de baixa relevância humana não receberam scores altos. Porém, o sistema produziu **falsos negativos relevantes** e, como consequência, vagas adequadas ficaram abaixo de vagas que o humano descartaria.

O problema observado não aponta primeiro para pesos. Ele aponta para a camada que transforma anúncio + perfil em estados `MATCHED`, `GAP` e `UNKNOWN`.

A cobertura média relativamente alta também não garante compreensão correta: uma vaga pode ter alta cobertura porque muitos requisitos foram marcados como `GAP`, mesmo quando a evidência existe em outra forma textual no perfil.

---

## 4. Classes de erro observadas

### 4.1 Requisitos compostos tratados como uma string única

Exemplos típicos de anúncio:

- listas separadas por vírgula;
- alternativas com `ou`;
- requisitos conjuntos com `e`;
- famílias de ferramentas ou cursos.

O matching literal de toda a frase pode gerar falso `GAP` quando uma alternativa válida está confirmada.

### 4.2 Formação acadêmica pouco estruturada

Frases como "áreas de Tecnologia ou correlatas" ou "completo ou cursando" precisam ser decompostas em:

- área/curso aceito;
- operador de alternativas;
- status acadêmico exigido, somente quando explícito.

Ausência de status explícito no anúncio não deve ser convertida em exigência de conclusão.

### 4.3 Experiência avaliada principalmente pelo título do cargo

Requisitos de experiência podem estar claramente sustentados por:

- descrição da experiência;
- responsabilidades confirmadas;
- fatos profissionais;
- projetos realizados.

Depender do título literal do cargo reduz muito o recall.

### 4.4 Ausência de evidência confundida com ausência de competência

Em perfil incompleto, "não encontrei" não significa "não possui".

`GAP` deve ficar reservado para situações em que existe evidência suficiente de incompatibilidade, por exemplo:

- nível confirmado inferior ao mínimo;
- proficiência de idioma abaixo do mínimo explícito;
- anos confirmados abaixo do mínimo;
- blocker geográfico confirmado.

Quando simplesmente não há evidência suficiente, o estado deve permanecer não comprovado/indeterminado e não ser apresentado como afirmação de incapacidade.

### 4.5 Fit não deve virar decisão automática de candidatura

O Match é evidência para decisão, não decisão pelo usuário.

Uma vaga pode possuir gaps desenvolvíveis e ainda ser estrategicamente interessante. Blockers reais devem ser destacados separadamente de diferenças de fit.

---

## 5. O que funcionou

O blocker de localização continuou coerente com a preferência estruturada do piloto.

A comparação de proficiência de idioma da v1.3 também se comportou como planejado: possuir o idioma não é suficiente quando a vaga declara um nível mínimo superior.

A estratégia conservadora evitou scores artificialmente altos em vagas claramente distantes do perfil.

---

## 6. Decisão

**Não recalibrar pesos após o Holdout #2.**

Os pesos atuais ficam congelados porque mudar ponderações não corrige falsos `GAP` produzidos antes da etapa de score.

O próximo ciclo será **Match v1.4 — Structured Evidence & Uncertainty**, priorizando qualidade de normalização e recuperação de evidência.

---

## 7. Escopo proposto para Match v1.4

1. decompor requisitos compostos em grupos `ANY_OF` e `ALL_OF` preservando o texto original;
2. avaliar experiência usando título + descrição + fatos confirmados;
3. estruturar formação por área/curso e status acadêmico explícito;
4. distinguir `GAP` de `NOT_PROVEN`/evidência insuficiente;
5. permitir correspondência auditável entre alternativas de ferramentas/skills;
6. manter blockers determinísticos separados do fit;
7. manter explicação com evidência concreta para cada correspondência;
8. usar dúvidas geradas pela vaga para solicitar confirmação do usuário e enriquecer o perfil, sem inferir fatos automaticamente.

IA/embeddings podem ser usados como camada de recuperação/classificação, desde que o resultado continue preso a evidências confirmadas e não altere o score por inferência livre.

---

## 8. Próxima validação

Depois de implementar a v1.4:

- estes dez itens passam a ser **dados de desenvolvimento**;
- eles podem ser usados para testes de regressão;
- não podem ser reutilizados como holdout cego;
- criar **Blind Holdout #3** com dez novas vagas nunca vistas;
- repetir `Recall@5`, `NDCG@5`, cobertura e análise qualitativa.

O objetivo principal da v1.4 é aumentar recall sem criar falsos positivos ou enfraquecer blockers reais.
