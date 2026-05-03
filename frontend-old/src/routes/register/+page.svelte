<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth as authApi } from '$lib/api.js';
	import { authSession } from '$lib/stores/auth.js';
	import { theme, toggleTheme } from '$lib/stores/theme.js';
	import { branding } from '$lib/stores/branding.js';
	import GlassCard from '$lib/components/GlassCard.svelte';
	import { fade, fly } from 'svelte/transition';

	onMount(() => { if ($authSession) goto($authSession.role === 'admin' ? '/admin' : '/adviser'); });

	let fullName = $state('');
	let id = $state('');
	let password = $state('');
	let role = $state(/** @type {'admin' | 'adviser'} */ ('adviser'));
	let department = $state('');
	let isSubmitting = $state(false);
	let errorMessage = $state('');
	let successMessage = $state('');

	async function handleRegister(/** @type {SubmitEvent} */ e) {
		e.preventDefault();
		if (!id || !password || !fullName) { errorMessage = 'Please fill out all required fields.'; return; }
		if (fullName.length < 2) { errorMessage = 'Full name must be at least 2 characters.'; return; }
		if (id.length < 3) { errorMessage = 'ID must be at least 3 characters.'; return; }
		if (password.length < 6) { errorMessage = 'Password must be at least 6 characters.'; return; }
		isSubmitting = true; errorMessage = ''; successMessage = '';
		try {
			const payload = { id, password, full_name: fullName, role, ...(role === 'adviser' && department ? { department } : {}) };
			const data = await authApi.register(payload);
			successMessage = data.message;
			setTimeout(() => goto('/login'), 2000);
		} catch (/** @type {any} */ err) {
			errorMessage = err.message ?? 'Registration failed.';
		} finally { isSubmitting = false; }
	}
</script>

<svelte:head><title>Register | {$branding.appName} Staff Portal</title></svelte:head>

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
				<h1 class="auth-hero-title">JOIN THE<br /><span class="auth-hero-accent">TEAM.</span></h1>
				<p class="auth-hero-desc">
					REGISTER AS AN ADMIN OR ADVISER TO MANAGE ELECTIONS, OVERSEE STUDENT VOTING, AND REVIEW RESULTS.
				</p>
				<div class="auth-features">
					{#each ['ADMIN & ADVISER ROLES', 'FULL ELECTION MANAGEMENT', 'LIVE RESULT MONITORING'] as feature}
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

		<div class="auth-right auth-right-scroll">
			<div class="accent-sphere accent-sphere-br"></div>

			<div class="auth-form-container auth-form-container-wide" in:fade={{ duration: 500 }}>
				<h1 class="form-title">STAFF REGISTRATION</h1>
				<p class="form-subtitle">CREATE YOUR ACCOUNT</p>

				<!-- Role Switch -->
				<div class="role-switch">
					<button type="button" onclick={() => (role = 'adviser')} class="role-btn {role === 'adviser' ? 'role-active' : ''}">ADVISER</button>
					<button type="button" onclick={() => (role = 'admin')} class="role-btn {role === 'admin' ? 'role-active' : ''}">ADMIN</button>
				</div>

				<form onsubmit={handleRegister} class="auth-form">
					<div class="auth-grid">
						<div class="auth-field auth-field-full">
							<label for="fullName" class="field-label">FULL NAME</label>
							<input type="text" id="fullName" bind:value={fullName} placeholder="FULL NAME" class="input-base w-full uppercase" required />
						</div>

						{#if role === 'adviser'}
							<div class="auth-field auth-field-full" in:fly={{ y: -10, duration: 200 }}>
								<label for="department" class="field-label">DEPARTMENT</label>
								<input type="text" id="department" bind:value={department} placeholder="E.G. ENGINEERING" class="input-base w-full uppercase" />
							</div>
						{/if}

						<div class="auth-field">
							<label for="regId" class="field-label">STAFF / EMPLOYEE ID</label>
							<input type="text" id="regId" bind:value={id} placeholder="ID NUMBER" class="input-base w-full uppercase" required />
						</div>

						<div class="auth-field">
							<label for="regPassword" class="field-label">PASSWORD</label>
							<input type="password" id="regPassword" bind:value={password} placeholder="••••••••" class="input-base w-full" required minlength="6" />
						</div>
					</div>

					{#if errorMessage}
						<div class="pill pill-danger w-full py-3" in:fly={{ y: 5, duration: 200 }}>
							<svg class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
							</svg>
							<span class="font-bold">{errorMessage}</span>
						</div>
					{/if}

					{#if successMessage}
						<div class="pill pill-success w-full py-3" in:fade>
							<svg class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
							</svg>
							<span class="font-bold">{successMessage}</span>
						</div>
					{/if}

					<button type="submit" disabled={isSubmitting || !!successMessage} class="auth-btn-primary">
						{#if isSubmitting}
							<div class="flex items-center justify-center gap-3">
								<div class="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></div>
								REGISTERING...
							</div>
						{:else}
							REGISTER
						{/if}
					</button>
				</form>

				<div class="form-divider"><span>OR</span></div>
				<a href="/login" class="auth-btn-outline">SIGN IN INSTEAD</a>
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
			<p class="auth-mobile-sub">STAFF REGISTRATION</p>
		</div>

		<div class="auth-mobile-card">
			<h2 class="form-title form-title-sm">STAFF REGISTRATION</h2>
			<p class="form-subtitle">CREATE YOUR ACCOUNT</p>

			<div class="role-switch">
				<button type="button" onclick={() => (role = 'adviser')} class="role-btn {role === 'adviser' ? 'role-active' : ''}">ADVISER</button>
				<button type="button" onclick={() => (role = 'admin')} class="role-btn {role === 'admin' ? 'role-active' : ''}">ADMIN</button>
			</div>

			<form onsubmit={handleRegister} class="auth-form">
				<div class="auth-field">
					<label for="fullNameM" class="field-label">FULL NAME</label>
					<input type="text" id="fullNameM" bind:value={fullName} placeholder="FULL NAME" class="input-base w-full uppercase" required />
				</div>

				{#if role === 'adviser'}
					<div class="auth-field" in:fly={{ y: -10, duration: 200 }}>
						<label for="departmentM" class="field-label">DEPARTMENT</label>
						<input type="text" id="departmentM" bind:value={department} placeholder="E.G. ENGINEERING" class="input-base w-full uppercase" />
					</div>
				{/if}

				<div class="auth-field">
					<label for="regIdM" class="field-label">STAFF / EMPLOYEE ID</label>
					<input type="text" id="regIdM" bind:value={id} placeholder="ID NUMBER" class="input-base w-full uppercase" required />
				</div>

				<div class="auth-field">
					<label for="regPasswordM" class="field-label">PASSWORD</label>
					<input type="password" id="regPasswordM" bind:value={password} placeholder="••••••••" class="input-base w-full" required minlength="6" />
				</div>

				{#if errorMessage}
					<div class="pill pill-danger w-full py-3" in:fly={{ y: 5, duration: 200 }}>
						<svg class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
						<span class="font-bold">{errorMessage}</span>
					</div>
				{/if}

				{#if successMessage}
					<div class="pill pill-success w-full py-3" in:fade>
						<svg class="h-4 w-4 shrink-0" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" /></svg>
						<span class="font-bold">{successMessage}</span>
					</div>
				{/if}

				<button type="submit" disabled={isSubmitting || !!successMessage} class="auth-btn-primary">
					{#if isSubmitting}
						<div class="flex items-center justify-center gap-3">
							<div class="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></div>
							REGISTERING...
						</div>
					{:else}
						REGISTER
					{/if}
				</button>
			</form>

			<div class="form-divider"><span>OR</span></div>
			<a href="/login" class="auth-btn-outline">SIGN IN INSTEAD</a>
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

	.auth-right { flex: 1; background: var(--bg-main); padding: 2rem 2.5rem; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; overflow: hidden; border-radius: 0 20px 20px 0; }
	.auth-right-scroll { overflow-y: auto; overflow-x: hidden; }
	:global(.dark) .auth-right { background: var(--bg-card); }

	.accent-sphere { position: absolute; border-radius: 50%; pointer-events: none; z-index: 0; }
	.accent-sphere-br { width: 160px; height: 160px; bottom: -50px; right: -50px; background: radial-gradient(circle at 35% 35%, var(--brand-primary-light, rgba(11,117,254,0.2)), var(--brand-primary, rgba(0,82,204,0.5)) 60%, var(--brand-secondary, rgba(0,50,140,0.7))); box-shadow: inset -4px -4px 10px rgba(0,0,0,0.2); animation: sphereBob2 14s ease-in-out infinite; }

	.auth-form-container { position: relative; z-index: 1; width: 100%; max-width: 380px; }
	.auth-form-container-wide { max-width: 440px; }
	.form-title { font-size: 1.75rem; font-weight: 900; color: var(--text-main); letter-spacing: -0.01em; margin: 0 0 0.25rem; }
	.form-title-sm { font-size: 1.4rem; }
	.form-subtitle { font-size: 0.6rem; font-weight: 600; letter-spacing: 0.12em; color: var(--text-subtle); margin: 0 0 1rem; }

	.role-switch { display: flex; gap: 0.4rem; border-radius: 14px; border: 1px solid var(--border-main); background: var(--bg-main); padding: 0.3rem; margin-bottom: 1rem; box-shadow: inset 0 1px 3px rgba(0,0,0,0.05); }
	.role-btn { flex: 1; border: none; border-radius: 10px; padding: 0.5rem; font-size: 0.6rem; font-weight: 900; letter-spacing: 0.15em; cursor: pointer; background: transparent; color: var(--text-subtle); transition: all 0.3s; text-transform: uppercase; }
	.role-active { background: var(--brand-primary); color: white; box-shadow: 0 4px 12px rgba(11,117,254,0.25); }

	.auth-form { display: flex; flex-direction: column; gap: 0.875rem; }
	.auth-grid { display: grid; grid-template-columns: 1fr; gap: 0.875rem; }
	@media (min-width: 640px) { .auth-grid { grid-template-columns: 1fr 1fr; } }
	.auth-field { display: flex; flex-direction: column; gap: 0.35rem; }
	.auth-field-full { grid-column: 1 / -1; }

	.auth-btn-primary { width: 100%; padding: 0.875rem; background: linear-gradient(135deg, var(--brand-primary, #1a1a2e), var(--brand-primary-hover, #16213e)); color: white; border: none; border-radius: 10px; font-size: 0.7rem; font-weight: 800; letter-spacing: 0.2em; cursor: pointer; transition: all 0.2s; text-transform: uppercase; }
	.auth-btn-primary:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0,0,0,0.2); }
	.auth-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

	.form-divider { display: flex; align-items: center; gap: 1rem; margin: 0.75rem 0; }
	.form-divider::before, .form-divider::after { content: ''; flex: 1; height: 1px; background: var(--border-main); }
	.form-divider span { font-size: 0.55rem; font-weight: 700; letter-spacing: 0.15em; color: var(--text-subtle); }

	.auth-btn-outline { display: block; width: 100%; padding: 0.75rem; border: 1.5px solid var(--border-main); border-radius: 10px; background: transparent; color: var(--text-main); font-size: 0.65rem; font-weight: 800; letter-spacing: 0.15em; text-align: center; text-decoration: none; text-transform: uppercase; cursor: pointer; transition: all 0.2s; }
	.auth-btn-outline:hover { border-color: var(--brand-primary); color: var(--brand-primary); }

	.form-links { margin-top: 0.75rem; text-align: center; }
	.form-link { font-size: 0.55rem; font-weight: 700; letter-spacing: 0.15em; color: var(--text-subtle); text-decoration: none; text-transform: uppercase; transition: color 0.2s; }
	.form-link:hover { color: var(--text-main); }



	.auth-mobile { display: flex; flex-direction: column; align-items: center; min-height: 100vh; padding: 2rem 1.25rem; z-index: 2; position: relative; }
	@media (min-width: 1024px) { .auth-mobile { display: none; } }
	.auth-mobile-header { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; margin-bottom: 1.5rem; }
	.auth-logo-btn-mobile { background: rgba(255,255,255,0.2); }
	.auth-mobile-title { font-size: 1.75rem; font-weight: 900; color: white; letter-spacing: 0.05em; }
	.auth-mobile-sub { font-size: 0.6rem; font-weight: 700; letter-spacing: 0.2em; color: rgba(255,255,255,0.6); }
	.auth-mobile-card { width: 100%; max-width: 420px; background: var(--bg-main); border-radius: 20px; padding: 1.5rem; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
	:global(.dark) .auth-mobile-card { background: var(--bg-card); }
	.auth-mobile-copyright { margin-top: auto; padding-top: 1.5rem; font-size: 0.5rem; font-weight: 700; letter-spacing: 0.2em; color: rgba(255,255,255,0.3); }
</style>
