<script>
	import { voterSession } from '$lib/stores/session.js';
	import { goto } from '$app/navigation';
	import { branding } from '$lib/stores/branding.js';
	import { Avatar, Badge } from 'flowbite-svelte';
	import { ArrowRightToBracketOutline } from 'flowbite-svelte-icons';

	/** @type {{ initials?: string }} */
	let { initials = '??' } = $props();

	function handleLogout() {
		voterSession.logout();
		goto('/student/validate');
	}
</script>

<header class="topbar">
	<a href="/student" class="topbar-logo" style="text-decoration: none;">
		<img src={$branding.logoUrl || "/favicon.svg"} alt="{$branding.appName} Logo" class="logo-img" />
		<span class="logo-text">{$branding.appName}</span>
	</a>
	<div class="topbar-right">
		<!-- Flowbite Avatar -->
		{#if $voterSession?.photo_url}
			<Avatar
				src={$voterSession.photo_url}
				alt="Profile"
				size="sm"
				class="topbar-avatar"
				rounded
			/>
		{:else}
			<Avatar size="sm" class="topbar-avatar-fallback" rounded>{initials}</Avatar>
		{/if}

		<button
			class="topbar-logout"
			onclick={handleLogout}
			aria-label="Sign Out"
			title="Sign Out"
		>
			<ArrowRightToBracketOutline size="sm" />
		</button>
	</div>
</header>

<style>
	.topbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 10px 16px;
		padding-top: calc(env(safe-area-inset-top) + 8px);
		background: var(--bg-elevated);
		border-bottom: 1px solid var(--border-subtle);
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		height: calc(56px + env(safe-area-inset-top));
		z-index: 150;
		backdrop-filter: blur(20px);
	}

	.topbar-logo {
		display: flex;
		align-items: center;
		gap: 9px;
	}

	.logo-img {
		width: 28px; height: 28px;
		object-fit: contain; border-radius: 6px; flex-shrink: 0;
	}

	.logo-text {
		font-weight: 800; font-size: 14px;
		letter-spacing: -0.4px; color: var(--text);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: 140px;
	}

	.topbar-right {
		display: flex; align-items: center; gap: 12px;
	}

	:global(.topbar-avatar) {
		border: 2px solid var(--accent) !important;
		box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
		width: 34px !important; height: 34px !important;
	}
	:global(.topbar-avatar-fallback) {
		background: var(--accent) !important;
		color: #fff !important;
		font-size: 11px !important; font-weight: 800 !important;
		width: 34px !important; height: 34px !important;
	}

	.topbar-logout {
		width: 38px; height: 38px;
		border-radius: 10px;
		background: var(--bg-card);
		border: 1px solid var(--border-subtle);
		display: grid; place-items: center;
		color: #e11d48;
		cursor: pointer;
		transition: all 0.2s ease;
		padding: 0;
	}
	.topbar-logout:hover {
		background: #fffafa;
		border-color: #e11d48;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(225, 29, 72, 0.1);
	}
	.topbar-logout:active { transform: scale(0.96); }

	@media (min-width: 1025px) {
		.topbar { display: none; }
	}
</style>
