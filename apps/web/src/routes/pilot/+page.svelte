<script lang="ts">
  import { onMount } from 'svelte';

  const API = 'http://localhost:8000/api/v1';

  type Evaluation = {
    job_id: string;
    relevance: number;
    blocker_real: boolean;
    reason: string | null;
    error_category: string | null;
  };

  type ReviewJob = {
    job_id: string;
    company_name: string;
    title: string;
    location_text: string | null;
    work_model: string | null;
    contract_type: string | null;
    seniority: string | null;
    requirement_count: number;
    evaluation: Evaluation | null;
  };

  type Metrics = {
    sample_count: number;
    relevant_count: number;
    scored_count: number;
    average_coverage: number;
    recall_at_5: number;
    recall_at_10: number;
    ndcg_at_5: number;
    ndcg_at_10: number;
  };

  type RankingItem = {
    job_id: string;
    company_name: string;
    title: string;
    relevance: number;
    score: number | null;
    coverage: number;
    band: string;
    blocker_real: boolean;
    reason: string | null;
    error_category: string | null;
  };

  type Report = {
    metrics: Metrics;
    ranking: RankingItem[];
  };

  let profileReady = false;
  let jobs: ReviewJob[] = [];
  let report: Report | null = null;
  let loading = true;
  let error = '';

  const errorLabels: Record<string, string> = {
    MISSING_PROFILE_EVIDENCE: 'Falta de evidência no perfil',
    BAD_JOB_NORMALIZATION: 'Normalização da vaga',
    SIMPLE_ALIAS: 'Alias simples',
    SEMANTIC_EQUIVALENCE: 'Equivalência semântica',
    PREFERENCE_RULE: 'Regra de preferência',
    SALARY_RULE: 'Regra salarial',
    SENIORITY_RULE: 'Regra de senioridade',
    COVERAGE_FAILURE: 'Cobertura insuficiente',
    RANKING_WEIGHT: 'Peso / ranking',
    OTHER: 'Outro'
  };

  $: reviewedCount = jobs.filter((job) => job.evaluation !== null).length;
  $: smokeProgress = Math.min(reviewedCount / 5, 1);
  $: baselineProgress = Math.min(reviewedCount / 30, 1);
  $: extendedProgress = Math.min(reviewedCount / 50, 1);
  $: goodCount = jobs.filter((job) => (job.evaluation?.relevance ?? -1) >= 3).length;
  $: blockerCount = jobs.filter((job) => job.evaluation?.blocker_real).length;
  $: uncategorizedCount = jobs.filter(
    (job) => job.evaluation && job.evaluation.error_category === null
  ).length;
  $: errorDistribution = buildErrorDistribution(jobs);
  $: topErrors = errorDistribution.slice(0, 5);
  $: nextStep = deriveNextStep();

  function buildErrorDistribution(items: ReviewJob[]) {
    const counts = new Map<string, number>();
    for (const item of items) {
      const category = item.evaluation?.error_category;
      if (!category) continue;
      counts.set(category, (counts.get(category) ?? 0) + 1);
    }
    return [...counts.entries()]
      .map(([category, count]) => ({ category, count }))
      .sort((a, b) => b.count - a.count || a.category.localeCompare(b.category));
  }

  function deriveNextStep() {
    if (!profileReady) {
      return {
        title: 'Complete seu perfil profissional',
        description: 'O Match precisa de uma fonte de verdade antes de comparar você com uma vaga.',
        href: '/',
        action: 'Completar perfil'
      };
    }
    if (jobs.length < 5) {
      return {
        title: 'Cadastre as primeiras 5 vagas reais',
        description: `Há ${jobs.length}/5 vagas no smoke test. Priorize oportunidades que você realmente consideraria.`,
        href: '/jobs',
        action: 'Adicionar vagas'
      };
    }
    if (reviewedCount < 5) {
      return {
        title: 'Conclua o smoke test de revisão',
        description: `${reviewedCount}/5 vagas já receberam sua avaliação humana.`,
        href: '/jobs/review',
        action: 'Revisar vagas'
      };
    }
    if (reviewedCount < 30) {
      return {
        title: 'Expanda a baseline para 30 vagas',
        description: `Smoke test concluído. Faltam ${30 - reviewedCount} avaliações para o primeiro dataset útil.`,
        href: '/jobs/review',
        action: 'Continuar piloto'
      };
    }
    if (reviewedCount < 50) {
      return {
        title: 'Aumente a confiança da baseline',
        description: `A meta mínima foi atingida. Mais ${50 - reviewedCount} avaliações levam o piloto ao alvo estendido.`,
        href: '/jobs/review',
        action: 'Continuar até 50'
      };
    }
    return {
      title: 'Dataset pronto para decisão técnica',
      description: 'Já existe evidência suficiente para decidir se o próximo ganho vem de regras, aliases, embeddings ou LLM.',
      href: '/jobs/review',
      action: 'Revisar diagnóstico'
    };
  }

  function metricPercent(value: number) {
    return `${Math.round(value * 100)}%`;
  }

  async function load() {
    loading = true;
    error = '';
    try {
      const [profileResponse, jobsResponse] = await Promise.all([
        fetch(`${API}/profile`),
        fetch(`${API}/evals/jobs`)
      ]);

      profileReady = profileResponse.ok;

      if (!jobsResponse.ok) {
        const body = await jobsResponse.json().catch(() => null);
        throw new Error(body?.detail ?? `Falha ao carregar vagas (${jobsResponse.status}).`);
      }
      jobs = await jobsResponse.json();

      if (profileReady && reviewedCount > 0) {
        const reportResponse = await fetch(`${API}/evals/report`);
        if (reportResponse.ok) {
          report = await reportResponse.json();
        } else {
          const body = await reportResponse.json().catch(() => null);
          throw new Error(body?.detail ?? `Falha ao gerar relatório (${reportResponse.status}).`);
        }
      } else {
        report = null;
      }
    } catch (reason) {
      error = reason instanceof Error ? reason.message : 'Não foi possível carregar o piloto.';
    } finally {
      loading = false;
    }
  }

  onMount(load);
</script>

<svelte:head>
  <title>Piloto · HireIn</title>
  <meta name="description" content="Progresso do piloto individual do HireIn." />
</svelte:head>

<main class="app-main">
  <section class="pilot-hero">
    <div>
      <p class="eyebrow">Piloto individual</p>
      <h1>Provar antes de automatizar.</h1>
      <p>O objetivo agora não é candidatar mais. É descobrir se o HireIn consegue colocar as oportunidades certas na sua frente e explicar o motivo.</p>
    </div>
    <span class="pilot-accent" aria-hidden="true"></span>
  </section>

  {#if loading}
    <div class="status-notice">Carregando o estado do piloto…</div>
  {:else}
    {#if error}<div class="status-notice error" aria-live="polite">{error}</div>{/if}

    <section class="next-action">
      <div class="next-index">Agora</div>
      <div class="next-copy">
        <p class="section-kicker">Próxima ação</p>
        <h2>{nextStep.title}</h2>
        <p>{nextStep.description}</p>
      </div>
      <a class="btn btn-accent" href={nextStep.href}>{nextStep.action}</a>
    </section>

    <div class="pilot-layout">
      <section class="surface surface-padded validation-path">
        <div class="section-head">
          <div class="section-head-copy">
            <p class="section-kicker">Caminho de validação</p>
            <h2 class="section-title">5 → 30 → 50 vagas</h2>
            <p class="section-description">Cada etapa responde uma pergunta diferente. Não aceleramos para IA antes de entender os erros.</p>
          </div>
        </div>

        <div class="progress-rail">
          <div class="progress-step" class:done={profileReady} class:current={!profileReady}>
            <div class="progress-step-head"><strong>Perfil confiável</strong><span>{profileReady ? 'pronto' : 'pendente'}</span></div>
            <p>Fonte de verdade profissional para que os resultados tenham evidência.</p>
          </div>
          <div class="progress-step" class:done={reviewedCount >= 5} class:current={profileReady && reviewedCount < 5}>
            <div class="progress-step-head"><strong>Smoke test</strong><span>{reviewedCount}/5</span></div>
            <div class="progress-bar"><span style={`width: ${smokeProgress * 100}%`}></span></div>
            <p>Encontrar falhas operacionais e leituras obviamente erradas antes de ampliar a amostra.</p>
          </div>
          <div class="progress-step" class:done={reviewedCount >= 30} class:current={reviewedCount >= 5 && reviewedCount < 30}>
            <div class="progress-step-head"><strong>Baseline mínima</strong><span>{reviewedCount}/30</span></div>
            <div class="progress-bar"><span style={`width: ${baselineProgress * 100}%`}></span></div>
            <p>Volume inicial para reconhecer padrões de erro e comparar qualidade de ranking.</p>
          </div>
          <div class="progress-step" class:done={reviewedCount >= 50} class:current={reviewedCount >= 30 && reviewedCount < 50}>
            <div class="progress-step-head"><strong>Baseline estendida</strong><span>{reviewedCount}/50</span></div>
            <div class="progress-bar"><span style={`width: ${extendedProgress * 100}%`}></span></div>
            <p>Confiança maior para decidir a próxima tecnologia com base em evidência real.</p>
          </div>
        </div>
      </section>

      <aside class="surface surface-padded signals-panel">
        <div class="section-head">
          <div class="section-head-copy">
            <p class="section-kicker">Sinais do piloto</p>
            <h2 class="section-title">O que já sabemos</h2>
          </div>
        </div>
        <div class="data-list">
          <div class="data-row"><span class="data-row-label">Vagas cadastradas</span><strong class="data-row-value">{jobs.length}</strong></div>
          <div class="data-row"><span class="data-row-label">Avaliações humanas</span><strong class="data-row-value">{reviewedCount}</strong></div>
          <div class="data-row"><span class="data-row-label">Boas ou excelentes</span><strong class="data-row-value">{goodCount}</strong></div>
          <div class="data-row"><span class="data-row-label">Blockers reais</span><strong class="data-row-value">{blockerCount}</strong></div>
          <div class="data-row"><span class="data-row-label">Erros sem categoria</span><strong class="data-row-value">{uncategorizedCount}</strong></div>
        </div>
        <a class="text-link signals-link" href="/jobs/review">Abrir fila de revisão</a>
      </aside>
    </div>

    <div class="diagnostic-layout">
      <section class="surface surface-padded">
        <div class="section-head">
          <div class="section-head-copy">
            <p class="section-kicker">Qualidade do ranking</p>
            <h2 class="section-title">Baseline atual</h2>
            <p class="section-description">Estas métricas só ficam úteis quando existe volume suficiente para comparação.</p>
          </div>
          <span class="section-meta">{report?.metrics.sample_count ?? 0} amostras</span>
        </div>
        {#if report}
          <div class="baseline-table">
            <div><span>Recall@5</span><strong>{metricPercent(report.metrics.recall_at_5)}</strong><small>quantas vagas relevantes aparecem no topo</small></div>
            <div><span>NDCG@5</span><strong>{report.metrics.ndcg_at_5.toFixed(3)}</strong><small>qualidade da ordem das vagas relevantes</small></div>
            <div><span>Cobertura média</span><strong>{Math.round(report.metrics.average_coverage)}%</strong><small>quanto da vaga o Match consegue avaliar</small></div>
            <div><span>Com score</span><strong>{report.metrics.scored_count}</strong><small>amostras que passaram do mínimo de cobertura</small></div>
          </div>
        {:else}
          <div class="empty-state">As métricas aparecem depois da primeira avaliação humana e de um perfil válido.</div>
        {/if}
      </section>

      <section class="surface surface-padded">
        <div class="section-head">
          <div class="section-head-copy">
            <p class="section-kicker">Diagnóstico</p>
            <h2 class="section-title">Onde o Match está errando</h2>
            <p class="section-description">Classificar o erro vem antes de escolher a solução técnica.</p>
          </div>
        </div>
        {#if topErrors.length > 0}
          <div class="error-ranking">
            {#each topErrors as item, index}
              <div>
                <span class="error-rank">{String(index + 1).padStart(2, '0')}</span>
                <span>{errorLabels[item.category] ?? item.category}</span>
                <strong>{item.count}</strong>
              </div>
            {/each}
          </div>
        {:else}
          <div class="empty-state">Ainda não há erros categorizados. Isso é esperado antes do smoke test.</div>
        {/if}
      </section>
    </div>

    <section class="surface surface-padded samples-section">
      <div class="section-head">
        <div class="section-head-copy">
          <p class="section-kicker">Amostras</p>
          <h2 class="section-title">Últimas vagas do piloto</h2>
        </div>
        <a class="text-link" href="/jobs/review">Revisar todas</a>
      </div>

      {#if jobs.length === 0}
        <div class="empty-state">Nenhuma vaga cadastrada. O piloto ainda não começou operacionalmente.</div>
      {:else}
        <div class="sample-list">
          {#each jobs.slice(0, 8) as job}
            <div class="sample-row">
              <div>
                <strong>{job.title}</strong>
                <span>{job.company_name} · {job.location_text ?? 'local n/d'}</span>
              </div>
              <div class="sample-status">
                {#if job.evaluation}
                  <strong>{job.evaluation.relevance}/4</strong>
                  <span>{job.evaluation.error_category ? (errorLabels[job.evaluation.error_category] ?? job.evaluation.error_category) : 'revisada'}</span>
                {:else}
                  <strong>—</strong>
                  <span>pendente</span>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </section>

    <aside class="pilot-principle">
      <span aria-hidden="true"></span>
      <div><strong>Regra do piloto</strong><p>Uma métrica ruim não é motivo automático para adicionar IA. Primeiro classificamos o erro. Se o problema for dado ausente, alias ou regra simples, corrigimos isso antes de aumentar custo e opacidade.</p></div>
    </aside>
  {/if}
</main>

<style>
  .pilot-hero { position: relative; display: grid; grid-template-columns: minmax(0, 830px) 1fr; min-height: 270px; align-items: end; margin-bottom: 1rem; padding: clamp(1.6rem, 5vw, 3.2rem); overflow: hidden; border-radius: var(--radius-xl); background: var(--brand-700); color: white; }
  .pilot-hero .eyebrow { color: var(--brand-200); }
  .pilot-hero h1 { margin: .3rem 0 .75rem; max-width: 760px; color: white; font-size: clamp(2.7rem, 7vw, 5.8rem); line-height: .9; letter-spacing: -.065em; }
  .pilot-hero p:last-child { margin: 0; max-width: 690px; color: var(--brand-100); line-height: 1.6; }
  .pilot-accent { position: absolute; right: 4%; bottom: 18%; width: min(160px, 16vw); height: 17px; border-radius: 999px; background: var(--lime-400); transform: rotate(-8deg); }
  .next-action { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 1rem; align-items: center; margin: 1rem 0; padding: 1.15rem 1.2rem; border: 1px solid var(--brand-200); border-radius: var(--radius-lg); background: var(--brand-50); }
  .next-index { display: grid; place-items: center; width: 46px; height: 46px; border-radius: 50%; background: var(--brand-500); color: white; font-size: .72rem; font-weight: 700; }
  .next-copy h2 { margin: .1rem 0 .25rem; font-size: 1.25rem; }
  .next-copy p { margin: 0; color: var(--text-secondary); font-size: .84rem; }
  .pilot-layout { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(280px, .7fr); gap: 1rem; margin-top: 1rem; align-items: start; }
  .signals-panel { position: sticky; top: calc(var(--nav-height) + 1rem); }
  .signals-link { display: inline-block; margin-top: 1rem; }
  .diagnostic-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }
  .baseline-table { display: grid; gap: 0; }
  .baseline-table > div { display: grid; grid-template-columns: 1fr auto; gap: .15rem 1rem; padding: .8rem 0; border-top: 1px solid var(--border); }
  .baseline-table > div:first-child { border-top: 0; padding-top: 0; }
  .baseline-table span { color: var(--text-secondary); font-size: .84rem; }
  .baseline-table strong { color: var(--brand-700); font-family: var(--font-display); }
  .baseline-table small { grid-column: 1 / -1; color: var(--text-muted); font-size: .72rem; }
  .error-ranking { display: grid; }
  .error-ranking > div { display: grid; grid-template-columns: 32px 1fr auto; gap: .7rem; align-items: center; padding: .75rem 0; border-top: 1px solid var(--border); }
  .error-ranking > div:first-child { border-top: 0; padding-top: 0; }
  .error-rank { color: var(--brand-500); font-size: .7rem; font-weight: 700; }
  .error-ranking span:nth-child(2) { color: var(--text-secondary); font-size: .84rem; }
  .samples-section { margin-top: 1rem; }
  .sample-list { display: grid; }
  .sample-row { display: flex; justify-content: space-between; gap: 1rem; align-items: center; padding: .8rem 0; border-top: 1px solid var(--border); }
  .sample-row:first-child { border-top: 0; }
  .sample-row > div:first-child { display: grid; gap: .12rem; }
  .sample-row > div:first-child span, .sample-status span { color: var(--text-muted); font-size: .74rem; }
  .sample-status { display: grid; justify-items: end; gap: .1rem; text-align: right; }
  .pilot-principle { display: flex; gap: 1rem; align-items: flex-start; margin-top: 1rem; padding: 1rem 0; color: var(--text-secondary); }
  .pilot-principle > span { flex: 0 0 auto; width: 42px; height: 8px; margin-top: .45rem; border-radius: 999px; background: var(--lime-400); transform: rotate(-5deg); }
  .pilot-principle p { margin: .3rem 0 0; max-width: 900px; font-size: .84rem; line-height: 1.55; }
  @media (max-width: 900px) {
    .pilot-layout, .diagnostic-layout { grid-template-columns: 1fr; }
    .signals-panel { position: static; }
  }
  @media (max-width: 640px) {
    .pilot-hero { min-height: 320px; grid-template-columns: 1fr; align-items: end; }
    .pilot-accent { right: 8%; top: 18%; width: 88px; height: 10px; }
    .next-action { grid-template-columns: auto 1fr; }
    .next-action .btn { grid-column: 1 / -1; width: 100%; }
    .sample-row { align-items: flex-start; }
  }
</style>
