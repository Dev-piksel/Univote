<script>
	/** @type {{ status: string, dot?: boolean }} */
	let { status, dot = true } = $props();

	const config = {
		active: { label: 'Active', cls: 'pill-success' },
		completed: { label: 'Completed', cls: 'pill-neutral' },
		upcoming: { label: 'Upcoming', cls: 'pill-info' },
		paused: { label: 'Paused', cls: 'pill-warning' },
		voted: { label: 'Voted', cls: 'pill-success' },
		pending: { label: 'Pending', cls: 'pill-warning' },
		cancelled: { label: 'Cancelled', cls: 'pill-danger' },
		draft: { label: 'Draft', cls: 'pill-neutral' }
	};

	const cfg = $derived((/** @type {any} */ (config))[status?.toLowerCase()] ?? { label: status, cls: 'pill-neutral' });
</script>

<span class="pill {cfg.cls} {dot ? 'pill-dot' : ''}">{cfg.label}</span>
