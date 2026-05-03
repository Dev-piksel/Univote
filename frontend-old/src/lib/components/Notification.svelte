<script>
	/** @type {{ text?: string, type?: 'info' | 'success' | 'error' }} */
	let { text = '', type = 'info' } = $props();

	/** @type {Record<'info' | 'success' | 'error', string>} */
	const styles = {
		info: 'bg-[var(--status-info-bg)] border-[var(--status-info-fg)]/30 text-[var(--status-info-fg)]',
		success:
			'bg-[var(--status-success-bg)] border-[var(--status-success-fg)]/30 text-[var(--status-success-fg)]',
		error:
			'bg-[var(--status-danger-bg)] border-[var(--status-danger-fg)]/30 text-[var(--status-danger-fg)]'
	};
</script>

{#if text}
	<div
		class="animate-in slide-in-from-bottom-5 fade-in fixed right-6 bottom-6 flex items-center
           gap-3 rounded-xl border px-6 py-4 shadow-2xl duration-300
           {styles[type]}"
	>
		<div class="h-2 w-2 animate-pulse rounded-full bg-current"></div>
		<span>{text}</span>
	</div>
{/if}
