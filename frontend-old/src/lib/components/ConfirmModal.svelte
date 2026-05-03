<script>
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

	function handleOverlayClick(/** @type {MouseEvent} */ e) {
		if (e.target === e.currentTarget) {
			onCancel();
		}
	}
</script>

{#if show}
	<div 
		class="modal-overlay" 
		onclick={handleOverlayClick}
		role="button"
		tabindex="-1"
		onkeydown={(e) => e.key === 'Escape' && onCancel()}
	>
		<div class="modal-content bento-card">
			<div class="modal-header">
				<h3 class="modal-title">{title}</h3>
				<button onclick={onCancel} class="btn-icon" aria-label="Close">
					<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
					</svg>
				</button>
			</div>
			<div class="modal-body">
				<p>{message}</p>
			</div>
			<div class="modal-footer">
				<button onclick={onCancel} class="btn-secondary btn-sm">{cancelLabel}</button>
				<button 
					onclick={onConfirm} 
					class={isDanger ? 'btn-danger-solid btn-sm' : 'btn-primary btn-sm'}
				>
					{confirmLabel}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.4);
		backdrop-filter: blur(8px);
		-webkit-backdrop-filter: blur(8px);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: 1rem;
		animation: fadeIn 0.15s ease-out;
	}

	.modal-content {
		width: 100%;
		max-width: 400px;
		background: var(--bg-card);
		padding: 1.5rem;
		box-shadow: var(--shadow-modal);
		animation: slideUp 0.15s ease-out;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		border-radius: 16px;
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.modal-title {
		font-size: 1rem;
		font-weight: 700;
		color: var(--text-main);
	}

	.modal-body p {
		font-size: 0.875rem;
		color: var(--text-muted);
		line-height: 1.5;
	}

	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: 0.5rem;
		margin-top: 0.5rem;
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}

	@keyframes slideUp {
		from { transform: translateY(10px); opacity: 0; }
		to { transform: translateY(0); opacity: 1; }
	}

	.h-4 { height: 16px; }
	.w-4 { width: 16px; }
</style>
