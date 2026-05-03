<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authSession } from '$lib/stores/auth.js';
	import { theme, setTheme } from '$lib/stores/theme.js';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Ripples from '$lib/components/Ripples.svelte';
	import { branding } from '$lib/stores/branding.js';
	import { fly } from 'svelte/transition';

	/** @type {{ children: import('svelte').Snippet }} */
	let { children } = $props();
	let isChecking = $state(true);

	onMount(() => {
		const unsub = authSession.subscribe((session) => {
			if (!session) {
				goto('/login');
			} else if (session.role === 'adviser') {
				goto('/adviser');
			} else if (session.role === 'super_admin' || session.role === 'dept_admin') {
				// Admin/Adviser dashboard: follow global theme but stay visually dark
				isChecking = false;
			} else {
				goto('/login');
			}
		});

		return unsub;
	});
</script>

{#if !isChecking}
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

		<!-- Content Layer -->
		<div class="relative z-10">
			<Sidebar role={$authSession?.role} student_info={$authSession}>
				<div
					style="display:flex;justify-content:flex-end;margin-bottom:1.5rem;"
					in:fly={{ y: -10, duration: 400 }}
				></div>
				{@render children()}
			</Sidebar>
		</div>
	</div>
{:else}
	<div class="flex min-h-screen items-center justify-center bg-[#02040a]">
		<div class="relative">
			<div class="h-16 w-16 animate-spin rounded-full border-4 border-white/5 border-t-[var(--brand-primary)] shadow-[0_0_20px_var(--brand-glow)]"></div>
			<div class="absolute inset-0 flex items-center justify-center">
				<div class="h-8 w-8 rounded-full bg-white/5 backdrop-blur-xl animate-pulse"></div>
			</div>
		</div>
	</div>
{/if}

<style>
	@keyframes blob {
		0% { transform: translate(0, 0) scale(1); border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
		33% { transform: translate(5%, 10%) scale(1.1); border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; }
		66% { transform: translate(-5%, 5%) scale(0.9); border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
		100% { transform: translate(0, 0) scale(1); border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
	}
	.animate-blob {
		animation: blob 7s infinite;
	}

	.animation-delay-2000 {
		animation-delay: 2s;
	}

	.animation-delay-4000 {
		animation-delay: 4s;
	}
</style>
