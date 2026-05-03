<script>
	import { onMount } from 'svelte';
	import { admin as adminApi } from '$lib/api.js';
	import { branding } from '$lib/stores/branding.js';
	import { authSession } from '$lib/stores/auth.js';
	import Notification from '$lib/components/Notification.svelte';
	import ConfirmModal from '$lib/components/ConfirmModal.svelte';
	import { fade, fly, slide } from 'svelte/transition';
	import {
		Button,
		Badge,
		Spinner,
		Table,
		TableHead,
		TableHeadCell,
		TableBody,
		TableBodyRow,
		TableBodyCell,
		Skeleton,
		Card,
		FloatingLabelInput,
		Select,
		Avatar,
		Helper,
		Input,
		Label
	} from 'flowbite-svelte';
	import {
		PlusOutline,
		RefreshOutline,
		CloseOutline,
		EditOutline,
		TrashBinOutline,
		UserOutline,
		SearchOutline,
		FilterOutline,
		CloudArrowUpOutline,
		DownloadOutline,
		EyeOutline,
		EyeSlashOutline,
		CheckCircleOutline,
		ExclamationCircleOutline,
		CameraPhotoOutline
	} from 'flowbite-svelte-icons';

	/** @type {any[]} */
	let deptAdmins = $state([]);
	/** @type {any[]} */
	let departments = $state([]);
	let isLoading = $state(true);
	let isSaving = $state(false);
	let isImporting = $state(false);
	let showForm = $state(false);
	let showImport = $state(false);
	let searchQuery = $state('');

	let newAdmin = $state({ id_number: '', first_name: '', last_name: '', middle_initial: '', email: '', password: '', department_id: '', photo_url: '' });
	let visibleIds = $state(new Set());
	let editingAdmin = $state(/** @type {any} */ (null));
	/** @type {string | null} */
	let photoPreview = $state(null);

	/** @type {Array<{full_name:string,employee_id:string,default_password:string,department:string}>} */
	let importResults = $state([]);
	/** @type {any[]} */
	let importSkipped = $state([]);

	let pageHistory = $state([/** @type {string | null} */ (null)]);
	let currentPage = $state(0);
	let nextPageToken = $state(/** @type {string | null} */ (null));

	let confirmState = $state({ show: false, title: '', message: '', id: '', onConfirm: () => {} });
	/** @type {{ text: string, type: 'info' | 'success' | 'error' }} */
	let notification = $state({ text: '', type: 'info' });

	onMount(async () => {
		await Promise.all([loadDeptAdmins(), loadDepartments()]);
	});

	async function loadDeptAdmins(/** @type {string | null} */ token = null) {
		isLoading = true;
		try {
			const res = await adminApi.getDeptAdmins(15, token);
			deptAdmins = res.data ?? [];
			nextPageToken = res.next_page_token ?? null;
		} catch (/** @type {any} */ err) {
			notify(err.message ?? 'Failed to load dept admins.', 'error');
		} finally {
			isLoading = false;
		}
	}

	async function loadDepartments() {
		try {
			const res = await adminApi.getDepartments();
			departments = res.data ?? [];
		} catch { /* silent */ }
	}

	async function goNext() {
		if (!nextPageToken || isLoading) return;
		pageHistory.push(nextPageToken);
		currentPage++;
		await loadDeptAdmins(nextPageToken);
	}

	async function goPrev() {
		if (currentPage === 0 || isLoading) return;
		currentPage--;
		pageHistory.pop();
		await loadDeptAdmins(pageHistory[currentPage]);
	}

	const filteredAdmins = $derived(
		searchQuery
			? deptAdmins.filter(
					(a) =>
						a.full_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
						a.id_number?.toLowerCase().includes(searchQuery.toLowerCase())
				)
			: deptAdmins
	);

	function notify(text = '', type = /** @type {'info'|'success'|'error'} */ ('info')) {
		notification = { text, type };
		setTimeout(() => (notification = { text: '', type: 'info' }), 3500);
	}

	function copyToClipboard(/** @type {string} */ text) {
		navigator.clipboard?.writeText(text).then(() => notify('Copied!', 'success'));
	}

	async function handleAdd(/** @type {SubmitEvent} */ e) {
		e.preventDefault();
		if (!newAdmin.id_number || !newAdmin.first_name || !newAdmin.last_name || (!editingAdmin && !newAdmin.password) || !newAdmin.email) {
			notify('First name, last name, email, employee ID and password are required.', 'error');
			return;
		}
		isSaving = true;
		try {
			if (editingAdmin) {
				await adminApi.updateDeptAdmin(editingAdmin.id, {
					first_name: newAdmin.first_name,
					last_name: newAdmin.last_name,
					middle_initial: newAdmin.middle_initial || undefined,
					email: newAdmin.email || undefined,
					department_id: newAdmin.department_id || undefined,
					photo_url: newAdmin.photo_url || undefined
				});
				notify('Dept Admin updated successfully.', 'success');
			} else {
				await adminApi.createDeptAdmin({
					id_number: newAdmin.id_number,
					first_name: newAdmin.first_name,
					last_name: newAdmin.last_name,
					middle_initial: newAdmin.middle_initial || undefined,
					password: newAdmin.password,
					email: newAdmin.email,
					department_id: newAdmin.department_id || undefined,
					photo_url: newAdmin.photo_url || undefined
				});
				notify('Dept Admin created successfully.', 'success');
			}
			resetForm();
			await loadDeptAdmins();
		} catch (/** @type {any} */ err) {
			notify(err.message ?? 'Failed to save dept admin.', 'error');
		} finally {
			isSaving = false;
		}
	}

	function resetForm() {
		editingAdmin = null;
		photoPreview = null;
		newAdmin = { id_number: '', first_name: '', last_name: '', middle_initial: '', email: '', password: '', department_id: '', photo_url: '' };
		showForm = false;
	}

	function startEdit(/** @type {any} */ admin) {
		editingAdmin = admin;
		newAdmin = { 
			id_number: admin.id_number, 
			first_name: admin.first_name, 
			last_name: admin.last_name, 
			middle_initial: admin.middle_initial || '', 
			email: admin.email || '',
			password: '****', 
			department_id: admin.department_id || '',
			photo_url: admin.photo_url || ''
		};
		photoPreview = admin.photo_url || null;
		showForm = true;
		showImport = false;
	}

	/** @param {Event} e */
	async function handlePhotoSelect(e) {
		const input = /** @type {HTMLInputElement} */ (e.target);
		const file = input.files?.[0];
		if (!file) return;
		try {
			const reader = new FileReader();
			reader.onload = () => {
				const base64 = /** @type {string} */ (reader.result);
				photoPreview = base64;
				newAdmin.photo_url = base64;
			};
			reader.readAsDataURL(file);
		} catch {
			notify('Failed to read image', 'error');
		}
	}

	function promptDelete(/** @type {any} */ admin) {
		confirmState = {
			show: true,
			title: 'Remove Dept Admin',
			message: `Are you sure you want to delete the account for ${admin.full_name}? This cannot be undone.`,
			id: admin.id,
			onConfirm: async () => {
				try {
					await adminApi.deleteDeptAdmin(confirmState.id);
					deptAdmins = deptAdmins.filter((a) => a.id !== confirmState.id);
					notify('Dept Admin removed.', 'success');
				} catch (/** @type {any} */ err) {
					notify(err.message ?? 'Delete failed.', 'error');
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
			const res = await adminApi.importDeptAdmins(fd);
			importResults = res.created ?? [];
			importSkipped = res.skipped ?? [];
			notify(res.message ?? 'Import complete.', importResults.length > 0 ? 'success' : 'info');
			await loadDeptAdmins();
		} catch (/** @type {any} */ err) {
			notify(err.message ?? 'Import failed.', 'error');
		} finally {
			isImporting = false;
			input.value = '';
		}
	}

	function getDeptName(/** @type {string|null} */ dept_id) {
		if (!dept_id) return null;
		return departments.find((d) => d.id === dept_id)?.name ?? dept_id;
	}

	function toggleIdVisibility(/** @type {string} */ id) {
		if (visibleIds.has(id)) visibleIds.delete(id);
		else visibleIds.add(id);
		visibleIds = new Set(visibleIds);
	}
</script>

<svelte:head><title>Admin Registry | {$branding.appName}</title></svelte:head>

{#if $authSession?.role !== 'super_admin'}
	<div class="dash flex items-center justify-center min-h-[60vh]">
		<Card size="none" class="w-full max-w-full bg-indigo-50/50 dark:bg-white/5 backdrop-blur-3xl border-indigo-200 dark:border-white/10 p-12 rounded-[2.5rem] text-center border max-w-md">
			<div class="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 mx-auto mb-6">
				<ExclamationCircleOutline size="lg" />
			</div>
			<h2 class="text-xl font-black text-indigo-950 dark:text-white tracking-tighter uppercase mb-2">ACCESS RESTRICTED</h2>
			<p class="text-sm text-indigo-900/60 dark:text-white/40 font-medium">This registry is only accessible to Super Administrators.</p>
		</Card>
	</div>
{:else}
<div class="dash space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
	<!-- Header -->
	<header class="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
		<div>
			<p class="text-[10px] font-black text-indigo-900/50 dark:text-white/30 uppercase tracking-[0.3em] mb-1">
				Personnel / <span class="text-primary-400">Administrative Nodes</span>
			</p>
			<h1 class="text-3xl font-black text-indigo-950 dark:text-white tracking-tighter uppercase">DEPT ADMIN REGISTRY</h1>
		</div>
		
		<div class="flex items-center flex-wrap gap-3">
			<div class="relative group hidden sm:block">
				<SearchOutline size="xs" class="absolute left-3 top-1/2 -translate-y-1/2 text-indigo-900/40 dark:text-white/20 group-focus-within:text-primary-400 transition-colors" />
				<input bind:value={searchQuery} placeholder="FIND ADMINS..." class="bg-indigo-50/50 dark:bg-white/5 border-indigo-200 dark:border-white/10 text-[10px] font-bold text-indigo-950 dark:text-white placeholder:text-indigo-900/30 dark:text-white/10 rounded-xl pl-9 pr-4 py-2 w-48 focus:ring-0 focus:border-primary-400 transition-all shadow-xl" />
			</div>
			<Button color="none" class="bg-indigo-50/50 dark:bg-white/5 border border-indigo-200 dark:border-white/10 text-indigo-900/80 dark:text-white/60 hover:text-indigo-950 dark:text-white hover:bg-indigo-100/50 dark:bg-white/10 px-4 py-2 rounded-xl transition-all font-bold text-[10px] tracking-widest uppercase shadow-xl" onclick={() => loadDeptAdmins()}>
				<RefreshOutline size="xs" class="mr-2" />
				Sync
			</Button>
			<Button color="none" class="bg-indigo-50/50 dark:bg-white/5 border border-indigo-200 dark:border-white/10 text-indigo-900/80 dark:text-white/60 hover:text-indigo-950 dark:text-white hover:bg-indigo-100/50 dark:bg-white/10 px-4 py-2 rounded-xl transition-all font-bold text-[10px] tracking-widest uppercase shadow-xl" onclick={() => { showImport = !showImport; resetForm(); }}>
				<CloudArrowUpOutline size="xs" class="mr-2" />
				Bulk Import
			</Button>
			<Button color={showForm && !editingAdmin ? 'red' : 'primary'} class="px-6 py-2.5 rounded-xl font-black text-[10px] tracking-widest uppercase shadow-xl transition-all active:scale-95" onclick={() => { if(showForm && !editingAdmin) { resetForm(); } else { showForm = true; editingAdmin = null; showImport = false; } }}>
				{#if showForm && !editingAdmin}
					<CloseOutline size="xs" class="mr-2" />
					Cancel
				{:else}
					<PlusOutline size="xs" class="mr-2" />
					Deploy Admin
				{/if}
			</Button>
		</div>
	</header>

	<!-- Import Panel -->
	{#if showImport}
		<div transition:slide={{ duration: 400 }}>
			<Card size="none" class="w-full max-w-full bg-indigo-500/5 backdrop-blur-3xl border-indigo-500/10 p-8 rounded-[2rem] border relative overflow-hidden shadow-2xl">
				<div class="absolute top-0 right-0 p-6 opacity-5 text-indigo-400">
					<CloudArrowUpOutline size="xl" />
				</div>
				
				<header class="mb-8">
					<h2 class="text-xl font-black text-indigo-950 dark:text-white tracking-tighter uppercase mb-1">BULK REGISTRATION</h2>
					<p class="text-[10px] font-bold text-indigo-900/50 dark:text-white/30 uppercase tracking-widest leading-relaxed max-w-2xl">
						Ingest a CSV payload to mass-deploy administrative accounts. <br/>
						Payload Schema: <code class="bg-indigo-50/50 dark:bg-white/5 px-2 py-0.5 rounded text-indigo-300">id_number, first_name, last_name, middle_initial, email, department_name</code>
					</p>
				</header>

				<div class="flex flex-wrap items-center gap-4">
					<label class="cursor-pointer">
						<div class="px-8 py-3 rounded-xl font-black text-[10px] tracking-widest uppercase bg-indigo-500 text-indigo-950 dark:text-white hover:bg-indigo-400 transition-all shadow-2xl flex items-center gap-3">
							{#if isImporting}
								<Spinner size="4" color="current" />
								INGESTING...
							{:else}
								<CloudArrowUpOutline size="xs" />
								UPLOAD PAYLOAD
							{/if}
						</div>
						<input type="file" accept=".csv" class="hidden" onchange={handleImport} disabled={isImporting} />
					</label>
					
					<a href={adminApi.downloadDeptAdminTemplate()} download class="px-6 py-3 rounded-xl font-black text-[10px] tracking-widest uppercase bg-indigo-50/50 dark:bg-white/5 border border-indigo-200 dark:border-white/10 text-indigo-900/80 dark:text-white/60 hover:text-indigo-950 dark:text-white hover:bg-indigo-100/50 dark:bg-white/10 transition-all flex items-center gap-3">
						<DownloadOutline size="xs" />
						GET TEMPLATE
					</a>
				</div>

				{#if importResults.length > 0}
					<div class="mt-8 pt-8 border-t border-indigo-100 dark:border-white/5" in:fade>
						<div class="flex items-center justify-between mb-4">
							<Badge color="green" rounded class="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-black px-4 py-1.5 uppercase tracking-widest">
								{importResults.length} NODES DEPLOYED
							</Badge>
							<Button color="none" class="text-[10px] font-black text-primary-400 hover:text-primary-300 uppercase tracking-widest" onclick={() => {
								const list = importResults.map(r => `Name: ${r.full_name}\nID: ${r.employee_id}\nPassword: ${r.default_password}\nDept: ${r.department}`).join('\n\n---\n\n');
								copyToClipboard(list);
							}}>Copy All Credentials</Button>
						</div>
						
						<div class="bg-black/20 rounded-2xl border border-indigo-100 dark:border-white/5 overflow-hidden max-h-64 overflow-y-auto">
							<Table class="bg-transparent">
								<TableHead class="bg-indigo-50/50 dark:bg-white/5 text-[9px] font-black uppercase tracking-widest border-none">
									<TableHeadCell class="px-6 py-4">Designation</TableHeadCell>
									<TableHeadCell class="px-6 py-4">Auth ID</TableHeadCell>
									<TableHeadCell class="px-6 py-4">Temp Key</TableHeadCell>
									<TableHeadCell class="px-6 py-4 text-right">Ops</TableHeadCell>
								</TableHead>
								<TableBody>
									{#each importResults as r}
										<TableBodyRow class="border-b border-indigo-100 dark:border-white/5">
											<TableBodyCell class="px-6 py-4 text-xs font-bold text-indigo-900/80 dark:text-white/60">{r.full_name}</TableBodyCell>
											<TableBodyCell class="px-6 py-4 font-mono text-[10px] text-primary-400">{r.employee_id}</TableBodyCell>
											<TableBodyCell class="px-6 py-4 font-mono text-[10px] text-emerald-400">{r.default_password}</TableBodyCell>
											<TableBodyCell class="px-6 py-4 text-right">
												<button class="text-indigo-900/40 dark:text-white/20 hover:text-indigo-950 dark:text-white transition-colors" onclick={() => copyToClipboard(`ID: ${r.employee_id}\nPass: ${r.default_password}`)} title="Copy Credentials">
													<PlusOutline size="xs" />
												</button>
											</TableBodyCell>
										</TableBodyRow>
									{/each}
								</TableBody>
							</Table>
						</div>
					</div>
				{/if}
			</Card>
		</div>
	{/if}

	<!-- Registration / Edit Form -->
	{#if showForm}
		<div transition:slide={{ duration: 400 }}>
			<Card size="none" class="w-full max-w-full bg-indigo-50/50 dark:bg-white/5 backdrop-blur-3xl border-indigo-200 dark:border-white/10 p-10 rounded-[2.5rem] border relative overflow-hidden shadow-2xl">
				<div class="absolute top-0 right-0 p-8 opacity-5">
					<UserOutline size="xl" />
				</div>
				
				<header class="mb-10">
					<h2 class="text-xl font-black text-indigo-950 dark:text-white tracking-tighter uppercase mb-1">
						{editingAdmin ? 'Edit Dept Admin' : 'Add Dept Admin'}
					</h2>
					<p class="text-[10px] font-bold text-indigo-900/50 dark:text-white/30 uppercase tracking-widest">
						{editingAdmin ? 'Update profile details' : 'Create a new account'}
					</p>
				</header>

				<form onsubmit={handleAdd} class="space-y-10">
					<!-- Profile Image Upload -->
					<div class="flex items-center gap-8 pb-10 border-b border-indigo-100 dark:border-white/5">
						<div class="relative group">
							<div class="w-24 h-24 rounded-[2rem] bg-gradient-to-br from-primary-500 to-indigo-600 p-1 shadow-2xl">
								<div class="w-full h-full rounded-[1.8rem] bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:bg-none dark:bg-[#0a0f1e] flex items-center justify-center overflow-hidden border border-indigo-200 dark:border-white/10">
									{#if photoPreview}
										<img src={photoPreview} alt="Preview" class="w-full h-full object-cover" />
									{:else}
										<UserOutline size="lg" class="text-indigo-900/30 dark:text-white/10" />
									{/if}
								</div>
							</div>
							<label class="absolute -bottom-2 -right-2 bg-white text-black p-2 rounded-xl shadow-2xl hover:scale-110 transition-transform cursor-pointer border border-indigo-300 dark:border-white/20">
								<CameraPhotoOutline size="xs" />
								<input type="file" accept="image/*" class="hidden" onchange={handlePhotoSelect} />
							</label>
						</div>
						<div class="flex flex-col gap-2">
							<h3 class="text-sm font-black text-indigo-950 dark:text-white tracking-tight uppercase">Profile Picture</h3>
							<p class="text-[10px] font-bold text-indigo-900/40 dark:text-white/20 uppercase tracking-widest">Upload a profile photo</p>
							{#if photoPreview}
								<button type="button" class="text-[9px] font-black text-red-400 uppercase tracking-widest mt-1 hover:text-red-300 transition-colors" onclick={() => { photoPreview = null; newAdmin.photo_url = ''; }}>Remove Image</button>
							{/if}
						</div>
					</div>

					<div class="grid md:grid-cols-2 lg:grid-cols-3 gap-10">
						<div class="space-y-8">
							<div class="relative group">
								<FloatingLabelInput id="input-id_number" type="text" style="filled" bind:value={newAdmin.id_number} disabled={!!editingAdmin} required class="bg-indigo-50/50 dark:bg-white/5 border-none dark:text-white text-indigo-950 dark:text-white focus:border-primary-400 font-bold uppercase">
									Employee ID
								</FloatingLabelInput>
							</div>
							<div class="relative group">
								<FloatingLabelInput id="input-first_name" type="text" style="filled" bind:value={newAdmin.first_name} required class="bg-indigo-50/50 dark:bg-white/5 border-none dark:text-white text-indigo-950 dark:text-white focus:border-primary-400 font-bold">
									First Name
								</FloatingLabelInput>
							</div>
						</div>

						<div class="space-y-8">
							<div class="relative group">
								<FloatingLabelInput id="input-password" type="password" style="filled" bind:value={newAdmin.password} disabled={!!editingAdmin} required={!editingAdmin} class="bg-indigo-50/50 dark:bg-white/5 border-none dark:text-white text-indigo-950 dark:text-white focus:border-primary-400 font-bold">
									{editingAdmin ? '••••••••' : 'Password'}
								</FloatingLabelInput>
							</div>
							<div class="relative group">
								<FloatingLabelInput id="input-last_name" type="text" style="filled" bind:value={newAdmin.last_name} required class="bg-indigo-50/50 dark:bg-white/5 border-none dark:text-white text-indigo-950 dark:text-white focus:border-primary-400 font-bold">
									Last Name
								</FloatingLabelInput>
							</div>
						</div>

						<div class="space-y-8">
							<div class="relative group">
								<FloatingLabelInput id="input-email" type="email" style="filled" bind:value={newAdmin.email} required class="bg-indigo-50/50 dark:bg-white/5 border-none dark:text-white text-indigo-950 dark:text-white focus:border-primary-400 font-bold">
									Email Address
								</FloatingLabelInput>
							</div>
							<div class="relative group">
								<FloatingLabelInput id="input-middle_initial" type="text" style="filled" bind:value={newAdmin.middle_initial} class="bg-indigo-50/50 dark:bg-white/5 border-none dark:text-white text-indigo-950 dark:text-white focus:border-primary-400 font-bold">
									Middle Initial (Opt)
								</FloatingLabelInput>
							</div>
						</div>
					</div>

					<div class="space-y-4 pt-4">
						<Label for="adm-dept" class="text-[10px] font-black text-indigo-900/60 dark:text-white/40 uppercase tracking-widest mb-2 block">Department</Label>
						<Select id="adm-dept" bind:value={newAdmin.department_id} class="bg-indigo-50/50 dark:bg-white/5 border-none text-indigo-950 dark:text-white focus:border-primary-400 rounded-2xl py-3 font-bold">
							<option value="" class="bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:bg-none dark:bg-[#0a0f1e]">No Department / Global</option>
							{#each departments as dept}
								<option value={dept.id} class="bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:bg-none dark:bg-[#0a0f1e]">{dept.name.toUpperCase()}</option>
							{/each}
						</Select>
					</div>

					<div class="flex justify-end gap-4 pt-10 border-t border-indigo-100 dark:border-white/5">
						
						<Button type="submit" disabled={isSaving} class="px-10 py-4 rounded-2xl font-black text-[10px] tracking-widest uppercase bg-white text-indigo-950 hover:bg-primary-500 hover:text-white dark:bg-primary-600 dark:text-white dark:hover:bg-primary-500 dark:border-none transition-all shadow-2xl flex items-center gap-3">
							{#if isSaving}
								<Spinner size="4" color="current" />
								SYNCING...
							{:else}
								{editingAdmin ? 'Update Account' : 'Save Account'}
								<CheckCircleOutline size="sm" />
							{/if}
						</Button>
					</div>
				</form>
			</Card>
		</div>
	{/if}

	<!-- Data Registry Table -->
	<Card size="none" class="w-full max-w-full bg-indigo-50/50 dark:bg-white/5 backdrop-blur-3xl border-indigo-200 dark:border-white/10 rounded-[2.5rem] border overflow-hidden shadow-2xl relative">
		<header class="p-8 border-b border-indigo-100 dark:border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4 bg-indigo-50/30 dark:bg-white/[0.02]">
			<div>
				<h3 class="text-sm font-black text-indigo-950 dark:text-white tracking-[0.2em] uppercase">Administrative Directory</h3>
				<p class="text-[9px] font-bold text-indigo-900/40 dark:text-white/20 uppercase tracking-widest mt-1">Verified Structural Node Operators</p>
			</div>
			<div class="flex items-center gap-2">
				<Badge color="blue" rounded class="bg-primary-500/10 text-primary-400 border border-primary-500/20 font-black px-4 py-1 uppercase tracking-widest text-[9px]">
					{deptAdmins.length} REGISTRY NODES
				</Badge>
			</div>
		</header>

		{#if isLoading}
			<div class="p-8 space-y-4">
				{#each Array(5) as _}
					<Skeleton class="h-16 w-full bg-indigo-50/50 dark:bg-white/5 rounded-2xl" />
				{/each}
			</div>
		{:else if filteredAdmins.length === 0}
			<div class="p-24 text-center flex flex-col items-center justify-center gap-4 opacity-20">
				<UserOutline size="xl" />
				<p class="text-xs font-black tracking-[0.3em] uppercase">{searchQuery ? 'No Matching Registry Nodes' : 'No Administrative Data found'}</p>
			</div>
		{:else}
			<div class="overflow-x-auto">
				<Table hoverable={true} class="bg-transparent">
					<TableHead class="bg-indigo-50/50 dark:bg-white/[0.03] border-b border-indigo-100 dark:border-white/5">
						<TableHeadCell class="px-8 py-5 text-[10px] font-black text-indigo-900/60 dark:text-white/40 uppercase tracking-widest border-none">Node Operator</TableHeadCell>
						<TableHeadCell class="px-8 py-5 text-[10px] font-black text-indigo-900/60 dark:text-white/40 uppercase tracking-widest border-none">Auth Access</TableHeadCell>
						<TableHeadCell class="px-8 py-5 text-[10px] font-black text-indigo-900/60 dark:text-white/40 uppercase tracking-widest border-none">Institutional Node</TableHeadCell>
						<TableHeadCell class="px-8 py-5 text-[10px] font-black text-indigo-900/60 dark:text-white/40 uppercase tracking-widest border-none text-right">Registry Ops</TableHeadCell>
					</TableHead>
					<TableBody>
						{#each filteredAdmins as admin (admin.id)}
							<TableBodyRow class="border-b border-white/[0.03] hover:bg-indigo-50/30 dark:bg-white/[0.02] transition-colors group">
								<TableBodyCell class="px-8 py-6 border-none">
									<div class="flex items-center gap-4">
										<Avatar src={admin.photo_url} alt={admin.full_name} border class="bg-primary-500/10 border-indigo-200 dark:border-white/10" size="sm" rounded />
										<div class="flex flex-col">
											<span class="text-sm font-bold text-indigo-950 dark:text-white tracking-tight leading-tight">{admin.full_name}</span>
											<span class="text-[9px] font-black text-indigo-900/40 dark:text-white/20 uppercase tracking-widest mt-1">{admin.email || 'NO_EMAIL_REGISTRY'}</span>
										</div>
									</div>
								</TableBodyCell>
								<TableBodyCell class="px-8 py-6 border-none">
									<div class="flex items-center gap-3">
										<span class="font-mono text-[11px] font-bold text-primary-400 tracking-wider">
											{visibleIds.has(admin.id) ? admin.id_number : '••••••••'}
										</span>
										<button class="text-indigo-900/30 dark:text-white/10 hover:text-indigo-950 dark:text-white transition-colors" onclick={() => toggleIdVisibility(admin.id)}>
											{#if visibleIds.has(admin.id)}<EyeSlashOutline size="xs" />{:else}<EyeOutline size="xs" />{/if}
										</button>
									</div>
								</TableBodyCell>
								<TableBodyCell class="px-8 py-6 border-none">
									{#if getDeptName(admin.department_id)}
										<Badge color="blue" rounded class="bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-black px-3 py-1 uppercase tracking-widest text-[8px]">
											{getDeptName(admin.department_id)}
										</Badge>
									{:else}
										<span class="text-[9px] font-black text-indigo-900/40 dark:text-white/20 uppercase tracking-widest">Global Admin</span>
									{/if}
								</TableBodyCell>
								<TableBodyCell class="px-8 py-6 border-none text-right">
									<div class="flex items-center justify-end gap-2">
										<button class="p-2.5 bg-indigo-50/50 dark:bg-white/5 border border-indigo-200 dark:border-white/10 text-indigo-900/50 dark:text-white/30 hover:text-indigo-950 dark:text-white hover:bg-indigo-100/50 dark:bg-white/10 rounded-xl transition-all" onclick={() => startEdit(admin)} title="Edit Node">
											<EditOutline size="xs" />
										</button>
										<button class="p-2.5 bg-red-500/5 border border-red-500/10 text-red-500/40 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all" onclick={() => promptDelete(admin)} title="Decommission Node">
											<TrashBinOutline size="xs" />
										</button>
									</div>
								</TableBodyCell>
							</TableBodyRow>
						{/each}
					</TableBody>
				</Table>
			</div>
		{/if}

		<!-- Pagination -->
		<footer class="p-8 flex items-center justify-between border-t border-indigo-100 dark:border-white/5 bg-white/[0.01]">
			<button class="px-6 py-2 rounded-xl font-black text-[9px] tracking-[0.3em] uppercase bg-indigo-50/50 dark:bg-white/5 border border-indigo-200 dark:border-white/10 text-indigo-900/60 dark:text-white/40 hover:text-indigo-950 dark:text-white hover:bg-indigo-100/50 dark:bg-white/10 transition-all disabled:opacity-20 disabled:cursor-not-allowed" onclick={goPrev} disabled={currentPage === 0 || isLoading}>PREV_PAGE</button>
			<span class="text-[10px] font-black text-indigo-900/40 dark:text-white/20 tracking-[0.5em] uppercase italic">BLOCK {currentPage + 1}</span>
			<button class="px-6 py-2 rounded-xl font-black text-[9px] tracking-[0.3em] uppercase bg-indigo-50/50 dark:bg-white/5 border border-indigo-200 dark:border-white/10 text-indigo-900/60 dark:text-white/40 hover:text-indigo-950 dark:text-white hover:bg-indigo-100/50 dark:bg-white/10 transition-all disabled:opacity-20 disabled:cursor-not-allowed" onclick={goNext} disabled={!nextPageToken || isLoading}>NEXT_PAGE</button>
		</footer>
	</Card>
</div>
{/if}

<Notification text={notification.text} type={notification.type} />

<ConfirmModal
	show={confirmState.show}
	title={confirmState.title}
	message={confirmState.message}
	onConfirm={confirmState.onConfirm}
	onCancel={() => (confirmState.show = false)}
/>
