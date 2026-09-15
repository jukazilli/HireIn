<script lang="ts">
  import type { ActionData, PageData } from './$types';

  let { data, form }: { data: PageData; form: ActionData } = $props();
</script>

<svelte:head>
  <title>Acesso privado · HireIn</title>
</svelte:head>

<main class="login-shell">
  <section class="login-card" aria-labelledby="login-title">
    <p class="eyebrow">Piloto privado</p>
    <h1 id="login-title">Entre no seu HireIn</h1>
    <p class="intro">
      Este ambiente guarda o perfil e as avaliações reais do piloto. O acesso é individual.
    </p>

    {#if !data.configured}
      <div class="notice error" role="alert">
        O acesso privado ainda não foi configurado no ambiente.
      </div>
    {/if}

    <form method="POST" class="login-form">
      <label for="password">Senha do piloto</label>
      <input
        id="password"
        name="password"
        type="password"
        autocomplete="current-password"
        required
        disabled={!data.configured}
      />

      {#if form?.message}
        <p class="form-error" role="alert">{form.message}</p>
      {/if}

      <button class="primary-button" type="submit" disabled={!data.configured}>Entrar</button>
    </form>

    <p class="privacy-note">
      A senha é validada no servidor e não é gravada no navegador nem no repositório.
    </p>
  </section>
</main>

<style>
  .login-shell {
    min-height: 100vh;
    display: grid;
    place-items: center;
    padding: 24px;
    background: var(--surface-soft, #f4f4f5);
  }

  .login-card {
    width: min(100%, 440px);
    background: #fff;
    border: 1px solid var(--border-subtle, #e5e7eb);
    border-radius: 28px;
    padding: clamp(28px, 6vw, 44px);
    box-shadow: 0 18px 50px rgb(17 24 39 / 8%);
  }

  .eyebrow {
    margin: 0 0 10px;
    color: #6366f1;
    font-size: 0.78rem;
    font-weight: 750;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  h1 {
    margin: 0;
    color: #111827;
    font-size: clamp(2rem, 8vw, 3rem);
    line-height: 0.98;
    letter-spacing: -0.045em;
  }

  .intro {
    margin: 18px 0 28px;
    color: #6b7280;
    line-height: 1.6;
  }

  .login-form {
    display: grid;
    gap: 10px;
  }

  label {
    color: #374151;
    font-size: 0.9rem;
    font-weight: 700;
  }

  input {
    width: 100%;
    box-sizing: border-box;
    min-height: 50px;
    border: 1px solid #d1d5db;
    border-radius: 16px;
    padding: 0 16px;
    font: inherit;
    color: #111827;
    background: #fff;
    outline: none;
  }

  input:focus {
    border-color: #6366f1;
    box-shadow: 0 0 0 4px rgb(99 102 241 / 12%);
  }

  .primary-button {
    min-height: 50px;
    margin-top: 8px;
    border: 0;
    border-radius: 16px;
    padding: 0 20px;
    font: inherit;
    font-weight: 800;
    color: white;
    background: #6366f1;
    cursor: pointer;
  }

  .primary-button:disabled,
  input:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  .form-error,
  .notice {
    margin: 4px 0;
    border-radius: 14px;
    padding: 12px 14px;
    font-size: 0.88rem;
  }

  .form-error,
  .notice.error {
    color: #991b1b;
    background: #fef2f2;
    border: 1px solid #fecaca;
  }

  .privacy-note {
    margin: 22px 0 0;
    color: #9ca3af;
    font-size: 0.78rem;
    line-height: 1.5;
  }
</style>
