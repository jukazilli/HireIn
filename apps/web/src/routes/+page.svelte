<svelte:head>
  <title>HireIn</title>
  <meta
    name="description"
    content="HireIn — piloto local-first para busca e preparação inteligente de candidaturas."
  />
</svelte:head>

<main>
  <section>
    <p class="eyebrow">HireIn · piloto individual</p>
    <h1>Fundação técnica pronta para a primeira vertical slice.</h1>
    <p class="lead">
      O próximo fluxo será: perfil → vaga → normalização → match explicável → draft → revisão humana.
    </p>
    <div class="status" aria-label="Status do projeto">
      <span>Auto Apply</span>
      <strong>desativado</strong>
    </div>
  </section>
</main>

<style>
  :global(*) {
    box-sizing: border-box;
  }

  :global(body) {
    margin: 0;
    min-width: 320px;
    background: #f8f8fb;
    color: #17171d;
    font-family:
      ui-sans-serif,
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      "Segoe UI",
      sans-serif;
  }

  main {
    min-height: 100vh;
    display: grid;
    place-items: center;
    padding: 2rem;
  }

  section {
    width: min(720px, 100%);
    background: white;
    border: 1px solid #e7e7ee;
    border-radius: 24px;
    padding: clamp(2rem, 6vw, 4rem);
    box-shadow: 0 24px 80px rgb(30 30 45 / 8%);
  }

  .eyebrow {
    margin: 0 0 1rem;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #615f78;
  }

  h1 {
    margin: 0;
    font-size: clamp(2rem, 5vw, 3.4rem);
    line-height: 1.03;
    letter-spacing: -0.045em;
  }

  .lead {
    margin: 1.5rem 0 2rem;
    max-width: 62ch;
    line-height: 1.65;
    color: #555361;
  }

  .status {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    padding-top: 1.25rem;
    border-top: 1px solid #ececf2;
  }

  .status strong {
    font-weight: 700;
  }
</style>
