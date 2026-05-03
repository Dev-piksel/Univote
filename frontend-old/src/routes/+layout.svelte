<script>
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { theme } from '$lib/stores/theme.js';
	import { loadBranding } from '$lib/stores/branding.js';
	import { onMount } from 'svelte';

	let { children } = $props();

	onMount(() => {
		// Apply custom branding (colors + logo) from API on every page load
		loadBranding();

		const unsub = theme.subscribe((val) => {
			if (val === 'dark') {
				document.documentElement.classList.add('dark');
			} else {
				document.documentElement.classList.remove('dark');
			}
		});
		return unsub;
	});
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>



{@render children()}
