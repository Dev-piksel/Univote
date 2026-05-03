<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authSession } from '$lib/stores/auth.js';
	import { theme, setTheme } from '$lib/stores/theme.js';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import { fly } from 'svelte/transition';

	/** @type {{ children: import('svelte').Snippet }} */
	let { children } = $props();
	let isChecking = $state(true);

	onMount(() => {
		const unsub = authSession.subscribe((session) => {
			if (!session) {
				goto('/login');
			} else if (session.role === 'super_admin' || session.role === 'dept_admin') {
				goto('/admin');
			} else if (session.role === 'adviser') {
				// Force password change for imported advisers on first login
				if (session.must_change_password) {
					if (page.url.pathname !== '/adviser/change-password') {
						goto('/adviser/change-password');
						return;
					}
					// If already on the page, allow rendering without sidebar
					isChecking = false;
					return;
				}
				// Adviser dashboard: follow global theme but stay visually dark
				isChecking = false;
			} else {
				goto('/login');
			}
		});

		return unsub;
	});
</script>

{#if !isChecking}
	{#if $authSession.must_change_password}
		<main class="flex min-h-screen items-center justify-center p-6">
			{@render children()}
		</main>
	{:else}
		<div class="min-h-screen transition-all duration-700 relative" style="background-color: {$branding.showBgAnims ? 'transparent' : 'var(--bg-main)'}">
			<!-- Background Layer (Fixed) -->
			<div class="fixed inset-0 z-0 pointer-events-none overflow-hidden">
				<!-- Optimized Liquid Blobs -->
				{#if $branding.showBgAnims}
					<div class="absolute top-[-15%] left-[-15%] w-[80%] h-[80%] rounded-full blur-[80px] opacity-15 animate-blob" style="background-color: var(--brand-primary); will-change: transform, border-radius;"></div>
					<div class="absolute bottom-[-15%] right-[-15%] w-[80%] h-[80%] rounded-full blur-[80px] opacity-10 animate-blob animation-delay-4000" style="background-color: var(--brand-secondary); will-change: transform, border-radius;"></div>
				{/if}
				
				<!-- Grid Overlay -->
				<div class="absolute inset-0 bg-[linear-gradient(to_right,#ffffff03_1px,transparent_1px),linear-gradient(to_bottom,#ffffff03_1px,transparent_1px)] bg-[size:48px_48px] [mask-image:radial-gradient(ellipse_80%_80%_at_50%_20%,#000_60%,transparent_100%)]"></div>

				<!-- Water Ripple Effect (Global Component) -->
				<Ripples />
			</div>

			<Sidebar role="adviser" student_info={$authSession}>
				<div class="p-6 md:p-10 relative z-10">
					{@render children()}
				</div>
			</Sidebar>
		</div>
	{/if}
{:else}
	<div class="flex min-h-screen items-center justify-center bg-surface-main">
		<div
			class="h-8 w-8 animate-spin rounded-full border-4 border-fuchsia-500/30 border-t-fuchsia-500"
		></div>
	</div>
{/if}
