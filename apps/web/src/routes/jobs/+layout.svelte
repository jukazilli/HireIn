<nav class="workspace-nav" aria-label="HireIn workspace">
  <a href="/jobs">Vagas</a>
  <a href="/jobs/match">Match</a>
</nav>

<slot />

<style>
  .workspace-nav {
    position: sticky;
    top: 0;
    z-index: 20;
    display: flex;
    justify-content: center;
    gap: .35rem;
    width: fit-content;
    margin: .75rem auto -2rem;
    padding: .3rem;
    border: 1px solid #e6e5eb;
    border-radius: 999px;
    background: rgba(255, 255, 255, .94);
    backdrop-filter: blur(12px);
  }
  .workspace-nav a {
    padding: .5rem .85rem;
    border-radius: 999px;
    color: #555361;
    font: 650 .82rem/1 ui-sans-serif, system-ui, sans-serif;
    text-decoration: none;
  }
  .workspace-nav a:hover { background: #f2f1f5; color: #18181f; }
</style>
