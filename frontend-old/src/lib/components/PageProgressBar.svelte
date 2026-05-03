<script>
	import { navigating } from '$app/state';
	import { fade } from 'svelte/transition';

	let visible = $derived(!!navigating);
	/** @type {number} */
	let progress = $state(0);
	/** @type {ReturnType<typeof setInterval> | undefined} */
	let interval;

	$effect(() => {
		if (visible) {
			progress = 0;
			interval = setInterval(() => {
				if (progress < 90) progress += Math.random() * 10;
			}, 200);
		} else {
			progress = 100;
			if (interval) clearInterval(interval);
			const timer = setTimeout(() => { progress = 0; }, 400);
			return () => clearTimeout(timer);
		}
		return () => { if (interval) clearInterval(interval); };
	});
</script>

{#if visible || progress > 0}
	<div class="progress-bar-wrap" out:fade={{ duration: 400 }}>
		<div class="progress-bar" style="width: {progress}%"></div>
	</div>
{/if}

<style>
	.progress-bar-wrap {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		height: 3px;
		z-index: 9999;
		pointer-events: none;
	}
	.progress-bar {
		height: 100%;
		background: var(--brand-gradient);
		box-shadow: 0 0 10px var(--accent);
		transition: width 0.3s ease;
	}
</style>
