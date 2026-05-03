<script>
	import { Modal, Button } from 'flowbite-svelte';
	import { ExclamationCircleOutline, TrashBinOutline } from 'flowbite-svelte-icons';

	/** @type {{ 
	 *   show: boolean, 
	 *   title: string, 
	 *   message: string, 
	 *   onConfirm: () => void, 
	 *   onCancel: () => void,
	 *   confirmLabel?: string,
	 *   cancelLabel?: string,
	 *   isDanger?: boolean
	 * }} */
	let { 
		show, 
		title, 
		message, 
		onConfirm, 
		onCancel, 
		confirmLabel = 'Confirm', 
		cancelLabel = 'Cancel',
		isDanger = true
	} = $props();

	let open = $derived(show);
</script>

<Modal
	bind:open
	size="sm"
	autoclose={false}
	class="univote-modal"
	on:close={onCancel}
	outsideclose
>
	<svelte:fragment slot="header">
		<div class="modal-header-content">
			{#if isDanger}
				<ExclamationCircleOutline class="modal-icon danger-icon" />
			{/if}
			<span class="modal-title">{title}</span>
		</div>
	</svelte:fragment>

	<p class="modal-message">{message}</p>

	<svelte:fragment slot="footer">
		<div class="modal-actions">
			<Button color="alternative" onclick={onCancel} class="cancel-btn">{cancelLabel}</Button>
			{#if isDanger}
				<Button color="red" onclick={onConfirm} class="confirm-btn">
					<TrashBinOutline size="sm" class="mr-1" />
					{confirmLabel}
				</Button>
			{:else}
				<Button color="primary" onclick={onConfirm} class="confirm-btn">{confirmLabel}</Button>
			{/if}
		</div>
	</svelte:fragment>
</Modal>

<style>
	:global(.univote-modal) {
		font-family: inherit !important;
	}
	.modal-header-content {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}
	:global(.modal-icon) {
		width: 20px !important;
		height: 20px !important;
		flex-shrink: 0;
	}
	:global(.danger-icon) {
		color: #ef4444 !important;
	}
	.modal-title {
		font-size: 1rem;
		font-weight: 700;
		color: var(--text-main);
	}
	.modal-message {
		font-size: 0.875rem;
		color: var(--text-muted);
		line-height: 1.6;
	}
	.modal-actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.5rem;
		width: 100%;
	}
	:global(.cancel-btn), :global(.confirm-btn) {
		font-family: inherit !important;
		font-size: 0.8125rem !important;
		font-weight: 600 !important;
	}
</style>
