<script>
	/** @type {{ children: import('svelte').Snippet, headerExtra?: import('svelte').Snippet, title?: string, subtitle?: string }} */
	let { children, headerExtra, title, subtitle } = $props();
</script>

<div class="glass-shell">
	<div class="glass-content">
		<!-- Page Header -->
		{#if title}
			<div class="glass-header">
				<div>
					{#if subtitle}
						<p class="glass-subtitle">{subtitle}</p>
					{/if}
					<h1 class="glass-title">{title}</h1>
				</div>
				{#if headerExtra}
					<div class="glass-header-extra">
						{@render headerExtra()}
					</div>
				{/if}
			</div>
		{/if}

		<!-- Content -->
		<div class="glass-body" style={title ? 'margin-top: 1rem;' : ''}>
			{@render children()}
		</div>
	</div>
</div>

<style>
	.glass-shell {
		background-color: var(--bg-card);
		border: 1px solid var(--border-main);
		border-radius: 16px;
		box-shadow:
			0 4px 24px rgba(0, 0, 0, 0.06),
			0 1px 4px rgba(0, 0, 0, 0.04);
		overflow: hidden;
		transition: box-shadow 0.3s ease, border-color 0.3s ease;
		text-transform: uppercase;
	}

	:global(.dark) .glass-shell {
		box-shadow:
			0 4px 32px rgba(0, 0, 0, 0.3),
			0 1px 4px rgba(0, 0, 0, 0.2);
		border-color: rgba(255, 255, 255, 0.06);
	}

	.glass-content {
		padding: 1.5rem;
	}

	@media (min-width: 640px) {
		.glass-content {
			padding: 1.75rem;
		}
	}

	.glass-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 1rem;
		padding-bottom: 1rem;
		border-bottom: 1px solid var(--border-main);
	}

	.glass-subtitle {
		font-size: 0.625rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.18em;
		color: var(--brand-primary);
		margin: 0;
	}

	.glass-title {
		font-size: 1.375rem;
		font-weight: 800;
		color: var(--text-main);
		letter-spacing: -0.02em;
		margin: 0.3rem 0 0;
		line-height: 1.2;
	}

	.glass-header-extra {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		flex-shrink: 0;
	}

	.glass-body {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}
</style>
