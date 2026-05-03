<script>
	import { onMount } from 'svelte';
	import { admin as adminApi } from '$lib/api.js';
	import { branding } from '$lib/stores/branding.js';
	import Notification from '$lib/components/Notification.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import ConfirmModal from '$lib/components/ConfirmModal.svelte';

	/** @type {Array<any>} */
	let elections = $state([]);
	let isLoading = $state(true);
	let electionSearch = $state('');
	let newElection = $state({ name: '', start_date: '', end_date: '', description: '' });
	let isCreating = $state(false);
	let showForm = $state(false);
	let editingElectionId = $state(/** @type {string|null} */ (null));

	// Confirmation Modal State
	let confirmState = $state({
		show: false,
		title: '',
		message: '',
		onConfirm: () => {},
		id: ''
	});

	/** @type {{ text: string, type: 'info' | 'success' | 'error' }} */
	let notification = $state({ text: '', type: 'info' });

	onMount(async () => {
		await loadElections();
	});

	async function loadElections() {
		try {
			const res = await adminApi.getElections();
			elections = res.data ?? [];
		} catch (err) {
			console.error('Failed to load elections:', err);
		} finally {
			isLoading = false;
		}
	}

	const filteredElections = $derived(
		electionSearch
			? elections.filter((e) => e.name.toLowerCase().includes(electionSearch.toLowerCase()))
			: elections
	);

	function notify(text = '', type = /** @type {'info' | 'success' | 'error'} */ ('info')) {
		notification = { text, type };
		setTimeout(() => (notification = { text: '', type: 'info' }), 3500);
	}

	async function handleSubmit(/** @type {SubmitEvent} */ e) {
		e.preventDefault();
		if (!newElection.name || !newElection.start_date || !newElection.end_date) {
			notify('Please fill in all required fields.', 'error');
			return;
		}
		if (new Date(newElection.end_date) <= new Date(newElection.start_date)) {
			notify('End date must be after start date.', 'error');
			return;
		}
		isCreating = true;
		try {
			const payload = {
				...newElection,
				start_date: new Date(newElection.start_date).toISOString(),
				end_date: new Date(newElection.end_date).toISOString()
			};

			if (editingElectionId) {
				await adminApi.updateElection(editingElectionId, payload);
				notify('Election updated successfully', 'success');
			} else {
				await adminApi.createElection(payload);
				notify('Election created successfully', 'success');
			}

			await loadElections();
			resetForm();
		} catch (/** @type {any} */ err) {
			notify(err.message ?? 'Operation failed', 'error');
		} finally {
			isCreating = false;
		}
	}

	function resetForm() {
		newElection = { name: '', start_date: '', end_date: '', description: '' };
		editingElectionId = null;
		showForm = false;
	}

	function openEdit(/** @type {any} */ election) {
		// Convert ISO to local datetime-local format (YYYY-MM-DDTHH:MM)
		const start = new Date(election.start_date);
		const end = new Date(election.end_date);

		// Helper to format for datetime-local
		const fmt = (/** @type {Date} */ d) => {
			const pad = (/** @type {number} */ n) => String(n).padStart(2, '0');
			return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
		};

		newElection = {
			name: election.name,
			start_date: fmt(start),
			end_date: fmt(end),
			description: election.description || ''
		};
		editingElectionId = election.id;
		showForm = true;
		// Scroll to form
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	async function toggleElection(/** @type {string} */ id, /** @type {string} */ current_status) {
		let nextStatus = 'upcoming';
		if (current_status === 'upcoming') nextStatus = 'active';
		else if (current_status === 'active') nextStatus = 'completed';
		try {
			await adminApi.toggleElection(id, /** @type {any} */ (nextStatus));
			const res = await adminApi.getElections();
			elections = res.data ?? [];
			notify('Election status updated', 'success');
		} catch (/** @type {any} */ err) {
			notify(err.message ?? 'Error updating status', 'error');
		}
	}

	function promptDelete(/** @type {any} */ election) {
		confirmState = {
			show: true,
			title: 'Delete Election',
			message: `Are you sure you want to delete "${election.name}"? This will permanently remove all associated candidates and votes.`,
			id: election.id,
			onConfirm: async () => {
				try {
					await adminApi.deleteElection(confirmState.id);
					elections = elections.filter((e) => e.id !== confirmState.id);
					notify('Election deleted', 'success');
				} catch (/** @type {any} */ err) {
					notify(err.message ?? 'Failed to delete election', 'error');
				} finally {
					confirmState.show = false;
				}
			}
		};
	}

	function toggleLabel(/** @type {string} */ status) {
		if (status === 'upcoming') return 'Activate';
		if (status === 'active') return 'Complete';
		return '';
	}
	function toggleVariant(/** @type {string} */ status) {
		if (status === 'upcoming') return 'btn-success btn-sm';
		if (status === 'active') return 'btn-danger btn-sm';
		return '';
	}
</script>

<svelte:head><title>Elections | {$branding.appName}</title></svelte:head>

<div class="dash">
	<div class="dash-header">
		<div>
			<p class="dash-eyebrow"><span class="prefix">Pages /</span> Administrator</p>
			<h1 class="dash-title">Election Management</h1>
		</div>
		<div style="display:flex;gap:0.5rem;align-items:center;">
			<!-- Search -->
			<div style="position:relative;">
				<svg
					style="position:absolute;left:0.75rem;top:50%;transform:translateY(-50%);width:0.875rem;height:0.875rem;color:var(--text-subtle);opacity:0.6;"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					><path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2.5"
						d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
					/></svg
				>
				<input
					bind:value={electionSearch}
					placeholder="Search elections…"
					class="input-base"
					style="padding-left:2.5rem;width:240px;height:2rem;font-size:0.75rem;font-family:sans-serif;"
				/>
			</div>
			<button onclick={loadElections} class="btn-secondary btn-sm">
				<svg
					class="h-3.5 w-3.5"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					viewBox="0 0 24 24"
					><path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"
					/></svg
				>
				Refresh
			</button>
			<button onclick={() => (showForm = !showForm)} class="btn-primary btn-sm">
				<svg
					class="h-3.5 w-3.5"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					viewBox="0 0 24 24"
					><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg
				>
				New Election
			</button>
		</div>
	</div>

	<!-- Create Election Form (collapsible) -->
	{#if showForm}
		<div class="admin-card" style="padding:1.25rem;">
			<div
				style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;"
			>
				<h2 style="font-size:0.875rem;font-weight:600;color:var(--text-main);">
					{editingElectionId ? 'Edit Election' : 'Create New Election'}
				</h2>
				<button onclick={() => (showForm = false)} class="btn-icon" aria-label="Close form">
					<svg
						class="h-4 w-4"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						viewBox="0 0 24 24"
						><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg
					>
				</button>
			</div>
			<form onsubmit={handleSubmit} style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;">
				<div style="grid-column:1/-1;">
					<label class="field-label" for="election_name">Election Name *</label>
					<input
						id="election_name"
						class="input-base"
						bind:value={newElection.name}
						placeholder="e.g. Student Council 2025"
					/>
				</div>
				<div>
					<label class="field-label" for="start_date">Start Date *</label>
					<input
						id="start_date"
						type="datetime-local"
						class="input-base"
						bind:value={newElection.start_date}
					/>
				</div>
				<div>
					<label class="field-label" for="end_date">End Date *</label>
					<input
						id="end_date"
						type="datetime-local"
						class="input-base"
						bind:value={newElection.end_date}
					/>
				</div>
				<div style="grid-column:1/-1;">
					<label class="field-label" for="description">Description</label>
					<input
						id="description"
						class="input-base"
						bind:value={newElection.description}
						placeholder="Optional description"
					/>
				</div>
				<div
					style="grid-column:1/-1;display:flex;gap:0.5rem;justify-content:flex-end;margin-top:0.25rem;"
				>
					<button type="button" onclick={() => (showForm = false)} class="btn-secondary btn-sm"
						>Cancel</button
					>
					<button type="submit" disabled={isCreating} class="btn-primary btn-sm">
						{isCreating ? 'Saving…' : editingElectionId ? 'Update Election' : 'Create Election'}
					</button>
				</div>
			</form>
		</div>
	{/if}

	<!-- Elections Table -->
	<div class="admin-card" style="overflow:hidden;">
		<div
			style="padding:0.75rem 1rem;border-bottom:1px solid var(--border-main);display:flex;align-items:center;justify-content:space-between;"
		>
			<p class="section-label">{filteredElections.length} Election{filteredElections.length !== 1 ? 's' : ''}</p>
		</div>

		{#if isLoading}
			<div style="padding:1.5rem;display:flex;flex-direction:column;gap:0.5rem;">
				{#each Array(4) as _}
					<div class="skeleton" style="height:3rem;"></div>
				{/each}
			</div>
		{:else if filteredElections.length === 0}
			<div class="empty-state">
				{electionSearch ? 'No elections match your search.' : 'No elections yet. Click "New Election" to create one.'}
			</div>
		{:else}
			<div style="overflow-x:auto;">
				<table class="data-table">
					<thead>
						<tr>
							<th>Name</th>
							<th>Status</th>
							<th>Start Date</th>
							<th>End Date</th>
							<th>Voters</th>
							<th>Turnout</th>
							<th style="text-align:right;">Actions</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredElections as election (election.id)}
							<tr>
								<td
									style="font-weight:600;color:var(--text-main);max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
									>{election.name}</td
								>
								<td><StatusBadge status={election.status} /></td>
								<td style="color:var(--text-muted);white-space:nowrap;"
									>{new Date(election.start_date).toLocaleDateString()}</td
								>
								<td style="color:var(--text-muted);white-space:nowrap;"
									>{new Date(election.end_date).toLocaleDateString()}</td
								>
								<td style="color:var(--text-muted);">{election.voters_count ?? 0}</td>
								<td>
									{#if election.voters_count}
										<span style="font-weight:600;color:var(--text-main);"
											>{Math.round((election.votes_cast / election.voters_count) * 100)}%</span
										>
									{:else}
										<span style="color:var(--text-subtle);">—</span>
									{/if}
								</td>
								<td style="text-align:right;white-space:nowrap;">
									{#if election.status !== 'completed'}
										<button
											onclick={() => toggleElection(election.id, election.status)}
											class={toggleVariant(election.status)}>{toggleLabel(election.status)}</button
										>
										{#if election.status === 'upcoming'}
											<button
												onclick={() => openEdit(election)}
												class="btn-icon-edit"
												title="Edit election"
												style="margin-left:0.25rem;"
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
														d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L6.832 19.82a4.5 4.5 0 01-1.897 1.13l-2.685.8.8-2.685a4.5 4.5 0 011.13-1.897L16.863 4.487zm0 0L19.5 7.125"
													/></svg
												>
											</button>
										{/if}
									{/if}
									<button
										onclick={() => promptDelete(election)}
										class="btn-icon-danger"
										title="Delete election"
										style="margin-left:0.25rem;"
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
												d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"
											/></svg
										>
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
</div>

<div style="position:fixed;bottom:1.5rem;right:1.5rem;z-index:110;">
	<Notification text={notification.text} type={notification.type} />
</div>

<ConfirmModal
	show={confirmState.show}
	title={confirmState.title}
	message={confirmState.message}
	onConfirm={confirmState.onConfirm}
	onCancel={() => (confirmState.show = false)}
/>
