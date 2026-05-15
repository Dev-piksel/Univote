<script>
	import {
		CheckCircleOutline,
		ExclamationCircleOutline,
		InfoCircleOutline
	} from 'flowbite-svelte-icons';

	/** @type {{ text?: string, type?: 'info' | 'success' | 'error' | 'warning' }} */
	let { text = '', type = 'info' } = $props();

	const config = {
		success: { bg: '#052e16', border: '#16a34a', iconColor: '#4ade80', Icon: CheckCircleOutline },
		error:   { bg: '#2d0f0f', border: '#ef4444', iconColor: '#f87171', Icon: ExclamationCircleOutline },
		warning: { bg: '#2d1f00', border: '#f59e0b', iconColor: '#fbbf24', Icon: ExclamationCircleOutline },
		info:    { bg: '#0c1a3a', border: '#3b82f6', iconColor: '#60a5fa', Icon: InfoCircleOutline }
	};

	const cfg = $derived(config[type] ?? config.info);

	let visible = $state(false);

	$effect(() => {
		if (text) {
			visible = true;
		} else {
			visible = false;
		}
	});
</script>

{#if text && visible}
	{@const Icon = cfg.Icon}
	<div
		class="toast-wrap"
		style="
			background: {cfg.bg};
			border: 1px solid {cfg.border};
			box-shadow: 0 4px 6px -1px rgba(0,0,0,0.3), 0 0 20px {cfg.border}33;
		"
		role="status"
		aria-live="polite"
	>
		<span class="toast-icon" style="color: {cfg.iconColor};">
			<Icon size="sm" />
		</span>
		<span class="toast-msg">{text}</span>
		<button
			class="toast-close"
			onclick={() => (visible = false)}
			aria-label="Dismiss notification"
			style="color: {cfg.iconColor};"
		>
			<svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
			</svg>
		</button>
	</div>
{/if}

<style>
	.toast-wrap {
		display: flex;
		align-items: center;
		gap: 0.625rem;
		min-width: 280px;
		max-width: 420px;
		padding: 0.75rem 1rem;
		border-radius: 14px;
		backdrop-filter: blur(16px);
		-webkit-backdrop-filter: blur(16px);
		animation: slideIn 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
		font-family: inherit;
	}

	@keyframes slideIn {
		from { opacity: 0; transform: translateY(12px) scale(0.95); }
		to   { opacity: 1; transform: translateY(0)    scale(1); }
	}

	.toast-icon {
		display: flex;
		align-items: center;
		flex-shrink: 0;
	}

	.toast-msg {
		font-size: 0.8125rem;
		font-weight: 600;
		line-height: 1.4;
		color: #fff;
		flex: 1;
	}

	.toast-close {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 20px;
		height: 20px;
		border-radius: 4px;
		border: none;
		background: transparent;
		cursor: pointer;
		flex-shrink: 0;
		opacity: 0.6;
		transition: opacity 0.15s;
	}

	.toast-close:hover {
		opacity: 1;
	}
</style>
