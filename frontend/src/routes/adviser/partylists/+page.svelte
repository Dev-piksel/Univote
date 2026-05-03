<script>
	import { onMount } from 'svelte';
	import { admin, adviser } from '$lib/api.js';
	import { selectedElectionId } from '$lib/stores/election.js';
	import { branding } from '$lib/stores/branding.js';
	import GlassCard from '$lib/components/GlassCard.svelte';
	import { toast } from '$lib/stores/toast.js';
	import { compressImage } from '$lib/image-utils.js';

	/** @type {any[]} */
	let elections = $state([]);
	/** @type {any[]} */
	let partylists = $state([]);

	let newPartylist = $state('');
	let newLogoUrl = $state('');
	let editingPartylistId = $state(/** @type {string | null} */ (null));
	let editingPartylistName = $state('');
	let editingLogoUrl = $state('');

	let isCompressing = $state(false);
	let isSubmitting = $state(false);

	/** @param {Event} e */
	function handleLogoUpload(e) {
		const target = /** @type {HTMLInputElement} */ (e.target);
		const file = target.files?.[0];
		if (!file) return;

		if (file.size > 2 * 1024 * 1024) {
			toast.error('Logo must be smaller than 2MB');
			return;
		}

		isCompressing = true;
		const reader = new FileReader();
		reader.onload = async () => {
			const result = /** @type {string} */ (reader.result);
			try {
				// Optimal thumbnail size for logos
				const compressed = await compressImage(result, 300, 300, 0.5);
				if (editingPartylistId) {
					editingLogoUrl = compressed;
				} else {
					newLogoUrl = compressed;
				}
			} catch (err) {
				console.error('Compression failed:', err);
				toast.error('Failed to process image.');
			} finally {
				isCompressing = false;
			}
		};
		reader.readAsDataURL(file);
	}

	async function loadElections() {
		try {
			const res = await adviser.getElections();
			elections = res.data || [];
		} catch (err) {
			console.error('Failed to load elections:', err);
		}
	}

	async function loadPartylists() {
		if (!$selectedElectionId) return;
		try {
			const res = await adviser.getPartylists($selectedElectionId);
			partylists = res.data || [];
		} catch (err) {
			console.error('Failed to load partylists:', err);
			toast.error('Failed to refresh partylists list.');
		}
	}

	onMount(async () => {
		await loadElections();
		if ($selectedElectionId) await loadPartylists();
	});

	$effect(() => {
		if ($selectedElectionId) {
			loadPartylists();
		}
	});

	const selectedElection = $derived(() =>
		elections.find(/** @param {any} e */ (e) => e.id === $selectedElectionId)
	);
	const isModifiable = $derived(() => selectedElection()?.status === 'upcoming');

	/** @param {SubmitEvent} e */
	async function handleAddPartylist(e) {
		e.preventDefault();
		if (!newPartylist || !$selectedElectionId) return;
		if (!isModifiable()) {
			toast.error('Cannot add partylist to an active/completed election.');
			return;
		}
		isSubmitting = true;
		try {
			const res = await adviser.createPartylist($selectedElectionId, newPartylist);
			
			// NON-BLOCKING Logo Upload
			if (newLogoUrl) {
				adviser.updatePartylistLogo(res.data[0].id, newLogoUrl)
					.then(() => {
						toast.success('Logo uploaded!');
						loadData();
					})
					.catch(err => {
						console.error('Logo upload failed:', err);
						toast.error('Partylist created, but logo upload failed.');
					});
			}

			newPartylist = '';
			newLogoUrl = '';
			toast.success('Partylist added successfully!');
			await loadPartylists();
		} catch (/** @type {any} */ err) {
			toast.error(err.message || 'Failed to add partylist.');
		} finally {
			isSubmitting = false;
		}
	}

	/** @param {string} id */
	async function handleDeletePartylist(id) {
		if (!isModifiable()) {
			toast.error('Cannot delete from an active/completed election.');
			return;
		}
		if (
			!confirm(
				'Are you sure? Deleting this partylist will also DELETE all candidates associated with it.'
			)
		)
			return;
		try {
			await adviser.deletePartylist(id);
			toast.success('Partylist and its candidates deleted.');
			await loadPartylists();
		} catch (/** @type {any} */ err) {
			toast.error(err.message || 'Failed to delete partylist.');
		}
	}

	function startEditPartylist(/** @type {any} */ party) {
		if (!isModifiable()) {
			toast.error('Cannot edit an active/completed election.');
			return;
		}
		editingPartylistId = party.id;
		editingPartylistName = party.name;
		editingLogoUrl = party.logo_url || '';
	}

	async function handleUpdatePartylist() {
		if (!editingPartylistId || !editingPartylistName) return;
		try {
			await adviser.updatePartylist(editingPartylistId, editingPartylistName);
			if (editingLogoUrl) {
				await adviser.updatePartylistLogo(editingPartylistId, editingLogoUrl);
			}
			editingPartylistId = null;
			editingLogoUrl = '';
			toast.success('Partylist updated successfully!');
			await loadPartylists();
		} catch (/** @type {any} */ err) {
			toast.error(err.message || 'Failed to update partylist.');
		}
	}
</script>

<svelte:head><title>Partylists | {$branding.appName}</title></svelte:head>

<div class="dash">
	<div class="dash-header">
		<div>
			<p class="dash-eyebrow"><span class="prefix">Pages /</span> Partylists</p>
			<h1 class="dash-title">Partylists</h1>
		</div>
		<div style="display:flex;align-items:center;gap:0.75rem;">
			<label for="election-select" class="field-label" style="margin-bottom:0;line-height:1;"
				>Election</label
			>
			<select
				id="election-select"
				bind:value={$selectedElectionId}
				class="input-base"
				style="min-width:200px; width:auto; max-width:450px; padding:0.375rem 0.75rem; font-size:0.8125rem;"
			>
				<option value="" disabled>Select Election...</option>
				{#each elections as election}
					<option value={election.id}>{election.name}</option>
				{/each}
			</select>
		</div>
	</div>

	{#if !$selectedElectionId}
		<div class="empty-state">
			Please select an election from the dropdown above to manage its partylists.
		</div>
	{:else}
		<div class="bento-grid" style="grid-template-columns: 1fr 2.5fr; gap: 1rem;">
			<!-- Form -->
			<div class="admin-card" style="padding:1.25rem;height:fit-content;">
				<div style="margin-bottom:1.25rem;">
					<h2 style="font-size:0.875rem;font-weight:600;color:var(--text-main);">Add Partylist</h2>
				</div>

				<form onsubmit={handleAddPartylist} style="display:flex;flex-direction:column;gap:1rem;">
					<div>
						<label class="field-label" for="party-name">Partylist Name</label>
						<input
							id="party-name"
							type="text"
							bind:value={newPartylist}
							class="input-base"
							placeholder="e.g. Student Forward"
						/>
					</div>

					<div>
						<label class="field-label" for="party-logo">Logo (Optional)</label>
						<div class="flex items-center gap-4">
							{#if newLogoUrl}
								<img src={newLogoUrl} alt="Preview" class="w-12 h-12 rounded-lg object-contain bg-white/5 border border-white/10" />
							{/if}
							<input
								id="party-logo"
								type="file"
								accept="image/*"
								onchange={handleLogoUpload}
								class="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
							/>
						</div>
					</div>


					<button
						type="submit"
						disabled={isSubmitting || !isModifiable()}
						class="btn-primary"
						style="margin-top:0.5rem;"
					>
						{isSubmitting ? 'Adding...' : 'Add Partylist'}
					</button>
				</form>
			</div>

			<!-- List -->
			<div class="admin-card" style="overflow:hidden;">
				<div style="padding:0.75rem 1rem;border-bottom:1px solid var(--border-main);">
					<h2 style="font-size:0.875rem;font-weight:600;color:var(--text-main);">
						{partylists.length} Partylist{partylists.length !== 1 ? 's' : ''}
					</h2>
				</div>

				{#if partylists.length === 0}
					<div class="empty-state" style="border:none;border-radius:0;">
						No partylists added for this election yet.
					</div>
				{:else}
					<div class="bento-grid bento-2col" style="padding:1rem;gap:1rem;">
						{#each partylists as party}
							<div
								style="border:1px solid var(--border-main);border-radius:6px;padding:1rem;display:flex;flex-direction:column;gap:0.75rem;"
							>
								{#if editingPartylistId === party.id}
									<div class="flex flex-col gap-3">
										<input
											type="text"
											bind:value={editingPartylistName}
											class="input-base"
											placeholder="Partylist Name"
										/>
										<div class="flex items-center gap-3">
											{#if editingLogoUrl}
												<img src={editingLogoUrl} alt="Logo" class="w-10 h-10 rounded-lg object-contain bg-white/5" />
											{/if}
											<input type="file" accept="image/*" onchange={handleLogoUpload} class="text-[10px] flex-1" />
										</div>
									</div>
									<div style="display:flex;gap:0.5rem;">
										<button onclick={handleUpdatePartylist} class="btn-primary btn-sm flex-1"
											>Save</button
										>
										<button
											onclick={() => (editingPartylistId = null)}
											class="btn-secondary btn-sm flex-1">Cancel</button
										>
									</div>
								{:else}
									<div style="display:flex;align-items:center;justify-content:space-between;gap:1rem;">
										<div class="flex items-center gap-3 min-w-0">
											{#if party.logo_url}
												<img src={party.logo_url} alt="Logo" class="w-10 h-10 rounded-lg object-contain bg-white/5 border border-white/10 shrink-0" />
											{:else}
												<div class="w-10 h-10 rounded-lg bg-black/10 flex items-center justify-center shrink-0">
													<svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
												</div>
											{/if}
											<h3
												style="font-weight:600;font-size:0.875rem;color:var(--text-main);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
												title={party.name}
											>
												{party.name}
											</h3>
										</div>
										<div style="display:flex;gap:0.25rem;">
											{#if isModifiable()}
												<button
													onclick={() => startEditPartylist(party)}
													class="btn-icon-edit"
													title="Edit"
												>
													<svg
														class="h-4 w-4"
														fill="none"
														stroke="currentColor"
														stroke-width="2"
														viewBox="0 0 24 24"
														><path
															stroke-linecap="round"
															stroke-linejoin="round"
															d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"
														/></svg
													>
												</button>
												<button
													onclick={() => handleDeletePartylist(party.id)}
													class="btn-icon-danger"
													title="Delete"
												>
													<svg
														class="h-4 w-4"
														fill="none"
														stroke="currentColor"
														stroke-width="2"
														viewBox="0 0 24 24"
														><path
															stroke-linecap="round"
															stroke-linejoin="round"
															d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
														/></svg
													>
												</button>
											{/if}
										</div>
									</div>
									<p style="font-size:0.6875rem;color:var(--text-subtle);font-family:monospace;">
										ID: {party.id.substring(0, 8)}
									</p>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>
