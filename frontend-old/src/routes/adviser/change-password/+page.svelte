<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authSession } from '$lib/stores/auth.js';
	import { branding } from '$lib/stores/branding.js';
	import { adviser as adviserApi } from '$lib/api.js';

	let currentPassword = $state('');
	let newPassword = $state('');
	let confirmPassword = $state('');
	let isSaving = $state(false);
	let errorMsg = $state('');
	let showCurrent = $state(false);
	let showNew = $state(false);
	let showConfirm = $state(false);

	onMount(() => {
		// If not an adviser or don't need to change, redirect
		if (!$authSession || $authSession.role !== 'adviser') {
			goto('/');
		} else if (!$authSession.must_change_password) {
			goto('/adviser');
		}
	});

	async function handleSubmit(/** @type {SubmitEvent} */ e) {
		e.preventDefault();
		errorMsg = '';

		if (newPassword.length < 8) {
			errorMsg = 'New password must be at least 8 characters.';
			return;
		}
		if (newPassword !== confirmPassword) {
			errorMsg = 'Passwords do not match.';
			return;
		}
		if (newPassword === currentPassword) {
			errorMsg = 'New password must be different from your current password.';
			return;
		}

		isSaving = true;
		try {
			await adviserApi.changePassword({
				current_password: currentPassword,
				new_password: newPassword
			});

			// Clear the flag in the local session and redirect
			const currentSession = /** @type {import('$lib/stores/auth.js').AdminAdviserSession} */ ($authSession);
			authSession.login({ ...currentSession, must_change_password: false });
			goto('/adviser');
		} catch (/** @type {any} */ err) {
			errorMsg = err?.message || 'Failed to change password.';
		} finally {
			isSaving = false;
		}
	}

	/** Password strength indicator */
	const strength = $derived((() => {
		if (!newPassword) return { label: '', color: '', width: '0%' };
		let score = 0;
		if (newPassword.length >= 8) score++;
		if (newPassword.length >= 12) score++;
		if (/[A-Z]/.test(newPassword)) score++;
		if (/[0-9]/.test(newPassword)) score++;
		if (/[^A-Za-z0-9]/.test(newPassword)) score++;
		if (score <= 1) return { label: 'Weak', color: '#ef4444', width: '20%' };
		if (score === 2) return { label: 'Fair', color: '#f59e0b', width: '40%' };
		if (score === 3) return { label: 'Good', color: 'var(--brand-primary, #3b82f6)', width: '65%' };
		return { label: 'Strong', color: '#22c55e', width: '100%' };
	})());
</script>

<svelte:head><title>Change Password | {$branding.appName}</title></svelte:head>

<div class="page">
	<div class="card">
		<!-- Icon header -->
		<div class="icon-wrap">
			<svg width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"/>
			</svg>
		</div>

		<h1 class="title">Set Your New Password</h1>
		<p class="subtitle">
			Your account uses a temporary password. Please choose a secure password to continue.
		</p>

		{#if errorMsg}
			<div class="error-alert">
				<svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
					<path stroke-linecap="round" stroke-linejoin="round" d="M12 9v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
				</svg>
				{errorMsg}
			</div>
		{/if}

		<form onsubmit={handleSubmit} class="form">
			<!-- Current password -->
			<div class="field">
				<label class="field-label" for="cp-current">Current (Temporary) Password</label>
				<div class="input-wrap">
					<input
						id="cp-current"
						type={showCurrent ? 'text' : 'password'}
						class="input-base"
						bind:value={currentPassword}
						placeholder="Enter your temporary password"
						required
						autocomplete="current-password"
					/>
					<button
						type="button"
						class="eye-btn"
						onclick={() => (showCurrent = !showCurrent)}
						aria-label="Toggle visibility"
					>
						{#if showCurrent}
							<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"/>
							</svg>
						{:else}
							<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
							</svg>
						{/if}
					</button>
				</div>
			</div>

			<!-- New password -->
			<div class="field">
				<label class="field-label" for="cp-new">New Password</label>
				<div class="input-wrap">
					<input
						id="cp-new"
						type={showNew ? 'text' : 'password'}
						class="input-base"
						bind:value={newPassword}
						placeholder="At least 8 characters"
						required
						autocomplete="new-password"
					/>
					<button type="button" class="eye-btn" onclick={() => (showNew = !showNew)} aria-label="Toggle visibility">
						{#if showNew}
							<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"/></svg>
						{:else}
							<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
						{/if}
					</button>
				</div>
				{#if newPassword}
					<div class="strength-bar-wrap">
						<div class="strength-bar" style="width:{strength.width};background:{strength.color};"></div>
					</div>
					<p class="strength-label" style="color:{strength.color};">{strength.label}</p>
				{/if}
			</div>

			<!-- Confirm password -->
			<div class="field">
				<label class="field-label" for="cp-confirm">Confirm New Password</label>
				<div class="input-wrap">
					<input
						id="cp-confirm"
						type={showConfirm ? 'text' : 'password'}
						class="input-base {confirmPassword && confirmPassword !== newPassword ? 'input-error' : ''}"
						bind:value={confirmPassword}
						placeholder="Repeat your new password"
						required
						autocomplete="new-password"
					/>
					<button type="button" class="eye-btn" onclick={() => (showConfirm = !showConfirm)} aria-label="Toggle visibility">
						{#if showConfirm}
							<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"/></svg>
						{:else}
							<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z M15 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
						{/if}
					</button>
				</div>
				{#if confirmPassword && confirmPassword !== newPassword}
					<p class="match-error">Passwords do not match</p>
				{/if}
			</div>

			<button type="submit" class="btn-submit" disabled={isSaving}>
				{#if isSaving}
					<span class="spinner"></span> Saving…
				{:else}
					Set New Password & Continue
				{/if}
			</button>
		</form>
	</div>
</div>

<style>
	.page {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 1.5rem;
		background: var(--bg-base);
	}

	.card {
		width: 100%;
		max-width: 440px;
		background: var(--bg-card);
		border: 1px solid var(--border-main);
		border-radius: 20px;
		padding: 2.25rem;
		box-shadow: 0 8px 40px rgba(0, 0, 0, 0.12);
		display: flex;
		flex-direction: column;
		gap: 0;
	}

	.icon-wrap {
		width: 56px;
		height: 56px;
		border-radius: 14px;
		background: var(--brand-gradient, linear-gradient(135deg, #0b75fe, #5c60f5));
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		margin-bottom: 1.25rem;
	}

	.title {
		font-size: 1.375rem;
		font-weight: 800;
		color: var(--text-main);
		margin: 0 0 0.5rem;
		letter-spacing: -0.02em;
	}

	.subtitle {
		font-size: 0.8125rem;
		color: var(--text-subtle);
		margin: 0 0 1.5rem;
		line-height: 1.55;
	}

	.error-alert {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.625rem 0.875rem;
		background: var(--status-danger-bg, #fff1f2);
		color: var(--status-danger-fg, #dc2626);
		border: 1px solid rgba(220, 38, 38, 0.2);
		border-radius: 10px;
		font-size: 0.8125rem;
		font-weight: 600;
		margin-bottom: 1.25rem;
	}

	.form {
		display: flex;
		flex-direction: column;
		gap: 1.125rem;
	}

	.field {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}

	.field-label {
		font-size: 0.6875rem;
		font-weight: 700;
		color: var(--text-muted);
		text-transform: uppercase;
		letter-spacing: 0.07em;
	}

	.input-wrap {
		position: relative;
	}

	.input-base {
		width: 100%;
		padding: 0.6875rem 2.75rem 0.6875rem 0.875rem;
		font-size: 0.875rem;
		font-family: inherit;
		color: var(--text-main);
		background: var(--bg-elevated);
		border: 1.5px solid var(--border-main);
		border-radius: 10px;
		outline: none;
		box-sizing: border-box;
		transition: border-color 0.2s, box-shadow 0.2s;
	}
	.input-base:focus {
		border-color: var(--brand-primary, #0b75fe);
		box-shadow: var(--focus-ring, 0 0 0 3px rgba(11, 117, 254, 0.12));
	}
	.input-error {
		border-color: #ef4444 !important;
	}

	.eye-btn {
		position: absolute;
		right: 0.75rem;
		top: 50%;
		transform: translateY(-50%);
		background: none;
		border: none;
		cursor: pointer;
		color: var(--text-subtle);
		padding: 0;
		display: flex;
		align-items: center;
	}
	.eye-btn:hover { color: var(--text-muted); }

	/* Strength */
	.strength-bar-wrap {
		height: 4px;
		background: var(--border-main);
		border-radius: 4px;
		overflow: hidden;
		margin-top: 0.25rem;
	}
	.strength-bar {
		height: 100%;
		border-radius: 4px;
		transition: width 0.3s, background 0.3s;
	}
	.strength-label {
		font-size: 0.6875rem;
		font-weight: 700;
		margin: 0;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.match-error {
		font-size: 0.6875rem;
		color: #ef4444;
		font-weight: 600;
		margin: 0;
	}

	.btn-submit {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.75rem;
		font-size: 0.875rem;
		font-weight: 700;
		font-family: inherit;
		color: #fff;
		background: var(--brand-gradient, linear-gradient(135deg, #0b75fe, #5c60f5));
		border: none;
		border-radius: 10px;
		cursor: pointer;
		margin-top: 0.25rem;
		box-shadow: 0 2px 10px rgba(11, 117, 254, 0.3);
		transition: filter 0.18s, transform 0.18s;
	}
	.btn-submit:hover:not(:disabled) { filter: brightness(1.08); transform: translateY(-1px); }
	.btn-submit:disabled { opacity: 0.55; cursor: not-allowed; }

	.spinner {
		width: 14px;
		height: 14px;
		border: 2px solid rgba(15, 23, 42, 0.3);
		border-top-color: #0f172a;
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
	}
	@keyframes spin { to { transform: rotate(360deg); } }
</style>
