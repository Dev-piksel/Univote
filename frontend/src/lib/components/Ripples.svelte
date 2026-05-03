<script>
	import { branding } from '$lib/stores/branding.js';
	const show = $derived($branding.showBgAnims);
</script>

{#if show}
	<div class="ripple-layer top-left" aria-hidden="true">
		<div class="ripple"></div>
	</div>
	<div class="ripple-layer bottom-right" aria-hidden="true">
		<div class="ripple"></div>
	</div>
{/if}

<style>
	.ripple-layer {
		position: absolute;
		inset: 0;
		z-index: 0;
		overflow: hidden;
		pointer-events: none;
		contain: strict;
	}
	.ripple {
		position: absolute;
		width: 120vh; /* Slightly larger for better coverage */
		height: 120vh;
		border: 2px solid rgba(255, 255, 255, 0.03);
		border-radius: 50%;
		opacity: 0;
		transform: translate3d(0,0,0) scale(0);
		will-change: transform, opacity;
		filter: blur(2px); /* Add a liquid soft edge */
		animation: ripple-spread 10s cubic-bezier(0.2, 0.4, 0.3, 0.95) infinite;
	}
	
	.top-left .ripple { top: -60vh; left: -60vh; }
	.bottom-right .ripple { bottom: -60vh; right: -60vh; }
	
	:global(.light) .ripple { 
		border-color: rgba(var(--brand-primary-rgb, 11, 117, 254), 0.2); 
	}

	@keyframes ripple-spread {
		0% { transform: translate3d(0,0,0) scale(0); opacity: 0; }
		5% { opacity: 0.12; }
		100% { transform: translate3d(0,0,0) scale(2); opacity: 0; }
	}
</style>
