<script>
	import { onMount } from 'svelte';
	import { admin as adminApi } from '$lib/api.js';
	import { branding } from '$lib/stores/branding.js';
	import { authSession } from '$lib/stores/auth.js';
	import Notification from '$lib/components/Notification.svelte';
	import ConfirmModal from '$lib/components/ConfirmModal.svelte';
	import { formatFullName } from '$lib/utils.js';

	/** @type {Array<any>} */
	let students = $state([]);
	let isLoading = $state(true);
	let pageHistory = $state([/** @type {string | null} */ (null)]);
	let currentPage = $state(0);
	let nextPageToken = $state(/** @type {string | null} */ (null));
	let studentSearch = $state('');
	let csvFile = $state(/** @type {File | null} */ (null));
	let isUploading = $state(false);
	let departments = $state([]);
	let newStudent = $state({
		student_id: '',
		first_name: '',
		last_name: '',
		middle_initial: '',
		year_level: '',
		email: ''
	});
	let isAddingStudent = $state(false);
	let editingStudent = $state(/** @type {any} */ (null));
	let showForm = $state(false);

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
		await Promise.all([loadStudents(), loadDepartments()]);
	});

	// Resolve the dept_admin's own department name for display in the form.
	// super_admin has no fixed department so we show a dash.
	const adminDeptName = $derived.by(() => {
		const session = $authSession;
		if (!session?.department_id) return '';
		const match = departments.find(/** @param {any} d */ (d) => d.id === session.department_id);
		return match?.name ?? '';
	});

	const isSuperAdmin = $derived($authSession?.role === 'super_admin');

	/** @param {string | null} token */
	async function loadStudents(token = null) {
		try {
			isLoading = true;
			const res = await adminApi.getStudents(50, token);
			students = res.data ?? [];
			nextPageToken = res.next_page_token ?? null;
		} catch (err) {
			console.error('Failed to load students:', err);
			notify('Failed to load students', 'error');
		} finally {
			isLoading = false;
		}
	}

	async function loadDepartments() {
		try {
			const res = await adminApi.getDepartments();
			departments = res.data ?? [];
		} catch (err) {
			console.error('Failed to load departments:', err);
			notify('Failed to load departments', 'error');
		}
	}

	async function goNext() {
		if (!nextPageToken || isLoading) return;
		pageHistory.push(nextPageToken);
		currentPage++;
		await loadStudents(nextPageToken);
	}

	async function goPrev() {
		if (currentPage === 0 || isLoading) return;
		currentPage--;
		pageHistory.pop();
		const prevToken = pageHistory[currentPage];
		await loadStudents(prevToken);
	}

	function notify(text = '', type = /** @type {'info' | 'success' | 'error'} */ ('info')) {
		notification = { text, type };
		setTimeout(() => (notification = { text: '', type: 'info' }), 3500);
	}

	async function handleAddStudent(/** @type {SubmitEvent} */ e) {
		e.preventDefault();
		if (!newStudent.student_id || !newStudent.first_name || !newStudent.last_name) {
			notify('Student ID, First Name, and Last Name are required.', 'error');
			return;
		}
		if (!newStudent.email || !newStudent.email.trim()) {
			notify('Email is required.', 'error');
			return;
		}
		isAddingStudent = true;
		try {
			// Build payload explicitly — never use `|| undefined` for required
			// backend fields, as JSON.stringify drops `undefined` values which
			// causes Pydantic to raise a 422 validation error.
			/** @type {Record<string, any>} */
			const payload = {
				student_id: newStudent.student_id.trim(),
				first_name: newStudent.first_name.trim(),
				last_name: newStudent.last_name.trim(),
				email: newStudent.email.trim()
			};
			if (newStudent.middle_initial) payload.middle_initial = newStudent.middle_initial.trim().charAt(0).toUpperCase();
			if (newStudent.year_level) payload.year_level = parseInt(newStudent.year_level);
			// program = dept_admin's department name (auto-inherited, not editable)
			if (adminDeptName) payload.program = adminDeptName;
			// department_id is NOT sent — the backend auto-assigns the dept_admin's own department.

			if (editingStudent) {
				await adminApi.updateStudent(editingStudent.student_id, payload);
				notify('Student updated', 'success');
			} else {
				await adminApi.addStudent(payload);
				notify('Student added', 'success');
			}
			newStudent = { student_id: '', first_name: '', last_name: '', middle_initial: '', year_level: '', email: '' };
			editingStudent = null;
			showForm = false;
			await loadStudents();
		} catch (/** @type {any} */ err) {
			notify(err.message ?? 'Failed to save student', 'error');
		} finally {
			isAddingStudent = false;
		}
	}

	function startEdit(/** @type {any} */ student) {
		editingStudent = student;
		newStudent = {
			student_id: student.student_id ?? '',
			first_name: student.first_name ?? '',
			last_name: student.last_name ?? '',
			middle_initial: student.middle_initial ?? '',
			year_level: student.year_level?.toString() ?? '',
			email: student.email ?? ''
		};
		showForm = true;
	}

	function cancelEdit() {
		editingStudent = null;
		newStudent = { student_id: '', first_name: '', last_name: '', middle_initial: '', year_level: '', email: '' };
		showForm = false;
	}

	async function handleCSVUpload(/** @type {SubmitEvent} */ e) {
		e.preventDefault();
		if (!csvFile) return;
		isUploading = true;
		notify('Uploading…', 'info');
		const formData = new FormData();
		formData.append('file', csvFile);
		try {
			const data = await adminApi.uploadStudents(formData);
			notify(data.message ?? 'Students imported successfully.', 'success');
			csvFile = null;
			await loadStudents();
		} catch (/** @type {any} */ err) {
			notify(err.message ?? 'Error uploading students.', 'error');
		} finally {
			isUploading = false;
		}
	}

	function promptDelete(/** @type {any} */ student) {
		confirmState = {
			show: true,
			title: 'Delete Student',
			message: `Are you sure you want to remove ${student.full_name} (${student.student_id})? This will also remove any votes they have cast.`,
			id: student.student_id,
			onConfirm: async () => {
				try {
					await adminApi.deleteStudent(confirmState.id);
					students = students.filter((s) => s.student_id !== confirmState.id);
					notify('Student removed', 'success');
				} catch (/** @type {any} */ err) {
					notify(err.message ?? 'Failed to delete student', 'error');
				} finally {
					confirmState.show = false;
				}
			}
		};
	}

	const filteredStudents = $derived(
		studentSearch
			? students.filter(
					(s) =>
						s.full_name.toLowerCase().includes(studentSearch.toLowerCase()) ||
						s.student_id.includes(studentSearch)
				)
			: students
	);
</script>

<svelte:head><title>Voter Registry | {$branding.appName}</title></svelte:head>

<div class="dash">
	<div class="dash-header">
		<div>
			<p class="dash-eyebrow"><span class="prefix">Pages /</span> Administrator</p>
			<h1 class="dash-title">Voter Registry</h1>
		</div>
		<div style="display:flex;align-items:center;gap:0.5rem;">
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
					bind:value={studentSearch}
					placeholder="Search students…"
					class="input-base"
					style="padding-left:2.5rem;width:240px;height:2rem;font-size:0.75rem;font-family:sans-serif;"
				/>
			</div>
			{#if !isSuperAdmin}
			<button
				onclick={() => {
					cancelEdit();
					showForm = !showForm;
				}}
				class="btn-primary btn-sm"
			>
				<svg
					class="h-3.5 w-3.5"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					viewBox="0 0 24 24"
					><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" /></svg
				>
				Add Student
			</button>
			{/if}
		</div>
	</div>

	<!-- Add / Edit Form -->
	{#if showForm}
		<div class="bento-card" style="padding:1.5rem; border-radius: 16px; margin-bottom: 1.5rem;">
			<div
				style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;"
			>
				<h2 style="font-size:0.875rem;font-weight:600;color:var(--text-main);">
					{editingStudent ? 'Edit Student' : 'Add Student'}
				</h2>
				<button onclick={cancelEdit} class="btn-icon" aria-label="Close form">
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
			<form
				onsubmit={handleAddStudent}
				style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;"
			>
				<div>
					<label class="field-label" for="student_id">Student ID *</label>
					<input
						id="student_id"
						class="input-base"
						bind:value={newStudent.student_id}
						disabled={!!editingStudent}
						placeholder="2024-0001"
					/>
				</div>
				<div>
					<label class="field-label" for="student_email">Email *</label>
					<input
						id="student_email"
						type="email"
						class="input-base"
						bind:value={newStudent.email}
						placeholder="student@example.com"
						required
					/>
				</div>
				<div>
					<label class="field-label" for="student_first_name">First Name *</label>
					<input
						id="student_first_name"
						class="input-base"
						bind:value={newStudent.first_name}
						placeholder="Juan"
						required
					/>
				</div>
				<div>
					<label class="field-label" for="student_last_name">Last Name *</label>
					<input
						id="student_last_name"
						class="input-base"
						bind:value={newStudent.last_name}
						placeholder="Dela Cruz"
						required
					/>
				</div>
				<div>
					<label class="field-label" for="student_mi">Middle Initial</label>
					<input
						id="student_mi"
						class="input-base"
						bind:value={newStudent.middle_initial}
						placeholder="M"
						maxlength="1"
					/>
				</div>
				<div>
					<label class="field-label" for="student_year">Year Level</label>
					<input
						id="student_year"
						type="number"
						class="input-base"
						bind:value={newStudent.year_level}
						placeholder="1"
						min="1"
						max="6"
					/>
				</div>
				{#if adminDeptName}
				<div style="grid-column:1/-1;">
					<label class="field-label" for="student_program">
						Program
						<span style="font-weight:400;color:var(--text-subtle);font-size:0.7rem;">(auto-assigned from your department)</span>
					</label>
					<input
						id="student_program"
						class="input-base"
						value={adminDeptName}
						disabled
						style="opacity:0.65;cursor:not-allowed;"
					/>
				</div>
				{/if}
				<div
					style="grid-column:1/-1;display:flex;gap:0.5rem;justify-content:flex-end;margin-top:0.25rem;"
				>
					<button type="button" onclick={cancelEdit} class="btn-secondary btn-sm">Cancel</button>
					<button type="submit" disabled={isAddingStudent} class="btn-primary btn-sm">
						{isAddingStudent ? 'Saving…' : editingStudent ? 'Update Student' : 'Add Student'}
					</button>
				</div>
			</form>
		</div>
	{/if}

	<!-- CSV Upload -->
	{#if !isSuperAdmin}
	<div class="bento-card" style="padding:1.5rem; border-radius: 16px; margin-bottom: 1.5rem;">
		<div style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap;">
			<p style="font-size:0.8125rem;font-weight:600;color:var(--text-main);flex-shrink:0;">
				Bulk Import via CSV
			</p>
			<form
				onsubmit={handleCSVUpload}
				style="display:flex;align-items:center;gap:0.5rem;flex:1;flex-wrap:wrap;"
			>
				<label
					style="display:flex;align-items:center;gap:0.5rem;cursor:pointer;flex:1;min-width:160px;"
				>
					<div
						style="padding:0.375rem 0.625rem;background-color:var(--bg-elevated);border:1px solid var(--border-main);border-radius:6px;font-size:0.6875rem;font-weight:600;color:var(--text-muted);white-space:nowrap;cursor:pointer;"
					>
						Choose File
					</div>
					<span
						style="font-size:0.75rem;color:var(--text-subtle);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
					>
						{csvFile ? csvFile.name : 'No file selected'}
					</span>
					<input
						type="file"
						accept=".csv"
						class="hidden"
						style="display:none;"
						onchange={(e) =>
							(csvFile = /** @type {HTMLInputElement} */ (e.target).files?.[0] || null)}
					/>
				</label>
				<button type="submit" disabled={!csvFile || isUploading} class="btn-secondary btn-sm">
					{isUploading ? 'Uploading…' : 'Import'}
				</button>
			</form>
		</div>
	</div>
	{/if}

	<!-- Voter Table -->
	<div class="bento-card" style="overflow:hidden; border-radius: 16px;">
		<div style="padding:0.75rem 1rem;border-bottom:1px solid var(--border-main);">
			<p class="section-label">
				Listing student voters
			</p>
		</div>
		{#if isLoading}
			<div style="padding:1.25rem;display:flex;flex-direction:column;gap:0.375rem;">
				{#each Array(6) as _}
					<div class="skeleton" style="height:2.5rem;"></div>
				{/each}
			</div>
		{:else if filteredStudents.length === 0}
			<div class="empty-state">
				{studentSearch ? 'No students match your search.' : 'No students registered yet.'}
			</div>
		{:else}
			<div style="overflow-x:auto;">
				<table class="data-table">
					<thead>
						<tr>
							<th>Student ID</th>
							<th>Full Name</th>
							<th>Program</th>
							<th>Email</th>
							<th>Department</th>
							<th>Year</th>
							<th style="text-align:right;">Actions</th>
						</tr>
					</thead>
					<tbody>
						{#each filteredStudents as student (student.student_id)}
							<tr>
								<td
									style="font-weight:600;color:var(--text-main);font-family:monospace;font-size:0.8125rem;"
									>{student.student_id}</td
								>
								<td style="font-weight:500;color:var(--text-main);">{student.full_name || formatFullName(student)}</td>
								<td style="color:var(--text-muted);">{student.program || '—'}</td>
								<td style="color:var(--text-muted);">{student.email || '—'}</td>
								<td style="color:var(--text-muted);">{departments.find((d) => d.id === student.department_id)?.name || student.department_id || '—'}</td>
								<td>
									{#if student.year_level}
										<span class="pill pill-neutral">Yr {student.year_level}</span>
									{:else}
										<span style="color:var(--text-subtle);">—</span>
									{/if}
								</td>
								<td style="text-align:right;white-space:nowrap;">
									<button
										onclick={() => startEdit(student)}
										class="btn-icon-edit"
										title="Edit student"
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
									<button
										onclick={() => promptDelete(student)}
										class="btn-icon-danger"
										title="Delete student"
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

<style>
	.data-table thead th {
		position: sticky;
		top: 0;
		background: var(--bg-card);
		backdrop-filter: blur(12px);
		-webkit-backdrop-filter: blur(12px);
		z-index: 10;
		border-bottom: 1px solid var(--border-main);
		padding: 1rem;
		font-size: 0.75rem;
		font-weight: 800;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: var(--text-subtle);
		transition: color 0.2s;
	}
	.data-table thead th:hover {
		color: var(--text-main);
	}
	.data-table tbody td {
		padding: 1rem;
		vertical-align: middle;
	}
	.data-table tbody tr {
		transition: all 0.2s ease;
		border-bottom: 1px solid var(--border-subtle);
	}
	.data-table tbody tr:last-child {
		border-bottom: none;
	}
	.data-table tbody tr:hover {
		background: rgba(128, 128, 128, 0.05);
	}
</style>
