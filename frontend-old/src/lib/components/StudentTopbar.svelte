<script>
	import { voterSession } from '$lib/stores/session.js';
	import { goto } from '$app/navigation';
	import { branding } from '$lib/stores/branding.js';

	/** @type {{ initials?: string }} */
	let { initials = '??' } = $props();

	function handleLogout() {
		voterSession.logout();
		goto('/student/validate');
	}
</script>

<header class="topbar">
	<a href="/student" class="topbar-logo" style="text-decoration: none;">
		<img src={$branding.logoUrl || "/Messenger_creation_1261776042047231.jpeg"} alt="{$branding.appName} Logo" class="logo-img" />
		<span class="logo-text">{$branding.appName}</span>
	</a>
	<div class="topbar-actions">
		<div class="user-profile-mini">
			{#if $voterSession?.photo_url}
				<img src={$voterSession.photo_url} alt="Profile" class="mini-avatar" />
			{:else}
				<div class="mini-avatar-fallback">{initials}</div>
			{/if}
		</div>
		<button class="topbar-logout-premium" onclick={handleLogout} aria-label="Sign Out">
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="power-icon">
				<path d="M18.36 6.64a9 9 0 1 1-12.73 0M12 2v10" />
			</svg>
		</button>
	</div>
</header>

<style>
	.topbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 14px 20px;
		background: var(--surface);
		border-bottom: 1px solid var(--border);
		position: sticky;
		top: 0;
		z-index: 150;
	}

	.topbar-logo {
		display: flex;
		align-items: center;
		gap: 9px;
	}

	.logo-img {
		width: 28px;
		height: 28px;
		object-fit: contain;
		border-radius: 6px;
		flex-shrink: 0;
	}

	.logo-text {
		font-weight: 800;
		font-size: 17px;
		letter-spacing: -0.4px;
		color: var(--text);
	}

	.topbar-actions {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.user-profile-mini {
		display: flex;
		align-items: center;
	}

	.mini-avatar {
		width: 34px;
		height: 34px;
		border-radius: 50%;
		object-fit: cover;
		border: 2px solid var(--accent);
		box-shadow: 0 2px 8px rgba(0,0,0,0.1);
	}

	.mini-avatar-fallback {
		width: 34px;
		height: 34px;
		border-radius: 50%;
		background: var(--accent);
		color: #fff;
		display: grid;
		place-items: center;
		font-size: 11px;
		font-weight: 800;
	}

	.topbar-logout-premium {
		width: 38px;
		height: 38px;
		border-radius: 10px; /* Squircle style */
		background: #fff;
		border: 1px solid var(--border);
		display: grid;
		place-items: center;
		color: #e11d48;
		cursor: pointer;
		transition: all 0.2s ease;
		padding: 0;
		box-shadow: 0 1px 3px rgba(0,0,0,0.05);
	}

	.topbar-logout-premium:hover {
		background: #fffafa;
		border-color: #e11d48;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(225, 29, 72, 0.1);
	}

	.topbar-logout-premium:active {
		transform: scale(0.96);
	}

	.power-icon {
		width: 18px;
		height: 18px;
		stroke-width: 2.5;
	}

	@media (min-width: 768px) {
		.topbar {
			display: none;
		}
	}
</style>
