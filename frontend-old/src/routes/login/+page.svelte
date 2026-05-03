<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth as authApi } from '$lib/api.js';
	import { authSession } from '$lib/stores/auth.js';
	import { theme, toggleTheme } from '$lib/stores/theme.js';
	import { branding } from '$lib/stores/branding.js';

	import { fade, fly } from 'svelte/transition';

	onMount(() => { if ($authSession) goto($authSession.role === 'admin' ? '/admin' : '/adviser'); });

	let id = $state('');
	let password = $state('');
	let showPassword = $state(false);
	let isSubmitting = $state(false);
	let errorMessage = $state('');

	async function handleLogin(/** @type {SubmitEvent} */ e) {
		e.preventDefault();
		if (!id || !password) { errorMessage = 'Please enter both ID and password.'; return; }
		isSubmitting = true; errorMessage = '';
		try {
			const data = await authApi.login(id, password);
			authSession.login(data);
			goto(data.role === 'admin' ? '/admin' : '/adviser');
		} catch (/** @type {any} */ err) {
			errorMessage = err.message ?? 'Sign in failed. Please check your credentials.';
		} finally { isSubmitting = false; }
	}
</script>

<svelte:head><title>Sign In | {$branding.appName}</title></svelte:head>

<div class="auth-page">


	<!-- Desktop card -->
	<div class="auth-card">
		<div class="auth-left">
			<div class="auth-brand">
				<button onclick={toggleTheme} class="auth-logo-btn">
					<img src={$branding.logoUrl || "/Messenger_creation_1261776042047231.jpeg"} alt="{$branding.appName} Logo" class="auth-logo" />
				</button>
				<span class="auth-brand-name">{$branding.appName.toUpperCase()}</span>
			</div>

			<div class="auth-hero">
				<h2 class="auth-hero-title">MANAGE<br /><span class="auth-hero-accent">ELECTIONS.</span></h2>
				<p class="auth-hero-desc">
					SIGN IN TO CREATE ELECTIONS, MANAGE CANDIDATES, AND MONITOR VOTING RESULTS IN REAL TIME.
				</p>
				<div class="auth-features">
					{#each ['CREATE & MANAGE ELECTIONS', 'TRACK VOTES IN REAL TIME', 'FULL AUDIT TRAIL & REPORTS'] as feature}
						<div class="auth-feature-item">
							<div class="auth-feature-check">
								<svg class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="4" viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5" />
								</svg>
							</div>
							<span>{feature}</span>
						</div>
					{/each}
				</div>
			</div>

			<p class="auth-footer-text">© 2025 {$branding.appName.toUpperCase()}</p>
		</div>

		<div class="auth-right">


			<div class="auth-form-container" in:fade={{ duration: 400 }}>
				<h1 class="form-title">STAFF SIGN IN</h1>
				<p class="form-subtitle">ENTER YOUR CREDENTIALS</p>

				<form onsubmit={handleLogin} class="auth-form">
					<div class="auth-field">
						<label class="field-label" for="id">STAFF / EMPLOYEE ID</label>
						<div class="input-icon-wrap">
							<svg class="input-icon" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" /></svg>
							<input type="text" id="id" class="input-base input-with-icon w-full uppercase" bind:value={id} placeholder="E.G. ADM-2024" autocomplete="username" required />
						</div>
					</div>

					<div class="auth-field">
						<label class="field-label" for="password">PASSWORD</label>
						<div class="input-icon-wrap">
							<svg class="input-icon" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" /></svg>
							<input type={showPassword ? 'text' : 'password'} id="password" class="input-base input-with-icon w-full pr-20" bind:value={password} placeholder="••••••••" autocomplete="current-password" required />
							<button type="button" onclick={() => (showPassword = !showPassword)} class="show-toggle">
								{showPassword ? 'HIDE' : 'SHOW'}
							</button>
						</div>
					</div>

					{#if errorMessage}
						<div class="pill pill-danger w-full py-3" in:fly={{ y: 5, duration: 200 }}>
							<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
							</svg>
							<span class="font-bold tracking-tight">{errorMessage}</span>
						</div>
					{/if}

					<button type="submit" disabled={isSubmitting} class="auth-btn-primary">
						{#if isSubmitting}
							<div class="flex items-center gap-3">
								<div class="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></div>
								SIGNING IN...
							</div>
						{:else}
							SIGN IN
						{/if}
					</button>
				</form>

				<div class="form-divider"><span>OR</span></div>
				<a href="/register" class="auth-btn-outline">CREATE AN ACCOUNT</a>

				<div class="form-links">
					<a href="/" class="form-link">BACK TO HOME →</a>
				</div>
			</div>
		</div>
	</div>

	<!-- Mobile -->
	<div class="auth-mobile">
		<div class="auth-mobile-header">
			<button onclick={toggleTheme} class="auth-logo-btn auth-logo-btn-mobile">
				<img src={$branding.logoUrl || "/Messenger_creation_1261776042047231.jpeg"} alt="{$branding.appName} Logo" class="auth-logo auth-logo-lg" />
			</button>
			<h1 class="auth-mobile-title">{$branding.appName.toUpperCase()}</h1>
			<p class="auth-mobile-sub">STAFF PORTAL</p>
		</div>

		<div class="auth-mobile-card">
			<h2 class="form-title">STAFF SIGN IN</h2>
			<p class="form-subtitle">ENTER YOUR CREDENTIALS</p>

			<form onsubmit={handleLogin} class="auth-form">
				<div class="auth-field">
					<label class="field-label" for="idMobile">STAFF / EMPLOYEE ID</label>
					<div class="input-icon-wrap">
						<svg class="input-icon" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" /></svg>
						<input type="text" id="idMobile" class="input-base input-with-icon w-full uppercase" bind:value={id} placeholder="E.G. ADM-2024" autocomplete="username" required />
					</div>
				</div>

				<div class="auth-field">
					<label class="field-label" for="passwordMobile">PASSWORD</label>
					<div class="input-icon-wrap">
						<svg class="input-icon" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" /></svg>
						<input type={showPassword ? 'text' : 'password'} id="passwordMobile" class="input-base input-with-icon w-full pr-20" bind:value={password} placeholder="••••••••" autocomplete="current-password" required />
						<button type="button" onclick={() => (showPassword = !showPassword)} class="show-toggle">
							{showPassword ? 'HIDE' : 'SHOW'}
						</button>
					</div>
				</div>

				{#if errorMessage}
					<div class="pill pill-danger w-full py-3" in:fly={{ y: 5, duration: 200 }}>
						<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
						</svg>
						<span class="font-bold">{errorMessage}</span>
					</div>
				{/if}

				<button type="submit" disabled={isSubmitting} class="auth-btn-primary">
					{#if isSubmitting}
						<div class="flex items-center gap-3">
							<div class="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></div>
							SIGNING IN...
						</div>
					{:else}
						SIGN IN
					{/if}
				</button>
			</form>

			<div class="form-divider"><span>OR</span></div>
			<a href="/register" class="auth-btn-outline">CREATE AN ACCOUNT</a>
			<div class="form-links">
				<a href="/" class="form-link">BACK TO HOME →</a>
			</div>
		</div>

		<p class="auth-mobile-copyright">© 2025 {$branding.appName.toUpperCase()}</p>
	</div>
</div>

<style>
	.auth-page { position: relative; min-height: 100vh; background: linear-gradient(135deg, var(--brand-primary, #0b75fe) 0%, var(--brand-primary-hover, #0052cc) 50%, var(--brand-secondary, #003d99) 100%); overflow: hidden; }

	.auth-card { display: none; position: relative; z-index: 2; width: 90%; max-width: 1100px; min-height: 600px; margin: auto; border-radius: 20px; overflow: hidden; box-shadow: 0 25px 80px rgba(0,0,0,0.25); }
	@media (min-width: 1024px) { .auth-page { display: flex; align-items: center; justify-content: center; } .auth-card { display: flex; } .auth-mobile { display: none !important; } }

	.auth-left { width: 42%; display: flex; flex-direction: column; justify-content: space-between; padding: 2.5rem; position: relative; z-index: 1; }
	.auth-brand { display: flex; align-items: center; gap: 0.75rem; }
	.auth-logo-btn { display: flex; align-items: center; justify-content: center; border: none; background: rgba(255,255,255,0.15); backdrop-filter: blur(10px); border-radius: 12px; padding: 5px; cursor: pointer; transition: transform 0.2s, background 0.2s; outline: none; }
	.auth-logo-btn:hover { transform: scale(1.08) rotate(3deg); background: rgba(255,255,255,0.25); }
	.auth-logo { width: 38px; height: 38px; border-radius: 8px; object-fit: contain; }
	.auth-logo-lg { width: 64px; height: 64px; border-radius: 14px; }
	@media (min-width: 640px) { .auth-logo-lg { width: 72px; height: 72px; } }
	.auth-brand-name { font-size: 1.1rem; font-weight: 900; color: white; letter-spacing: 0.05em; }

	.auth-hero { max-width: 300px; }
	.auth-hero-title { font-size: 2.75rem; font-weight: 900; line-height: 1; color: white; letter-spacing: -0.02em; margin-bottom: 1rem; }
	.auth-hero-accent { color: rgba(255,255,255,0.45); }
	.auth-hero-desc { font-size: 0.55rem; font-weight: 600; letter-spacing: 0.12em; color: rgba(255,255,255,0.55); line-height: 1.8; margin-bottom: 1.5rem; }
	.auth-features { display: flex; flex-direction: column; gap: 0.75rem; }
	.auth-feature-item { display: flex; align-items: center; gap: 0.6rem; font-size: 0.5rem; font-weight: 700; letter-spacing: 0.15em; color: rgba(255,255,255,0.7); }
	.auth-feature-check { width: 22px; height: 22px; border-radius: 7px; background: rgba(255,255,255,0.18); backdrop-filter: blur(6px); display: flex; align-items: center; justify-content: center; color: white; flex-shrink: 0; }
	.auth-footer-text { font-size: 0.45rem; font-weight: 700; letter-spacing: 0.25em; color: rgba(255,255,255,0.3); }

	.auth-right { flex: 1; background: var(--bg-main); padding: 2.5rem 3rem; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; overflow: hidden; border-radius: 0 20px 20px 0; }
	:global(.dark) .auth-right { background: var(--bg-card); }



	.auth-form-container { position: relative; z-index: 1; width: 100%; max-width: 380px; }
	.form-title { font-size: 1.75rem; font-weight: 900; color: var(--text-main); letter-spacing: -0.01em; margin: 0 0 0.25rem; }
	.form-subtitle { font-size: 0.6rem; font-weight: 600; letter-spacing: 0.12em; color: var(--text-subtle); margin: 0 0 1.5rem; }

	.auth-form { display: flex; flex-direction: column; gap: 1rem; }
	.auth-field { display: flex; flex-direction: column; gap: 0.35rem; }

	.input-icon-wrap { position: relative; }
	.input-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); width: 18px; height: 18px; color: var(--text-subtle); opacity: 0.5; pointer-events: none; }
	.input-with-icon { padding-left: 2.5rem !important; }

	.show-toggle {
		position: absolute; right: 12px; top: 50%; transform: translateY(-50%);
		border: none; background: transparent; color: var(--text-subtle);
		font-size: 0.6rem; font-weight: 800; letter-spacing: 0.1em; cursor: pointer;
		transition: color 0.2s;
	}
	.show-toggle:hover { color: var(--brand-primary); }

	.auth-btn-primary { width: 100%; padding: 0.875rem; background: linear-gradient(135deg, var(--brand-primary, #1a1a2e), var(--brand-primary-hover, #16213e)); color: white; border: none; border-radius: 10px; font-size: 0.7rem; font-weight: 800; letter-spacing: 0.2em; cursor: pointer; transition: all 0.2s; text-transform: uppercase; }
	.auth-btn-primary:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0,0,0,0.2); }
	.auth-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

	.form-divider { display: flex; align-items: center; gap: 1rem; margin: 1rem 0; }
	.form-divider::before, .form-divider::after { content: ''; flex: 1; height: 1px; background: var(--border-main); }
	.form-divider span { font-size: 0.55rem; font-weight: 700; letter-spacing: 0.15em; color: var(--text-subtle); }

	.auth-btn-outline { display: block; width: 100%; padding: 0.75rem; border: 1.5px solid var(--border-main); border-radius: 10px; background: transparent; color: var(--text-main); font-size: 0.65rem; font-weight: 800; letter-spacing: 0.15em; text-align: center; text-decoration: none; text-transform: uppercase; cursor: pointer; transition: all 0.2s; }
	.auth-btn-outline:hover { border-color: var(--brand-primary); color: var(--brand-primary); }

	.form-links { margin-top: 1rem; text-align: center; }
	.form-link { font-size: 0.55rem; font-weight: 700; letter-spacing: 0.15em; color: var(--text-subtle); text-decoration: none; text-transform: uppercase; transition: color 0.2s; }
	.form-link:hover { color: var(--text-main); }



	.auth-mobile { display: flex; flex-direction: column; align-items: center; min-height: 100vh; padding: 2rem 1.25rem; z-index: 2; position: relative; }
	@media (min-width: 1024px) { .auth-mobile { display: none; } }
	.auth-mobile-header { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem; }
	.auth-logo-btn-mobile { background: rgba(255,255,255,0.2); }
	.auth-mobile-title { font-size: 1.75rem; font-weight: 900; color: white; letter-spacing: 0.05em; }
	.auth-mobile-sub { font-size: 0.6rem; font-weight: 700; letter-spacing: 0.2em; color: rgba(255,255,255,0.6); }
	.auth-mobile-card { width: 100%; max-width: 420px; background: var(--bg-main); border-radius: 20px; padding: 1.75rem; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
	:global(.dark) .auth-mobile-card { background: var(--bg-card); }
	.auth-mobile-copyright { margin-top: auto; padding-top: 1.5rem; font-size: 0.5rem; font-weight: 700; letter-spacing: 0.2em; color: rgba(255,255,255,0.3); }
</style>
