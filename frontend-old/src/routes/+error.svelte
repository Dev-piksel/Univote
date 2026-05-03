<script>
	import { page } from '$app/state';
	import { branding } from '$lib/stores/branding.js';
	import favicon from '$lib/assets/favicon.svg';

	/** @type {Record<number, { title: string, subtitle: string, icon: string }>} */
	const errorDetails = {
		404: {
			title: 'Resource Segregation Error',
			subtitle: 'The requested ballot or path does not exist in the current voter registry.',
			icon: 'M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
		},
		500: {
			title: 'Core Engine Failure',
			subtitle: 'The tally mechanism encountered an unexpected exception during processing.',
			icon: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.268 16c-.77 1.333.192 3 1.732 3z'
		}
	};

	let status = $derived(page.status);
	let message = $derived(page.error?.message || 'Something went wrong on our end.');

	let details = $derived(
		errorDetails[status] || {
			title: 'System Discrepancy',
			subtitle: message,
			icon: 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
		}
	);
</script>

<svelte:head>
	<title>{status} | {$branding.appName} Error</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-surface-main p-6 font-sans">
	<div class="animate-in fade-in zoom-in w-full max-w-md space-y-8 text-center duration-700">
		<!-- Brand Header -->
		<div class="mb-8 flex justify-center">
			<img src={$branding.logoUrl || favicon} alt="{$branding.appName} Logo" class="h-12 w-12 opacity-50 grayscale" />
		</div>

		<!-- Main Error Content -->
		<div
			class="group relative overflow-hidden rounded-[40px] border border-line-subtle bg-surface-card p-12 shadow-2xl"
		>
			<!-- Animated Background Element -->
			<div
				class="absolute -top-24 -right-24 h-48 w-48 rounded-full bg-surface-main transition-transform duration-700 group-hover:scale-110"
			></div>

			<div class="relative">
				<!-- Status Badge -->
				<div
					class="mb-6 inline-flex items-center rounded-full bg-content-main px-4 py-1.5 text-[10px] font-black tracking-widest text-surface-main uppercase shadow-lg"
				>
					Error Protocol {status}
				</div>

				<!-- Icon -->
				<div class="mb-6 flex justify-center">
					<div
						class="flex h-20 w-20 items-center justify-center rounded-3xl border border-line-main bg-surface-elevated text-content-subtle transition-colors duration-500 group-hover:text-content-muted"
					>
						<svg class="h-10 w-10" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="1.5"
								d={details.icon}
							></path>
						</svg>
					</div>
				</div>

				<h1 class="mb-3 text-3xl font-bold tracking-tight text-content-main">
					{details.title}
				</h1>

				<p class="mb-8 leading-relaxed font-medium text-content-muted">
					{details.subtitle}
				</p>

				<div class="flex flex-col gap-3">
					<a
						href="/"
						class="btn-primary group/btn flex w-full items-center justify-center gap-2 !rounded-2xl !py-4 shadow-xl"
					>
						<span>Return to Dashboard</span>
						<svg
							class="h-4 w-4 transition-transform group-hover/btn:translate-x-1"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M14 5l7 7m0 0l-7 7m7-7H3"
							></path>
						</svg>
					</a>

					<button
						onclick={() => window.location.reload()}
						class="btn-secondary w-full !rounded-2xl !py-4"
					>
						Reconnect System
					</button>
				</div>
			</div>
		</div>

		<!-- System Footer -->
		<div class="pt-4">
			<p class="text-[10px] font-black tracking-widest text-content-subtle uppercase">
				{$branding.appName} Automated Recovery Service • v0.0.1
			</p>
		</div>
	</div>
</div>

<style>
	:global(body) {
		background-color: var(--bg-main);
		overflow: hidden;
	}
</style>
