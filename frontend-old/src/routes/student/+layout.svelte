<script>
	import { onMount } from 'svelte';
	import { voterSession } from '$lib/stores/session.js';
	import { setTheme } from '$lib/stores/theme.js';
	import { page } from '$app/state';
	import StudentSidebar from '$lib/components/StudentSidebar.svelte';
	import StudentTopbar from '$lib/components/StudentTopbar.svelte';
	import StudentBottomNav from '$lib/components/StudentBottomNav.svelte';
	import { fade, fly } from 'svelte/transition';

	/** @type {{ children: import('svelte').Snippet }} */
	let { children } = $props();

	// Student voter portal: enforce light mode for maximum legibility
	onMount(() => {
		setTheme('light');
	});

	const showNav = $derived($voterSession && page.url.pathname !== '/student/validate');
	const initials = $derived(
		($voterSession?.full_name || '??')
			.split(' ')
			.slice(0, 2)
			.map((/** @type {string} */ w) => w[0]?.toUpperCase())
			.join('')
	);
</script>

{#if showNav}
	<StudentTopbar {initials} />
	<StudentSidebar student_info={$voterSession} />
	
	<main class="main">
		{#key page.url.pathname}
			<div in:fly={{ y: 8, duration: 400, delay: 100 }} out:fade={{ duration: 250 }} class="flex-1 flex flex-col">
				{@render children()}
			</div>
		{/key}
	</main>

	<StudentBottomNav />
{:else}
	<div class="min-h-screen">
		{#key page.url.pathname}
			<div in:fade={{ duration: 400 }}>
				{@render children()}
			</div>
		{/key}
	</div>
{/if}

<style>
	:global(body) {
		background-color: var(--bg);
		margin: 0;
		padding: 0;
	}

	.main {
		flex: 1;
		min-height: 100vh;
		background-color: var(--bg);
		transition: padding var(--ease);
		padding: 30px 24px 100px; /* space for bottom nav on mobile */
		display: flex;
		flex-direction: column;
	}

	/* Desktop Adjustments */
	@media (min-width: 768px) {
		.main {
			padding: 40px 48px;
			margin-left: var(--sw);
		}
		
		:global(body.col) .main {
			margin-left: var(--sc);
		}
	}
</style>

