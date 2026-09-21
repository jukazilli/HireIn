<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';

  const items = [
    { href: '/pilot', label: 'Piloto', icon: 'pilot' },
    { href: '/', label: 'Perfil', icon: 'profile' },
    { href: '/jobs', label: 'Vagas', icon: 'jobs' },
    { href: '/jobs/match', label: 'Match', icon: 'match' },
    { href: '/applications', label: 'Studio', icon: 'studio' },
    { href: '/jobs/review', label: 'Revisar', icon: 'review' }
  ];

  const isActive = (href: string) => {
    const path = $page.url.pathname;
    if (href === '/') return path === '/';
    if (href === '/jobs') return path === '/jobs';
    return path.startsWith(href);
  };
</script>

{#if $page.url.pathname === '/login'}
  <slot />
{:else}
  <div class="app-shell">
    <header class="app-bar">
      <a class="brand" href="/pilot" aria-label="HireIn — abrir piloto">
        <span class="brand-mark" aria-hidden="true"><i></i><i></i><b></b></span>
        <span class="brand-word">Hire<span>In</span></span>
        <small>piloto privado</small>
      </a>

      <nav class="desktop-nav" aria-label="Navegação principal">
        {#each items as item}
          <a class:active={isActive(item.href)} href={item.href}>{item.label}</a>
        {/each}
      </nav>

      <div class="header-actions">
        <div class="pilot-state" title="Piloto individual · revisão humana">
          <span aria-hidden="true"></span>
          privado
        </div>
        <form method="POST" action="/logout">
          <button class="logout-button" type="submit" title="Sair do piloto">Sair</button>
        </form>
      </div>
    </header>

    <slot />

    <nav class="mobile-nav" aria-label="Navegação principal mobile">
      {#each items as item}
        <a class:active={isActive(item.href)} href={item.href} aria-label={item.label}>
          {#if item.icon === 'pilot'}
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 19V9m6 10V5m6 14v-7m4 7H2" /></svg>
          {:else if item.icon === 'profile'}
            <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8" r="3.2"/><path d="M5.5 19c.8-3.5 3.1-5.2 6.5-5.2s5.7 1.7 6.5 5.2"/></svg>
          {:else if item.icon === 'jobs'}
            <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="7" width="16" height="12" rx="2"/><path d="M9 7V5h6v2M4 12h16"/></svg>
          {:else if item.icon === 'match'}
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h4l2.2-5 3.4 10L16 12h4"/></svg>
          {:else if item.icon === 'studio'}
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4h10v16H7z"/><path d="M10 8h4M10 12h4M10 16h3"/></svg>
          {:else}
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>
          {/if}
          <span>{item.label}</span>
        </a>
      {/each}
    </nav>
  </div>
{/if}

<style>
  .app-shell { min-height: 100vh; }
  .app-bar {
    position: sticky;
    top: 0;
    z-index: 50;
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    min-height: var(--nav-height);
    padding: 0 max(1rem, calc((100vw - var(--content)) / 2));
    border-bottom: 1px solid rgb(231 231 236 / 88%);
    background: rgb(250 250 251 / 94%);
    backdrop-filter: blur(16px);
  }
  .brand { display: inline-flex; align-items: center; gap: .55rem; color: var(--text-primary); text-decoration: none; }
  .brand-word { font-family: var(--font-display); font-size: 1.28rem; font-weight: 720; letter-spacing: -.045em; }
  .brand-word span { color: var(--brand-500); }
  .brand small { margin-left: .15rem; color: var(--text-muted); font-size: .62rem; font-weight: 650; letter-spacing: .08em; text-transform: uppercase; }
  .brand-mark { position: relative; display: block; width: 26px; height: 25px; }
  .brand-mark i { position: absolute; top: 1px; width: 8px; height: 23px; border-radius: 7px; background: var(--brand-500); }
  .brand-mark i:first-child { left: 1px; transform: rotate(-2deg); }
  .brand-mark i:nth-child(2) { right: 1px; transform: rotate(2deg); }
  .brand-mark b { position: absolute; left: 7px; top: 9px; width: 13px; height: 8px; border-radius: 5px; background: var(--brand-400); transform: rotate(-8deg); }

  .desktop-nav { justify-self: center; display: flex; align-items: center; gap: .2rem; }
  .desktop-nav a { position: relative; padding: .6rem .72rem; border-radius: 9px; color: var(--text-secondary); font-size: .82rem; font-weight: 650; text-decoration: none; }
  .desktop-nav a:hover { background: var(--neutral-100); color: var(--text-primary); }
  .desktop-nav a.active { color: var(--brand-700); background: var(--brand-50); }
  .desktop-nav a.active::after { content: ""; position: absolute; left: 50%; bottom: -.56rem; width: 18px; height: 3px; border-radius: 999px; background: var(--lime-400); transform: translateX(-50%); }

  .header-actions { display: flex; align-items: center; gap: .65rem; }
  .pilot-state { display: inline-flex; align-items: center; gap: .45rem; color: var(--text-muted); font-size: .72rem; font-weight: 600; }
  .pilot-state > span { width: 7px; height: 7px; border-radius: 50%; background: var(--lime-400); box-shadow: 0 0 0 3px var(--lime-100); }
  .logout-button { border: 0; background: transparent; padding: .45rem .5rem; color: var(--text-muted); font: inherit; font-size: .72rem; font-weight: 650; cursor: pointer; }
  .logout-button:hover { color: var(--text-primary); }

  .mobile-nav { display: none; }
  svg { width: 21px; height: 21px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }

  @media (max-width: 760px) {
    .app-bar { min-height: var(--nav-height); grid-template-columns: 1fr auto; padding: 0 .9rem; }
    .desktop-nav { display: none; }
    .brand small { display: none; }
    .pilot-state { display: none; }
    .logout-button { font-size: .68rem; }
    .mobile-nav {
      position: fixed;
      z-index: 60;
      left: .55rem;
      right: .55rem;
      bottom: max(.55rem, env(safe-area-inset-bottom));
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      min-height: 62px;
      padding: .35rem;
      border: 1px solid var(--border);
      border-radius: 18px;
      background: rgb(255 255 255 / 96%);
      box-shadow: var(--shadow-lift);
      backdrop-filter: blur(16px);
    }
    .mobile-nav a { display: grid; place-items: center; align-content: center; gap: .15rem; border-radius: 13px; color: var(--text-muted); text-decoration: none; font-size: .62rem; font-weight: 650; }
    .mobile-nav a.active { background: var(--brand-50); color: var(--brand-700); }
    :global(.app-main) { padding-bottom: 6.5rem; }
  }
</style>
