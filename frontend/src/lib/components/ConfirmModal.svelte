<script>
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

	function handleBackdropClick(/** @type {MouseEvent} */ e) {
		if (e.target === e.currentTarget) onCancel();
	}
</script>

{#if show}
	<!-- Backdrop -->
	<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
	<div class="modal-backdrop" onclick={handleBackdropClick}>
		<div class="modal-box" role="dialog" aria-modal="true" aria-labelledby="modal-title">
			<!-- Header -->
			<div class="modal-header">
				<div class="modal-header-content">
					{#if isDanger}
						<ExclamationCircleOutline class="modal-icon danger-icon" />
					{/if}
					<span id="modal-title" class="modal-title">{title}</span>
				</div>
				<button class="modal-close-btn" onclick={onCancel} aria-label="Close">
					<svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
					</svg>
				</button>
			</div>

			<!-- Body -->
			<div class="modal-body">
				<p class="modal-message">{message}</p>
			</div>

			<!-- Footer -->
			<div class="modal-footer">
				<button class="cancel-btn" onclick={onCancel}>{cancelLabel}</button>
				{#if isDanger}
					<button class="confirm-btn danger" onclick={onConfirm}>
						<TrashBinOutline class="btn-icon" />
						{confirmLabel}
					</button>
				{:else}
					<button class="confirm-btn primary" onclick={onConfirm}>{confirmLabel}</button>
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		inset: 0;
		z-index: 1000;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(4px);
		-webkit-backdrop-filter: blur(4px);
		padding: 1rem;
		animation: fadeIn 0.15s ease;
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to   { opacity: 1; }
	}

	.modal-box {
		background: var(--bg-card, #1a2035);
		border: 1px solid var(--border-main, rgba(255,255,255,0.1));
		border-radius: 1rem;
		box-shadow: 0 25px 60px rgba(0, 0, 0, 0.5);
		width: 100%;
		max-width: 420px;
		font-family: inherit;
		animation: slideUp 0.2s ease;
		overflow: hidden;
	}

	@keyframes slideUp {
		from { transform: translateY(12px); opacity: 0; }
		to   { transform: translateY(0);    opacity: 1; }
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 1rem 1.25rem;
		border-bottom: 1px solid var(--border-subtle, rgba(255,255,255,0.06));
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
		font-size: 0.9375rem;
		font-weight: 700;
		color: var(--text-main, #fff);
	}

	.modal-close-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		border-radius: 6px;
		background: transparent;
		border: none;
		color: var(--text-subtle, rgba(255,255,255,0.4));
		cursor: pointer;
		transition: background 0.15s, color 0.15s;
	}

	.modal-close-btn:hover {
		background: rgba(255,255,255,0.08);
		color: var(--text-main, #fff);
	}

	.modal-body {
		padding: 1.25rem;
	}

	.modal-message {
		font-size: 0.875rem;
		color: var(--text-muted, rgba(255,255,255,0.6));
		line-height: 1.6;
		margin: 0;
	}

	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: 0.625rem;
		padding: 0.875rem 1.25rem;
		border-top: 1px solid var(--border-subtle, rgba(255,255,255,0.06));
	}

	.cancel-btn {
		padding: 0.5rem 1rem;
		border-radius: 0.5rem;
		font-family: inherit;
		font-size: 0.8125rem;
		font-weight: 600;
		background: transparent;
		border: 1px solid var(--border-main, rgba(255,255,255,0.12));
		color: var(--text-muted, rgba(255,255,255,0.6));
		cursor: pointer;
		transition: all 0.15s;
	}

	.cancel-btn:hover {
		background: rgba(255,255,255,0.06);
		color: var(--text-main, #fff);
	}

	.confirm-btn {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.5rem 1rem;
		border-radius: 0.5rem;
		font-family: inherit;
		font-size: 0.8125rem;
		font-weight: 600;
		border: none;
		cursor: pointer;
		transition: all 0.15s;
	}

	.confirm-btn.danger {
		background: #ef4444;
		color: #fff;
	}

	.confirm-btn.danger:hover {
		background: #dc2626;
	}

	.confirm-btn.primary {
		background: var(--primary-600, #16a34a);
		color: #fff;
	}

	.confirm-btn.primary:hover {
		background: var(--primary-500, #22c55e);
	}

	:global(.btn-icon) {
		width: 14px !important;
		height: 14px !important;
	}
</style>
