<script>
	import { Toast } from 'flowbite-svelte';
	import {
		CheckCircleOutline,
		ExclamationCircleOutline,
		InfoCircleOutline
	} from 'flowbite-svelte-icons';

	/** @type {{ text?: string, type?: 'info' | 'success' | 'error' | 'warning' }} */
	let { text = '', type = 'info' } = $props();

	const config = {
		success: { color: 'green',   Icon: CheckCircleOutline },
		error:   { color: 'red',     Icon: ExclamationCircleOutline },
		warning: { color: 'yellow',  Icon: ExclamationCircleOutline },
		info:    { color: 'blue',    Icon: InfoCircleOutline }
	};

	let open = $state(false);
	let dismissed = $state(false);

	$effect(() => {
		if (text) {
			dismissed = false;
			open = true;
		} else {
			open = false;
		}
	});

	const cfg = $derived(config[type] ?? config.info);
</script>

{#if text && open && !dismissed}
	{@const Icon = cfg.Icon}
	<Toast
		color={cfg.color}
		bind:open
		on:close={() => (dismissed = true)}
		class="univote-toast"
		position="bottom-right"
		dismissable
	>
		<svelte:fragment slot="icon">
			<Icon size="sm" />
		</svelte:fragment>
		<span class="toast-msg">{text}</span>
	</Toast>
{/if}

<style>
	:global(.univote-toast) {
		min-width: 280px !important;
		max-width: 420px !important;
		font-family: inherit !important;
		font-size: 0.8125rem !important;
		font-weight: 600 !important;
		box-shadow:
			0 4px 6px -1px rgba(0,0,0,0.10),
			0 12px 28px -6px rgba(0,0,0,0.16) !important;
		border-radius: 14px !important;
	}
	.toast-msg {
		font-size: 0.8125rem;
		font-weight: 600;
		line-height: 1.4;
	}
</style>
