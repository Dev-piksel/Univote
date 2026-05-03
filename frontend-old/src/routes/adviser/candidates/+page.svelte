<script>
	import { onMount } from 'svelte';
	import { admin, adviser } from '$lib/api.js';
	import { selectedElectionId } from '$lib/stores/election.js';
	import { branding } from '$lib/stores/branding.js';
	import { POSITION_ORDER, sortPositions } from '$lib/constants.js';

	/** @type {any[]} */
	let elections = $state([]);
	/** @type {any[]} */
	let candidates = $state([]);
	/** @type {any[]} */
	let partylists = $state([]);

	let newCandidate = $state({ student_id: '', position: '', partylist_id: '' });
	let customPosition = $state('');
	let isSubmitting = $state(false);
	let errorMessage = $state('');
	let successMessage = $state('');
	/** @type {string | null} */
	let newCandidatePhotoPreview = $state(null);
	/** @type {string | null} */
	let newCandidatePhotoBase64 = $state(null);
	/** @type {Record<string, boolean>} */
	let uploading = $state({});
	
	/** @type {any[]} */
	let studentSuggestions = $state([]);
	let isSearchingStudents = $state(false);
	let showSuggestions = $state(false);
	let isLoading = $state(false);
	/** @type {any} */
	let searchTimeout;


	async function loadElections() {
		try {
			const res = await adviser.getElections();
			elections = res.data || [];
		} catch (err) {
			console.error('Failed to load elections:', err);
		}
	}

	async function loadData() {
		if (!$selectedElectionId) return;
		isLoading = true;
		try {
			const [pRes, cRes] = await Promise.all([
				adviser.getPartylists($selectedElectionId),
				adviser.getCandidates($selectedElectionId)
			]);
			partylists = pRes.data || [];
			candidates = cRes.data || [];
		} catch (err) {
			console.error('Failed to load data:', err);
		} finally {
			isLoading = false;
		}
	}

	/**
	 * Convert a File to base64 data URL
	 * @param {File} file
	 * @returns {Promise<string>}
	 */
	function fileToBase64(file) {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = () => resolve(/** @type {string} */ (reader.result));
			reader.onerror = reject;
			reader.readAsDataURL(file);
		});
	}

	/** @param {Event} e */
	async function handleNewPhotoSelect(e) {
		const input = /** @type {HTMLInputElement} */ (e.target);
		const file = input.files?.[0];
		if (!file) return;
		try {
			const base64 = await fileToBase64(file);
			newCandidatePhotoBase64 = base64;
			newCandidatePhotoPreview = base64;
		} catch {
			errorMessage = 'Failed to read image. Try another file.';
		}
	}

	function clearNewPhoto() {
		newCandidatePhotoBase64 = null;
		newCandidatePhotoPreview = null;
	}

	/**
	 * @param {string} candidateId
	 * @param {Event} e
	 */
	async function handlePhotoUpload(candidateId, e) {
		const input = /** @type {HTMLInputElement} */ (e.target);
		const file = input.files?.[0];
		if (!file) return;
		uploading[candidateId] = true;
		try {
			const base64 = await fileToBase64(file);
			await adviser.uploadCandidatePhoto(candidateId, base64);
			// Update local state
			candidates = candidates.map((c) =>
				c.id === candidateId ? { ...c, photo_url: base64 } : c
			);
			successMessage = 'Photo updated!';
			setTimeout(() => (successMessage = ''), 2500);
		} catch (/** @type {any} */ err) {
			errorMessage = err.message || 'Failed to upload photo.';
		} finally {
			uploading[candidateId] = false;
			input.value = '';
		}
	}

	/** @param {string} candidateId */
	async function removePhoto(candidateId) {
		uploading[candidateId] = true;
		try {
			await adviser.deleteCandidatePhoto(candidateId);
			candidates = candidates.map((c) =>
				c.id === candidateId ? { ...c, photo_url: null } : c
			);
		} catch (/** @type {any} */ err) {
			errorMessage = err.message || 'Failed to remove photo.';
		} finally {
			uploading[candidateId] = false;
		}
	}

	onMount(() => {
		// Parallelize election loading and data loading if possible
		loadElections().then(() => {
			if ($selectedElectionId) loadData();
		});
	});

	$effect(() => {
		if ($selectedElectionId) {
			loadData();
		}
	});

	async function handleStudentIdInput() {
		const query = newCandidate.student_id;
		if (query.length < 2) {
			studentSuggestions = [];
			showSuggestions = false;
			return;
		}

		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(async () => {
			isSearchingStudents = true;
			try {
				const res = await adviser.searchStudents(query);
				studentSuggestions = res.data || [];
				showSuggestions = studentSuggestions.length > 0;
			} catch (err) {
				console.error('Student search failed:', err);
			} finally {
				isSearchingStudents = false;
			}
		}, 300);
	}

	/** @param {any} student */
	function selectStudent(student) {
		newCandidate.student_id = student.student_id;
		showSuggestions = false;
		studentSuggestions = [];
	}

	/** @param {SubmitEvent} e */
	async function handleAddCandidate(e) {
		e.preventDefault();
		if (!newCandidate.student_id || !newCandidate.position || !$selectedElectionId) {
			errorMessage = 'Please fill in all required fields.';
			return;
		}
		isSubmitting = true;
		errorMessage = '';
		successMessage = '';
		try {
			const finalPosition =
				newCandidate.position === 'Other' ? customPosition : newCandidate.position;
			if (!finalPosition) {
				errorMessage = 'Please provide a position name.';
				isSubmitting = false;
				return;
			}

			const createRes = await adviser.createCandidate($selectedElectionId, {
				student_id: newCandidate.student_id,
				position: finalPosition,
				partylist_id: newCandidate.partylist_id || null
			});

			// Upload photo if one was selected
			if (newCandidatePhotoBase64) {
				// The backend returns { message, data: [...] } where data is the inserted row
				const newId = createRes?.data?.[0]?.id || createRes?.data?.id || createRes?.id;
				if (newId) {
					try {
						await adviser.uploadCandidatePhoto(newId, newCandidatePhotoBase64);
					} catch (err) {
						console.error('Initial photo upload failed:', err);
						successMessage = 'Candidate added. Photo upload failed — you can retry on the card.';
					}
				}
				newCandidatePhotoBase64 = null;
				newCandidatePhotoPreview = null;
			}

			newCandidate = { student_id: '', position: '', partylist_id: '' };
			customPosition = '';
			if (!successMessage) successMessage = 'Candidate added successfully!';
			setTimeout(() => (successMessage = ''), 3000);
			await loadData();
		} catch (/** @type {any} */ err) {
			errorMessage = err.message || 'Failed to add candidate.';
		} finally {
			isSubmitting = false;
		}
	}

	// Group candidates by position and sort the positions
	const groupedCandidates = $derived(() => {
		/** @type {Record<string, any[]>} */
		const g = {};
		candidates.forEach((c) => {
			const pos = c.position || 'Unassigned';
			if (!g[pos]) g[pos] = [];
			g[pos].push(c);
		});

		const sortedKeys = sortPositions(Object.keys(g));
		/** @type {Record<string, any[]>} */
		const sortedG = {};
		sortedKeys.forEach((key) => {
			sortedG[key] = g[key];
		});
		return sortedG;
	});

	const selectedElection = $derived(() =>
		elections.find(/** @param {any} e */ (e) => e.id === $selectedElectionId)
	);
	const isModifiable = $derived(() => selectedElection()?.status === 'upcoming');

	/** @param {string} id */
	async function handleDeleteCandidate(id) {
		if (!confirm('Are you sure you want to delete this candidate?')) return;
		try {
			await adviser.deleteCandidate(id);
			successMessage = 'Candidate deleted successfully.';
			await loadData();
		} catch (/** @type {any} */ err) {
			errorMessage = err.message || 'Failed to delete candidate.';
		}
	}
</script>

<style>
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.suggestions-dropdown {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		z-index: 50;
		background: #111827; /* Solid dark background for contrast */
		backdrop-filter: blur(8px);
		border: 1px solid var(--border-main);
		border-radius: 8px;
		margin-top: 4px;
		max-height: 200px;
		overflow-y: auto;
		box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
	}

	.suggestion-item {
		width: 100%;
		padding: 0.625rem 0.875rem;
		border: none;
		background: none;
		cursor: pointer;
		border-bottom: 1px solid var(--border-subtle);
		display: flex;
		transition: background 0.15s;
	}

	.suggestion-item:last-child {
		border-bottom: none;
	}

	.suggestion-item:hover {
		background: var(--bg-elevated);
	}

	.suggestion-id {
		font-size: 0.75rem;
		font-weight: 700;
		color: var(--brand-primary, #0b75fe);
	}

	.suggestion-name {
		font-size: 0.6875rem;
		color: var(--text-muted);
	}
</style>

<svelte:head><title>Candidates | {$branding.appName}</title></svelte:head>

<div class="dash">
	<div class="dash-header">
		<div>
			<p class="dash-eyebrow"><span class="prefix">Pages /</span> Candidates</p>
			<h1 class="dash-title">Candidates</h1>
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
			Please select an election from the dropdown above to manage candidates.
		</div>
	{:else}
		<div class="bento-grid" style="grid-template-columns: 1fr 2.5fr; gap: 1rem;">
			<!-- Add Candidate Form -->
			<div class="admin-card" style="padding:1.25rem;height:fit-content;">
				<div style="margin-bottom:1.25rem;">
					<h2 style="font-size:0.875rem;font-weight:600;color:var(--text-main);">Add Candidate</h2>
				</div>

				<form onsubmit={handleAddCandidate} style="display:flex;flex-direction:column;gap:1rem;">
					<div style="position:relative;">
						<label class="field-label" for="student-id">Student ID *</label>
						<input
							id="student-id"
							type="text"
							bind:value={newCandidate.student_id}
							oninput={handleStudentIdInput}
							onfocus={() => { if(studentSuggestions.length > 0) showSuggestions = true; }}
							onblur={() => { setTimeout(() => showSuggestions = false, 200); }}
							class="input-base"
							placeholder="e.g. 2021-00123"
							autocomplete="off"
						/>
						{#if showSuggestions}
							<div class="suggestions-dropdown">
								{#each studentSuggestions as student}
									<button
										type="button"
										class="suggestion-item"
										onclick={() => selectStudent(student)}
									>
										<div class="flex flex-col text-left">
											<span class="suggestion-id">{student.student_id}</span>
											<span class="suggestion-name">{student.full_name}</span>
										</div>
									</button>
								{/each}
							</div>
						{/if}
					</div>

					<div>
						<label class="field-label" for="position">Position *</label>
						<select id="position" bind:value={newCandidate.position} class="input-base">
							<option value="" disabled>Select Role...</option>
							{#each POSITION_ORDER as pos}
								<option value={pos}>{pos}</option>
							{/each}
							<option value="Other">Other (Custom)</option>
						</select>
					</div>

					{#if newCandidate.position === 'Other'}
						<div>
							<label class="field-label" for="custom-position">Custom Position</label>
							<input
								id="custom-position"
								type="text"
								bind:value={customPosition}
								class="input-base"
								placeholder="e.g. Sgt. at Arms"
							/>
						</div>
					{/if}

					<div>
						<label class="field-label" for="party">Partylist</label>
						<select id="party" bind:value={newCandidate.partylist_id} class="input-base">
							<option value="">Independent</option>
							{#each partylists as party}
								<option value={party.id}>{party.name}</option>
							{/each}
						</select>
					</div>



					<!-- Profile Photo (optional) -->
					<div>
						<span class="field-label"
							>Photo <span style="font-weight:400;opacity:0.65;">(optional)</span></span
						>
						<div style="display:flex;align-items:center;gap:0.75rem;margin-top:0.375rem;">
							{#if newCandidatePhotoPreview}
								<img
									src={newCandidatePhotoPreview}
									alt="Preview"
									style="width:52px;height:52px;border-radius:50%;object-fit:cover;border:2px solid var(--brand-primary,#0b75fe);flex-shrink:0;"
								/>
							{:else}
								<div
									style="width:52px;height:52px;border-radius:50%;background:var(--bg-elevated);border:2px dashed var(--border-main);display:grid;place-items:center;flex-shrink:0;color:var(--text-muted);"
								>
									<svg
										width="18"
										height="18"
										fill="none"
										stroke="currentColor"
										stroke-width="2"
										viewBox="0 0 24 24"
										><path
											stroke-linecap="round"
											stroke-linejoin="round"
											d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"
										/><circle cx="12" cy="13" r="3" /></svg
									>
								</div>
							{/if}
							<div style="display:flex;flex-direction:column;gap:0.3rem;">
								<label
									style="display:inline-flex;align-items:center;gap:0.375rem;font-size:0.75rem;font-weight:600;color:var(--brand-primary,#0b75fe);cursor:pointer;padding:0.3rem 0.65rem;border:1.5px solid var(--brand-primary,#0b75fe);border-radius:6px;width:fit-content;"
								>
									<svg
										width="11"
										height="11"
										fill="none"
										stroke="currentColor"
										stroke-width="2.5"
										viewBox="0 0 24 24"
										><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline
											points="17 8 12 3 7 8"
										/><line x1="12" y1="3" x2="12" y2="15" /></svg
									>
									{newCandidatePhotoPreview ? 'Change' : 'Upload Photo'}
									<input
										type="file"
										accept="image/*"
										style="display:none;"
										onchange={handleNewPhotoSelect}
									/>
								</label>
								{#if newCandidatePhotoPreview}
									<button
										type="button"
										onclick={clearNewPhoto}
										style="font-size:0.65rem;font-weight:700;color:var(--status-danger-fg);background:none;border:none;cursor:pointer;padding:0;text-align:left;"
										>✕ Remove</button
									>
								{/if}
							</div>
						</div>
					</div>

					{#if errorMessage}
						<div
							style="color:var(--status-danger-fg);font-size:0.75rem;padding:0.5rem;background:var(--status-danger-bg);border-radius:4px;"
						>
							{errorMessage}
						</div>
					{/if}
					{#if successMessage}
						<div
							style="color:var(--status-success-fg);font-size:0.75rem;padding:0.5rem;background:var(--status-success-bg);border-radius:4px;"
						>
							{successMessage}
						</div>
					{/if}

					<button
						type="submit"
						disabled={isSubmitting || !isModifiable()}
						class="btn-primary"
						style="margin-top:0.5rem;"
					>
						{isSubmitting ? 'Adding...' : 'Add Candidate'}
					</button>
				</form>
			</div>

			<!-- Candidates List -->
			<div class="admin-card" style="padding:1.5rem;display:flex;flex-direction:column;gap:1.5rem;">
				<div
					style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border-subtle);padding-bottom:0.75rem;"
				>
					<h2 style="font-size:0.875rem;font-weight:600;color:var(--text-main);">
						Registered Candidates
					</h2>
					<span class="pill pill-neutral">{candidates.length} candidates</span>
				</div>

				{#if isLoading}
					<div style="display:flex;flex-direction:column;gap:2rem;">
						{#each [1, 2] as i}
							<div>
								<div class="skeleton" style="width:120px;height:12px;margin-bottom:1rem;border-radius:4px;"></div>
								<div class="bento-grid bento-2col" style="gap:0.75rem;">
									{#each [1, 2, 3, 4] as j}
										<div class="profile-card skeleton" style="height:70px;border-color:var(--border-subtle);opacity:0.5;"></div>
									{/each}
								</div>
							</div>
						{/each}
					</div>
				{:else if candidates.length === 0}
					<div class="empty-state" style="border:none;">
						No candidates registered for this election yet.
					</div>
				{:else}
					{#each Object.entries(groupedCandidates()) as [position, list]}
						<div>
							<h3 class="section-label" style="margin-bottom:0.75rem;">
								{position} ({list.length})
							</h3>
							<div class="bento-grid bento-2col" style="gap:0.75rem;">
								{#each list as candidate}
									{@const name = candidate.students?.full_name || 'Unknown'}
									{@const partyName = candidate.partylist_id
										? partylists.find((p) => p.id === candidate.partylist_id)?.name ||
											'Unknown Partylist'
										: 'Independent'}
									<div
										class="profile-card"
										style="padding:0.75rem 1rem;display:flex;align-items:center;gap:1rem;border-color:var(--border-subtle);box-shadow:none;"
									>
										<!-- Photo with upload overlay -->
										<div style="position:relative;flex-shrink:0;">
											{#if candidate.id}
												{@const photoUrl = adviser.getCandidatePhotoUrl(candidate.id)}
												<img 
													src={photoUrl} 
													alt={name} 
													loading="lazy"
													onerror={(e) => { 
														const target = /** @type {HTMLImageElement} */ (e.currentTarget);
														const next = /** @type {HTMLElement} */ (target.nextElementSibling);
														target.style.display = 'none'; 
														if (next) next.style.display = 'flex'; 
													}}
													style="width:42px;height:42px;border-radius:50%;object-fit:cover;border:2px solid var(--border-main);" 
												/>
												<div class="avatar-initial" style="width:42px;height:42px;display:none;">
													{(name || '??').split(' ').slice(0, 2).map((/** @type {string} */ w) => w[0]?.toUpperCase() || '').join('')}
												</div>
											{:else}
												<div class="avatar-initial" style="width:42px;height:42px;">
													{(name || '??').split(' ').slice(0, 2).map((/** @type {string} */ w) => w[0]?.toUpperCase() || '').join('')}
												</div>
											{/if}
											{#if isModifiable()}
												<label title="Upload photo" style="position:absolute;bottom:-3px;right:-3px;width:18px;height:18px;background:var(--brand-primary,#0b75fe);border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;border:2px solid var(--bg-card);">
													{#if uploading[candidate.id]}
														<span style="width:8px;height:8px;border:1.5px solid rgba(255,255,255,0.4);border-top-color:#fff;border-radius:50%;animation:spin 0.6s linear infinite;display:inline-block;"></span>
													{:else}
														<svg width="9" height="9" fill="none" stroke="white" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/><circle cx="12" cy="13" r="3"/></svg>
													{/if}
													<input type="file" accept="image/*" style="display:none;" onchange={(e) => handlePhotoUpload(candidate.id, e)} disabled={!!uploading[candidate.id]} />
												</label>
											{/if}
										</div>
										<div style="flex:1;min-width:0;">
											<p style="font-size:0.8125rem;font-weight:600;color:var(--text-main);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title={name}>
												{name}
											</p>
											<p style="font-size:0.6875rem;color:var(--text-muted);margin-top:0.125rem;">{partyName}</p>
											{#if candidate.photo_url && isModifiable()}
												<button onclick={() => removePhoto(candidate.id)} style="font-size:0.6rem;font-weight:700;color:var(--status-danger-fg);background:none;border:none;cursor:pointer;padding:0;margin-top:2px;">Remove photo</button>
											{/if}
										</div>

										{#if isModifiable()}
											<button
												onclick={() => handleDeleteCandidate(candidate.id)}
												class="btn-icon-danger flex-shrink-0"
												title="Remove candidate"
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
								{/each}
							</div>
						</div>
					{/each}
				{/if}
			</div>
		</div>
	{/if}
</div>
