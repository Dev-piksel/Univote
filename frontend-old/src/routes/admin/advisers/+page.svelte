<script>
	import { onMount } from 'svelte';
	import { admin as adminApi } from '$lib/api.js';
	import { branding } from '$lib/stores/branding.js';
	import Notification from '$lib/components/Notification.svelte';
	import ConfirmModal from '$lib/components/ConfirmModal.svelte';

	/** @type {Array<any>} */
	let advisers = $state([]);
	let isLoading = $state(true);
	let adviserSearch = $state('');
	let newAdviser = $state({ full_name: '', email: '', id_number: '', password: '', department: '' });
	let isAdding = $state(false);
	let showForm = $state(false);
	let showImport = $state(false);
	let isImporting = $state(false);
	/** @type {Array<{full_name:string,email:string,employee_id:string,default_password:string}>} */
	let importResults = $state([]);
	/** @type {Array<any>} */
	let importSkipped = $state([]);

	let pageHistory = $state([/** @type {string | null} */ (null)]);
	let currentPage = $state(0);
	let nextPageToken = $state(/** @type {string | null} */ (null));

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
		await loadAdvisers();
	});

	async function loadAdvisers(/** @type {string | null} */ token = null) {
		try {
			isLoading = true;
			const res = await adminApi.getAdvisers(15, token);
			advisers = res.data ?? [];
			nextPageToken = res.next_page_token ?? null;
		} catch (err) {
			console.error('Failed to load advisers:', err);
		} finally {
			isLoading = false;
		}
	}

	async function goNext() {
		if (!nextPageToken || isLoading) return;
		pageHistory.push(nextPageToken);
		currentPage++;
		await loadAdvisers(nextPageToken);
	}

	async function goPrev() {
		if (currentPage === 0 || isLoading) return;
		currentPage--;
		pageHistory.pop();
		const prevToken = pageHistory[currentPage];
		await loadAdvisers(prevToken);
	}

	const filteredAdvisers = $derived(
		adviserSearch
			? advisers.filter(
					(a) =>
						a.full_name.toLowerCase().includes(adviserSearch.toLowerCase()) ||
						a.email.toLowerCase().includes(adviserSearch.toLowerCase()) ||
						a.id_number?.toLowerCase().includes(adviserSearch.toLowerCase())
				)
			: advisers
	);

	function notify(text = '', type = /** @type {'info' | 'success' | 'error'} */ ('info')) {
		notification = { text, type };
		setTimeout(() => (notification = { text: '', type: 'info' }), 3500);
	}

	async function handleAdd(/** @type {SubmitEvent} */ e) {
		e.preventDefault();
		if (!newAdviser.email || !newAdviser.password || !newAdviser.full_name) {
			notify('Name, email, and password are required.', 'error');
			return;
		}
		isAdding = true;
		try {
			const res = await adminApi.createAdviser(newAdviser);
			newAdviser = { email: '', id_number: '', password: '', full_name: '', department: '' };
			showForm = false;
			notify('Adviser account created', 'success');
			await loadAdvisers();
		} catch (/** @type {any} */ err) {
			notify(err.message ?? 'Failed to create adviser', 'error');
		} finally {
			isAdding = false;
		}
	}

	function promptDelete(/** @type {any} */ adviser) {
		confirmState = {
			show: true,
			title: 'Revoke Access',
			message: `Are you sure you want to delete the adviser account for ${adviser.full_name}? This action cannot be undone.`,
			id: adviser.id,
			onConfirm: async () => {
				try {
					await adminApi.deleteAdviser(confirmState.id);
					advisers = advisers.filter((a) => a.id !== confirmState.id);
					notify('Adviser account removed', 'success');
				} catch (/** @type {any} */ err) {
					notify(err.message ?? 'Failed to delete adviser', 'error');
				} finally {
					confirmState.show = false;
				}
			}
		};
	}
	async function handleImport(/** @type {Event} */ e) {
		const input = /** @type {HTMLInputElement} */ (e.target);
		const file = input.files?.[0];
		if (!file) return;
		isImporting = true;
		importResults = [];
		importSkipped = [];
		try {
			const fd = new FormData();
			fd.append('file', file);
			const res = await adminApi.importAdvisers(fd);
			importResults = res.created ?? [];
			importSkipped = res.skipped ?? [];
			notify(res.message ?? 'Import complete', importResults.length > 0 ? 'success' : 'info');
			await loadAdvisers();
		} catch (/** @type {any} */ err) {
			notify(err.message ?? 'Import failed', 'error');
		} finally {
			isImporting = false;
			input.value = '';
		}
	}

	function copyToClipboard(/** @type {string} */ text) {
		navigator.clipboard?.writeText(text).then(() => notify('Copied!', 'success'));
	}
</script>

<svelte:head><title>Advisers | {$branding.appName}</title></svelte:head>

<div class="dash">
	<div class="dash-header">
		<div>
			<p class="dash-eyebrow"><span class="prefix">Pages /</span> Administrator</p>
			<h1 class="dash-title">Adviser Registry</h1>
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
					bind:value={adviserSearch}
					placeholder="Search advisers…"
					class="input-base"
					style="padding-left:2.5rem;width:240px;height:2rem;font-size:0.75rem;font-family:sans-serif;"
				/>
			</div>
			<button onclick={() => loadAdvisers()} class="btn-secondary btn-sm">
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
			<button onclick={() => { showImport = !showImport; showForm = false; }} class="btn-secondary btn-sm">
				<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
					><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/></svg
				>
				Import CSV
			</button>
			<button onclick={() => { showForm = !showForm; showImport = false; }} class="btn-primary btn-sm">
				<svg
					class="h-3.5 w-3.5"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					viewBox="0 0 24 24"
					><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg
				>
				Add Adviser
			</button>
		</div>
	</div>

	<!-- Import Panel -->
	{#if showImport}
		<div class="admin-card" style="padding:1.25rem;">
			<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">
				<h2 style="font-size:0.875rem;font-weight:600;color:var(--text-main);">Bulk Import Advisers via CSV</h2>
				<button onclick={() => (showImport = false)} class="btn-icon" aria-label="Close"><svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg></button>
			</div>

			<div style="display:flex;flex-direction:column;gap:0.75rem;">
				<p style="font-size:0.8125rem;color:var(--text-subtle);">
					Upload a CSV file with columns: <code style="background:var(--bg-elevated);padding:1px 5px;border-radius:4px;">full_name, email, employee_id, department</code>.
					<strong>employee_id</strong> is required and becomes the login ID. Each adviser must change their password on first login.
				</p>
				<div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;">
					<label class="btn-primary btn-sm" style="cursor:pointer;display:inline-flex;align-items:center;gap:0.4rem;">
						{#if isImporting}
							<span style="width:12px;height:12px;border:2px solid rgba(0,0,0,0.2);border-top-color:#0f172a;border-radius:50%;animation:spin 0.7s linear infinite;display:inline-block;"></span>
							Importing…
						{:else}
							<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/></svg>
							Choose CSV File
						{/if}
						<input type="file" accept=".csv,text/csv" style="display:none;" onchange={handleImport} disabled={isImporting} />
					</label>
					<a
						href={adminApi.downloadAdviserTemplate()}
						download="advisers_template.csv"
						class="btn-secondary btn-sm"
						style="display:inline-flex;align-items:center;gap:0.4rem;text-decoration:none;"
					>
						<svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5 0l-4.5 4.5m0 0L12 16.5m-1.5 4.5V3"/></svg>
						Download Template
					</a>
				</div>

				<!-- Import results -->
				{#if importResults.length > 0}
					<div style="margin-top:0.75rem;">
						<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem;">
							<p style="font-size:0.75rem;font-weight:700;color:var(--text-main);">
								✅ {importResults.length} adviser(s) created — share these credentials:
							</p>
							<button 
								class="btn-primary btn-sm" 
								style="font-size:0.6875rem;"
								onclick={() => {
									const list = importResults.map(r => `Full Name: ${r.full_name}\nID: ${r.employee_id}\nPassword: ${r.default_password}`).join('\n\n---\n\n');
									copyToClipboard(list);
									notify('All credentials copied to clipboard!', 'success');
								}}
							>
								Copy All Credentials
							</button>
						</div>
						<div style="overflow-x:auto;max-height:300px;border:1px solid var(--border-subtle);border-radius:12px;">
							<table class="data-table" style="font-size:0.75rem;">
								<thead>
									<tr>
										<th>Full Name</th>
										<th>Employee ID (Login)</th>
										<th>Temporary Password</th>
										<th></th>
									</tr>
								</thead>
								<tbody>
									{#each importResults as r}
										<tr>
											<td style="font-weight:600;">{r.full_name}</td>
											<td><code style="background:var(--bg-elevated);padding:1px 5px;border-radius:4px;">{r.employee_id}</code></td>
											<td><code style="background:var(--bg-elevated);padding:1px 5px;border-radius:4px;">{r.default_password}</code></td>
											<td style="text-align:right;">
												<button
													class="btn-secondary btn-sm"
													style="padding:0.2rem 0.5rem;font-size:0.6875rem;"
													onclick={() => copyToClipboard(`Employee ID: ${r.employee_id}\nPassword: ${r.default_password}`)}
												>Copy</button>
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
						<p style="font-size:0.6875rem;color:var(--text-subtle);margin-top:0.5rem;">⚠️ Save these credentials now — passwords are not stored in plaintext.</p>
					</div>
				{/if}
				{#if importSkipped.length > 0}
					<p style="font-size:0.75rem;color:var(--status-warning-fg,#d97706);margin-top:0.25rem;">⚠️ {importSkipped.length} row(s) skipped (duplicate email or missing fields).</p>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Add Adviser Form -->
	{#if showForm}
		<div class="admin-card" style="padding:1.25rem;">
			<div
				style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;"
			>
				<h2 style="font-size:0.875rem;font-weight:600;color:var(--text-main);">
					Create Adviser Account
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
			<form onsubmit={handleAdd} style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;">
				<div>
					<label class="field-label" for="adviser_full_name">Full Name *</label>
					<input
						id="adviser_full_name"
						class="input-base"
						bind:value={newAdviser.full_name}
						placeholder="e.g. Prof. Jane Doe"
					/>
				</div>
				<div>
					<label class="field-label" for="adviser_email">Email *</label>
					<input
						id="adviser_email"
						type="email"
						class="input-base"
						bind:value={newAdviser.email}
						placeholder="e.g. jane@school.edu"
					/>
				</div>
				<div>
					<label class="field-label" for="employee_id">Employee ID *</label>
					<input
						id="employee_id"
						class="input-base"
						bind:value={newAdviser.id_number}
						placeholder="e.g. EMP-2024-001"
					/>
				</div>
				<div>
					<label class="field-label" for="adviser_password">Password *</label>
					<input
						id="adviser_password"
						type="password"
						class="input-base"
						bind:value={newAdviser.password}
						placeholder="••••••••"
					/>
				</div>
				<div>
					<label class="field-label" for="adviser_dept">Department</label>
					<input
						id="adviser_dept"
						class="input-base"
						bind:value={newAdviser.department}
						placeholder="e.g. CITE"
					/>
				</div>
				<div
					style="grid-column:1/-1;display:flex;gap:0.5rem;justify-content:flex-end;margin-top:0.25rem;"
				>
					<button type="button" onclick={() => (showForm = false)} class="btn-secondary btn-sm"
						>Cancel</button
					>
					<button type="submit" disabled={isAdding} class="btn-primary btn-sm">
						{isAdding ? 'Creating…' : 'Create Adviser'}
					</button>
				</div>
			</form>
		</div>
	{/if}

	<!-- Advisers Table -->
	<div class="admin-card" style="overflow:hidden;">
		<div style="padding:0.75rem 1rem;border-bottom:1px solid var(--border-main);">
			<p class="section-label">
				Listing {filteredAdvisers.length} active adviser account{filteredAdvisers.length !== 1 ? 's' : ''}
			</p>
		</div>

		{#if isLoading}
			<div style="padding:1.5rem;display:flex;flex-direction:column;gap:0.5rem;">
				{#each Array(4) as _}
					<div class="skeleton" style="height:3rem;"></div>
				{/each}
			</div>
		{:else if filteredAdvisers.length === 0}
			<div class="empty-state">
				{adviserSearch ? 'No advisers match your search.' : 'No advisers registered. Click "Add Adviser" to create one.'}
			</div>
		{:else}
			<div style="overflow-x:auto;">
				<table class="data-table">
					<thead>
						<tr>
							<th style="width:1%;">Avatar</th>
							<th>Full Name</th>
							<th>Employee ID</th>
							<th>Department</th>
							<th style="text-align:right;">Actions</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredAdvisers as adviser (adviser.id)}
							<tr>
								<td>
									<div class="avatar-initial" style="width:32px;height:32px;">
										{adviser.full_name?.charAt(0) || 'A'}
									</div>
								</td>
								<td style="font-weight:600;color:var(--text-main);">{adviser.full_name}</td>
								<td style="color:var(--text-muted);">{adviser.id_number}</td>
								<td>
									{#if adviser.department}
										<span class="pill pill-neutral">{adviser.department}</span>
									{:else}
										<span style="color:var(--text-subtle);">—</span>
									{/if}
								</td>
								<td style="text-align:right;">
									<button
										onclick={() => promptDelete(adviser)}
										class="btn-icon-danger"
										title="Revoke access"
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

		<div
			style="padding:1rem;display:flex;align-items:center;justify-content:space-between;border-top:1px solid var(--border-main);"
		>
			<button onclick={goPrev} disabled={currentPage === 0 || isLoading} class="btn-secondary btn-sm">
				Previous
			</button>
			<span style="font-size:0.75rem;font-weight:600;color:var(--text-muted);">
				Page {currentPage + 1}
			</span>
			<button onclick={goNext} disabled={!nextPageToken || isLoading} class="btn-primary btn-sm">
				Next
			</button>
		</div>
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
