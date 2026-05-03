<script>
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { fade, fly } from 'svelte/transition';
	import { voterSession } from '$lib/stores/session.js';
	import { branding, loadBranding } from '$lib/stores/branding.js';
	import { theme, setTheme } from '$lib/stores/theme.js';
	import StudentSidebar from '$lib/components/StudentSidebar.svelte';
	import StudentTopbar from '$lib/components/StudentTopbar.svelte';
	import StudentBottomNav from '$lib/components/StudentBottomNav.svelte';
	import Ripples from '$lib/components/Ripples.svelte';

	let { children } = $props();

	onMount(() => {
		// Load dynamic branding from Admin setup (including global theme)
		loadBranding();
	});

	const showNav = $derived($voterSession && page.url.pathname !== '/student/validate');
	
	const initials = $derived(
		($voterSession?.full_name || '??')
			.split(' ')
			.filter(Boolean)
			.slice(0, 2)
			.map((w) => w[0]?.toUpperCase() || '')
			.join('') || '?'
	);
</script>

<div class="app-container">
	<!-- Fixed Immersive Background Layer -->
	<div class="bg-fixed-layer overflow-hidden" style="background-color: {$branding.showBgAnims ? 'var(--bg-main)' : 'color-mix(in srgb, var(--bg-main) 94%, white)'}">
		<!-- Optimized Flowing Waves -->
		{#if $branding.showBgAnims}
			<!-- Top Left Blob (Primary) -->
			<div class="absolute top-[-50vh] left-[-40vh] w-[140vh] h-[140vh] bg-[var(--brand-primary)] opacity-[0.45] rounded-[45%] blur-[130px] animate-flow" style="will-change: transform;"></div>
			<!-- Bottom Right Blob (Secondary) -->
			<div class="absolute bottom-[-50vh] right-[-40vh] w-[140vh] h-[140vh] bg-[var(--brand-secondary)] opacity-[0.35] rounded-[48%] blur-[140px] animate-flow-reverse" style="will-change: transform;"></div>
			<!-- Center-Left Accent -->
			<div class="absolute top-[10vh] left-[-50vh] w-[110vh] h-[110vh] bg-[var(--brand-primary)] opacity-[0.25] rounded-[40%] blur-[110px] animate-flow-slow" style="will-change: transform; animation-delay: -5s;"></div>
		{/if}
		
		<!-- Corner Glow Overlays -->
		<div class="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(var(--brand-primary-rgb),0.08)_0%,transparent_50%)] pointer-events-none"></div>
		<div class="absolute inset-0 bg-[radial-gradient(circle_at_bottom_right,rgba(var(--brand-accent-rgb),0.08)_0%,transparent_50%)] pointer-events-none"></div>

		<!-- Water Ripple Effect (Global Component) -->
		<Ripples />
	</div>

	{#if showNav}
		<StudentSidebar student_info={$voterSession} />
		<StudentTopbar {initials} />
	{/if}

	<main class={showNav ? 'main' : 'min-h-screen'}>
		{#key page.url.href}
			<div class={showNav ? 'flex-1 flex flex-col' : ''} in:fly={{ y: 20, duration: 350 }} out:fade={{ duration: 200 }}>
				{@render children()}
			</div>
		{/key}
	</main>

	{#if showNav}
		<StudentBottomNav />
	{/if}
</div>

<style>
	.app-container {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		background: transparent;
		position: relative;
		overflow-x: hidden;
	}

	.bg-fixed-layer {
		position: fixed;
		inset: 0;
		z-index: -1;
		background-color: transparent;
	}

	.main {
		flex: 1;
		padding: 16px;
		width: auto;
		transition: margin-left 0.3s ease;
		padding-top: calc(56px + env(safe-area-inset-top));
		padding-bottom: calc(56px + env(safe-area-inset-bottom) + 10px);
		/* Let the page scroll naturally */
		min-height: calc(100vh - 56px - 70px);
	}

	@media (min-width: 1025px) {
		.main {
			margin-left: 280px; /* Sidebar width */
			padding: 32px 48px;
			padding-top: 32px;
			padding-bottom: 32px;
			min-height: auto;
		}
		
		/* If sidebar is collapsed, adjust margin */
		:global(body.col) .main {
			margin-left: 88px;
		}
	}

	@media (max-width: 1024px) {
		.main {
			margin-bottom: 0;
		}
	}

	:global(body) {
		background-color: #f8fafc; /* Use the brand's base slate instead of pure white */
		color: var(--text-main);
	}
	
	.app-container, .main, .main > div {
		background: transparent !important;
	}

	:global(.univote-bottom-nav) {
		background: rgba(255, 255, 255, 0.7) !important;
		backdrop-filter: blur(20px) !important;
		-webkit-backdrop-filter: blur(20px) !important;
		border-top: 1px solid rgba(0, 0, 0, 0.05) !important;
		z-index: 200 !important;
		padding-bottom: env(safe-area-inset-bottom) !important;
	}
</style>
