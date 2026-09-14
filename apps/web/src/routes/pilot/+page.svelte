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
        title: 'Complete o Candidate Profile',
        description: 'O Match precisa de uma fonte de verdade profissional antes de avaliar vagas.',
        href: '/',
        action: 'Abrir perfil'
      };
    }
    if (jobs.length < 5) {
      return {
        title: 'Cadastre as primeiras 5 vagas reais',
        description: `Há ${jobs.length}/5 vagas no smoke test. Priorize vagas que você realmente consideraria candidatar.`,
        href: '/jobs',
        action: 'Cadastrar vagas'
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
        description: `Smoke test concluído. Faltam ${30 - reviewedCount} avaliações para o primeiro dataset representativo.`,
        href: '/jobs/review',
        action: 'Continuar piloto'
      };
    }
    if (reviewedCount < 50) {
      return {
        title: 'Aumente a confiança da baseline',
        description: `A meta mínima de 30 foi atingida. Mais ${50 - reviewedCount} avaliações levam o piloto ao alvo estendido.`,
        href: '/jobs/review',
        action: 'Continuar até 50'
      };
    }
    return {
      title: 'Dataset pronto para decisão técnica',
      description: 'Há evidência suficiente para revisar a distribuição dos erros e decidir a próxima tecnologia.',
      href: '/jobs/review',
      action: 'Revisar diagnóstico'
    };
  }

  function percent(value: number) {
    return `${Math.round(value * 100)}%`;
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
  <meta
    name="description"
    content="Dashboard local para acompanhar o smoke test e a baseline do piloto HireIn."
  />
</svelte:head>

<main>
  <header>
    <div>
      <p class="eyebrow">HireIn · Piloto individual</p>
      <h1>Provar antes de automatizar.</h1>
      <p class="lead">
        Este painel acompanha a validação do Match com vagas reais. Ele não mede volume de candidatura;
        mede se o HireIn consegue priorizar oportunidades que você considera boas.
      </p>
    </div>
    <nav>
      <a href="/">Perfil</a>
      <a href="/jobs">Vagas</a>
      <a href="/jobs/match">Match</a>
      <a class="primary" href="/jobs/review">Revisar</a>
    </nav>
  </header>

  {#if loading}
    <section class="card"><p class="muted">Carregando estado do piloto…</p></section>
  {:else}
    {#if error}
      <section class="notice error" aria-live="polite">{error}</section>
    {/if}

    <section class="next-card">
      <div>
        <p class="eyebrow">Próxima ação</p>
        <h2>{nextStep.title}</h2>
        <p>{nextStep.description}</p>
      </div>
      <a href={nextStep.href}>{nextStep.action} →</a>
    </section>

    <section class="metrics-grid">
      <article class:done={profileReady}>
        <span>Perfil</span>
        <strong>{profileReady ? 'Pronto' : 'Pendente'}</strong>
        <small>fonte de verdade do candidato</small>
      </article>
      <article>
        <span>Vagas</span>
        <strong>{jobs.length}</strong>
        <small>cadastradas no Job Core</small>
      </article>
      <article class:done={reviewedCount >= 5}>
        <span>Revisadas</span>
        <strong>{reviewedCount}</strong>
        <small>labels humanas registradas</small>
      </article>
      <article>
        <span>Boas / excelentes</span>
        <strong>{goodCount}</strong>
        <small>relevância humana 3–4</small>
      </article>
      <article>
        <span>Blockers reais</span>
        <strong>{blockerCount}</strong>
        <small>marcados por você</small>
      </article>
      <article>
        <span>Erros sem categoria</span>
        <strong>{uncategorizedCount}</strong>
        <small>revisões ainda sem diagnóstico</small>
      </article>
    </section>

    <section class="card">
      <div class="section-title">
        <div>
          <p class="eyebrow">Gates</p>
          <h2>Progresso da validação</h2>
        </div>
        <span>Sem IA adicional até existir evidência</span>
      </div>

      <div class="progress-list">
        <div>
          <div class="progress-head">
            <strong>Smoke test</strong>
            <span>{reviewedCount}/5</span>
          </div>
          <div class="track"><i style={`width: ${smokeProgress * 100}%`}></i></div>
          <p>Detecta problemas operacionais da coleta, Match e revisão antes de escalar o dataset.</p>
        </div>
        <div>
          <div class="progress-head">
            <strong>Baseline mínima</strong>
            <span>{reviewedCount}/30</span>
          </div>
          <div class="track"><i style={`width: ${baselineProgress * 100}%`}></i></div>
          <p>Primeiro volume aceitável para comparar padrões de erro e qualidade de ranking.</p>
        </div>
        <div>
          <div class="progress-head">
            <strong>Baseline estendida</strong>
            <span>{reviewedCount}/50</span>
          </div>
          <div class="track"><i style={`width: ${extendedProgress * 100}%`}></i></div>
          <p>Aumenta confiança antes de escolher aliases, embeddings, reranking ou LLM.</p>
        </div>
      </div>
    </section>

    <section class="two-columns">
      <article class="card">
        <div class="section-title">
          <div>
            <p class="eyebrow">Baseline</p>
            <h2>Métricas atuais</h2>
          </div>
          <span>{report?.metrics.sample_count ?? 0} amostras</span>
        </div>

        {#if report}
          <div class="metric-table">
            <div><span>Recall@5</span><strong>{metricPercent(report.metrics.recall_at_5)}</strong></div>
            <div><span>Recall@10</span><strong>{metricPercent(report.metrics.recall_at_10)}</strong></div>
            <div><span>NDCG@5</span><strong>{report.metrics.ndcg_at_5.toFixed(3)}</strong></div>
            <div><span>NDCG@10</span><strong>{report.metrics.ndcg_at_10.toFixed(3)}</strong></div>
            <div><span>Cobertura média</span><strong>{Math.round(report.metrics.average_coverage)}%</strong></div>
            <div><span>Com score</span><strong>{report.metrics.scored_count}</strong></div>
          </div>
        {:else}
          <p class="muted">
            As métricas aparecem depois da primeira avaliação humana e de um Candidate Profile válido.
          </p>
        {/if}
      </article>

      <article class="card">
        <div class="section-title">
          <div>
            <p class="eyebrow">Diagnóstico</p>
            <h2>Erros dominantes</h2>
          </div>
          <span>{errorDistribution.length} categorias</span>
        </div>

        {#if topErrors.length > 0}
          <div class="error-list">
            {#each topErrors as item}
              <div>
                <span>{errorLabels[item.category] ?? item.category}</span>
                <strong>{item.count}</strong>
              </div>
            {/each}
          </div>
        {:else}
          <p class="muted">
            Nenhum erro foi categorizado ainda. Isso é esperado antes do smoke test com vagas reais.
          </p>
        {/if}
      </article>
    </section>

    <section class="card">
      <div class="section-title">
        <div>
          <p class="eyebrow">Amostras</p>
          <h2>Últimas vagas do piloto</h2>
        </div>
        <a class="text-link" href="/jobs/review">Abrir revisão completa →</a>
      </div>

      {#if jobs.length === 0}
        <p class="muted">Nenhuma vaga cadastrada. O piloto ainda não começou operacionalmente.</p>
      {:else}
        <div class="job-list">
          {#each jobs.slice(0, 8) as job}
            <div>
              <div>
                <strong>{job.title}</strong>
                <span>{job.company_name} · {job.location_text ?? 'local n/d'}</span>
              </div>
              <div class="job-status">
                {#if job.evaluation}
                  <b>{job.evaluation.relevance}/4</b>
                  <span>{job.evaluation.error_category ? (errorLabels[job.evaluation.error_category] ?? job.evaluation.error_category) : 'revisada'}</span>
                {:else}
                  <b>—</b>
                  <span>pendente</span>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </section>

    <section class="principle">
      <strong>Regra do piloto</strong>
      <p>
        Uma métrica ruim não é motivo automático para adicionar IA. Primeiro classificamos o erro. Se o
        problema for dado ausente, alias ou regra simples, corrigimos isso antes de aumentar custo e opacidade.
      </p>
    </section>
  {/if}
</main>

<style>
  :global(*) { box-sizing: border-box; }
  :global(body) {
    margin: 0;
    min-width: 320px;
    background: #f7f7fa;
    color: #18181f;
    font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }
  main { width: min(1180px, calc(100% - 2rem)); margin: 0 auto; padding: 3rem 0 5rem; }
  header { display: flex; justify-content: space-between; align-items: flex-end; gap: 2rem; margin-bottom: 2rem; }
  h1 { margin: .35rem 0 .8rem; font-size: clamp(2.4rem, 6vw, 4.7rem); line-height: .98; letter-spacing: -.06em; }
  h2, p { margin-top: 0; }
  .lead { max-width: 760px; color: #62606c; line-height: 1.65; }
  .eyebrow { margin: 0; color: #706d79; font-size: .74rem; font-weight: 800; letter-spacing: .09em; text-transform: uppercase; }
  nav { display: flex; gap: .4rem; flex-wrap: wrap; justify-content: flex-end; }
  nav a, .next-card > a { padding: .7rem .85rem; border-radius: 10px; color: #3f3d47; text-decoration: none; font-size: .86rem; font-weight: 720; }
  nav a:hover { background: #ecebf0; }
  nav a.primary, .next-card > a { background: #1f1e24; color: white; }
  .card { margin-top: 1rem; padding: clamp(1.25rem, 3vw, 2rem); border: 1px solid #e6e5eb; border-radius: 22px; background: white; }
  .next-card { display: flex; justify-content: space-between; align-items: center; gap: 1.5rem; padding: 1.4rem 1.5rem; border-radius: 20px; background: #1f1e24; color: white; }
  .next-card h2 { margin: .25rem 0 .35rem; }
  .next-card p { margin: 0; max-width: 760px; color: #c9c7ce; line-height: 1.5; }
  .next-card .eyebrow { color: #aaa7b1; }
  .next-card > a { flex: 0 0 auto; background: white; color: #1f1e24; }
  .metrics-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: .7rem; margin-top: 1rem; }
  .metrics-grid article { display: grid; gap: .35rem; min-height: 126px; padding: 1rem; border: 1px solid #e6e5eb; border-radius: 16px; background: white; }
  .metrics-grid article.done { border-color: #dbe7dd; background: #fbfefb; }
  .metrics-grid span, .metrics-grid small { color: #777480; font-size: .76rem; line-height: 1.35; }
  .metrics-grid strong { font-size: 1.55rem; letter-spacing: -.035em; }
  .section-title, .progress-head { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
  .section-title { margin-bottom: 1.2rem; }
  .section-title h2 { margin: .2rem 0 0; }
  .section-title > span, .text-link { color: #777480; font-size: .8rem; }
  .text-link { text-decoration: none; }
  .progress-list { display: grid; gap: 1.3rem; }
  .progress-head span { color: #66636f; font-size: .82rem; }
  .track { height: 8px; margin-top: .5rem; overflow: hidden; border-radius: 999px; background: #ecebf0; }
  .track i { display: block; height: 100%; border-radius: inherit; background: #24232a; transition: width .2s ease; }
  .progress-list p { margin: .45rem 0 0; color: #777480; font-size: .82rem; line-height: 1.45; }
  .two-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  .metric-table { display: grid; grid-template-columns: repeat(3, 1fr); gap: .65rem; }
  .metric-table div { display: grid; gap: .35rem; padding: .9rem; border-radius: 13px; background: #f7f7fa; }
  .metric-table span { color: #777480; font-size: .74rem; }
  .metric-table strong { font-size: 1.2rem; }
  .error-list { display: grid; gap: .5rem; }
  .error-list div { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .75rem .85rem; border-radius: 12px; background: #f8f8fa; }
  .error-list span { color: #5e5b66; font-size: .86rem; }
  .job-list { display: grid; }
  .job-list > div { display: flex; justify-content: space-between; align-items: center; gap: 1rem; padding: .85rem 0; border-top: 1px solid #efedf2; }
  .job-list > div:first-child { border-top: 0; }
  .job-list > div > div:first-child { display: grid; gap: .2rem; }
  .job-list span { color: #7a7782; font-size: .78rem; }
  .job-status { display: grid; justify-items: end; gap: .15rem; }
  .job-status b { font-size: .9rem; }
  .principle { margin-top: 1rem; padding: 1.3rem; border: 1px dashed #d8d6de; border-radius: 18px; color: #55525f; }
  .principle p { margin: .45rem 0 0; max-width: 920px; line-height: 1.55; }
  .muted { margin: 0; color: #777480; line-height: 1.55; }
  .notice.error { margin-top: 1rem; padding: 1rem; border: 1px solid #edd7d7; border-radius: 14px; background: #fff8f8; color: #8a3c3c; }
  @media (max-width: 980px) {
    .metrics-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
    .two-columns { grid-template-columns: 1fr; }
  }
  @media (max-width: 700px) {
    main { width: min(100% - 1rem, 1180px); padding-top: 1.5rem; }
    header, .next-card { display: grid; align-items: start; }
    nav { justify-content: flex-start; }
    .next-card > a { width: fit-content; }
    .metrics-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .metric-table { grid-template-columns: repeat(2, 1fr); }
  }
</style>
