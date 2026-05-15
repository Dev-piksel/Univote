<script>
	import { onMount } from 'svelte';
	import { admin as adminApi } from '$lib/api.js';
	import { branding } from '$lib/stores/branding.js';
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
		Card
	} from 'flowbite-svelte';
	import {
		PlusOutline,
		RefreshOutline,
		CloseOutline,
		EditOutline,
		TrashBinOutline,
		BuildingOutline,
		SearchOutline,
		FilterOutline,
		CheckCircleOutline
	} from 'flowbite-svelte-icons';

	/** @typedef {object} Department @property {string} id @property {string} name @property {string} [code] @property {string} [description] @property {string} [created_at] */

	/** @type {Department[]} */
	let departments = $state([]);
	let isLoading = $state(true);
	let isSaving = $state(false);
	let showForm = $state(false);
	/** @type {Department|null} */
	let editingDept = $state(null);
	let newDept = $state({ name: '', code: '', description: '' });

	/** @type {{ text: string, type: 'info' | 'success' | 'error' | 'warning' }} */
	let notification = $state({ text: '', type: 'info' });

	let confirmState = $state({
		show: false,
		title: '',
		message: '',
		onConfirm: () => {},
		id: ''
	});


	onMount(async () => {
		await loadDepartments();
	});

	async function loadDepartments() {
		try {
			const res = await adminApi.getDepartments();
			departments = res.data ?? [];
		} catch (err) {
			notify('Failed to load departments', 'error');
		} finally {
			isLoading = false;
		}
	}

	/** @param {string} text @param {'info' | 'success' | 'error' | 'warning'} type */
	function notify(text = '', type = 'info') {
		notification = { text, type };
		setTimeout(() => (notification = { text: '', type: 'info' }), 3500);
	}

	/** @param {SubmitEvent} e */
	async function handleSubmit(e) {
		e.preventDefault();
		if (!newDept.name) { notify('Department name is required.', 'error'); return; }
		isSaving = true;
		try {
			if (editingDept) {
				await adminApi.updateDepartment(editingDept.id, newDept);
				notify('Department updated', 'success');
			} else {
				await adminApi.createDepartment(newDept);
				notify('Department created', 'success');
			}
			resetForm();
			await loadDepartments();
		} catch (/** @type {any} */ err) {
			notify(err.message ?? 'Failed to save department', 'error');
		} finally {
			isSaving = false;
		}
	}

	/** @param {Department} dept */
	function startEdit(dept) {
		editingDept = dept;
		newDept = { name: dept.name, code: dept.code || '', description: dept.description || '' };
		showForm = true;
	}

	function resetForm() {
		editingDept = null;
		newDept = { name: '', code: '', description: '' };
		showForm = false;
	}

	/** @param {Department} dept */
	function promptDelete(dept) {
		confirmState = {
			show: true,
			title: 'Delete Department',
			message: `Are you sure you want to remove ${dept.name}? This may fail if students are still assigned to this department.`,
			id: dept.id,
			onConfirm: async () => {
				const targetId = confirmState.id;
				const originalDepts = [...departments];
				departments = departments.filter(d => d.id !== targetId);
				try {
					await adminApi.deleteDepartment(targetId);
					notify('Department removed', 'success');
				} catch (/** @type {any} */ err) {
					departments = originalDepts;
					notify(err.message ?? 'Failed to delete department', 'error');
				} finally {
					confirmState.show = false;
				}
			}
		};
	}
</script>

<svelte:head><title>Departments | {$branding.appName}</title></svelte:head>

<div class="dash space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
	<!-- Header Section -->
	<header class="flex flex-col md:flex-row md:items-end justify-between gap-6">
		<div>
			<p class="text-[10px] font-black text-indigo-900/50 dark:text-white/30 uppercase tracking-[0.3em] mb-1">
				Governance / <span class="text-primary-400">Structure Control</span>
			</p>
			<h1 class="text-3xl font-black text-indigo-950 dark:text-white tracking-tighter uppercase">DEPARTMENT MANAGEMENT</h1>
		</div>
		
		<div class="flex items-center gap-3">
			<Button color="light" class="bg-indigo-50/50 dark:bg-white/5 border border-indigo-200 dark:border-white/10 text-indigo-900/80 dark:text-white/60 hover:text-indigo-950 dark:text-white hover:bg-indigo-100/50 dark:bg-white/10 px-4 py-2 rounded-xl transition-all font-bold text-[10px] tracking-widest uppercase" onclick={loadDepartments}>
				<RefreshOutline size="xs" class="mr-2" />
				Sync Registry
			</Button>
			<Button color={showForm && !editingDept ? 'red' : 'primary'} class="px-6 py-2.5 rounded-xl font-black text-[10px] tracking-widest uppercase shadow-xl transition-all active:scale-95" onclick={() => { if (showForm && !editingDept) resetForm(); else { showForm = true; editingDept = null; } }}>
				{#if showForm && !editingDept}
					<CloseOutline size="xs" class="mr-2" />
					Cancel Entry
				{:else}
					<PlusOutline size="xs" class="mr-2" />
					Register Department
				{/if}
			</Button>
		</div>
	</header>

	<!-- Registration / Edit Form -->
	{#if showForm}
		<div transition:slide={{ duration: 400 }}>
			<Card size="md" class="w-full max-w-full bg-indigo-50/50 dark:bg-white/5 backdrop-blur-3xl border-indigo-200 dark:border-white/10 p-8 rounded-[2rem] border relative overflow-hidden shadow-2xl">
				<div class="absolute top-0 right-0 p-6 opacity-5">
					<BuildingOutline size="xl" />
				</div>
				
				<header class="mb-10">
					<h2 class="text-xl font-black text-indigo-950 dark:text-white tracking-tighter uppercase mb-1">
						{editingDept ? 'MODIFY REGISTRATION' : 'NEW DEPARTMENT REGISTRY'}
					</h2>
					<p class="text-[10px] font-bold text-indigo-900/50 dark:text-white/30 uppercase tracking-widest">
						{editingDept ? 'Update structural details for this department' : 'Establish a new institutional entity'}
					</p>
				</header>

				<form onsubmit={handleSubmit} class="space-y-8">
					<div class="grid md:grid-cols-[1.5fr_1fr] gap-8">
						<div class="space-y-6">
							<!-- Department Name -->
							<div class="relative group">
								<div class="absolute -inset-px bg-primary-500/20 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-all duration-500 pointer-events-none"></div>
								<div class="relative bg-white/[0.04] border border-white/10 rounded-2xl overflow-hidden group-focus-within:border-primary-400 transition-all duration-300">
									<input
										id="input-name"
										type="text"
										bind:value={newDept.name}
										required
										placeholder=" "
										class="peer w-full px-4 pt-6 pb-2 bg-transparent text-white placeholder-transparent outline-none font-semibold text-sm tracking-wide focus:ring-0"
									/>
									<label for="input-name" class="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 font-black text-[9px] uppercase tracking-[0.3em] pointer-events-none transition-all duration-300 peer-focus:-translate-y-[1.1rem] peer-focus:scale-90 peer-[:not(:placeholder-shown)]:-translate-y-[1.1rem] peer-[:not(:placeholder-shown)]:scale-90 origin-left">
										Full Department Name
									</label>
								</div>
								<p class="mt-2 text-[9px] font-bold text-white/20 uppercase tracking-widest px-1">Official Academic Title</p>
							</div>

							<!-- Institutional Code -->
							<div class="relative group">
								<div class="absolute -inset-px bg-primary-500/20 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-all duration-500 pointer-events-none"></div>
								<div class="relative bg-white/[0.04] border border-white/10 rounded-2xl overflow-hidden group-focus-within:border-primary-400 transition-all duration-300">
									<input
										id="input-code"
										type="text"
										bind:value={newDept.code}
										placeholder=" "
										class="peer w-full px-4 pt-6 pb-2 bg-transparent text-white placeholder-transparent outline-none font-semibold text-sm tracking-wide focus:ring-0"
									/>
									<label for="input-code" class="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 font-black text-[9px] uppercase tracking-[0.3em] pointer-events-none transition-all duration-300 peer-focus:-translate-y-[1.1rem] peer-focus:scale-90 peer-[:not(:placeholder-shown)]:-translate-y-[1.1rem] peer-[:not(:placeholder-shown)]:scale-90 origin-left">
										Institutional Code
									</label>
								</div>
								<p class="mt-2 text-[9px] font-bold text-white/20 uppercase tracking-widest px-1">E.g. CAS, CITE, CBA</p>
							</div>
						</div>

						<!-- Description textarea -->
						<div class="relative group h-full">
							<label for="dept-desc" class="block text-[9px] font-black text-white/40 uppercase tracking-widest mb-2 px-1">Structural Overview</label>
							<div class="absolute -inset-px bg-primary-500/20 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-all duration-500 pointer-events-none"></div>
							<textarea
								id="dept-desc"
								bind:value={newDept.description}
								rows="5"
								placeholder="Brief description of the department's role..."
								class="relative w-full px-4 py-3 bg-white/[0.04] border border-white/10 rounded-2xl text-white placeholder-white/20 outline-none font-semibold text-sm tracking-wide focus:ring-0 focus:border-primary-400 transition-all duration-300 resize-none"
							></textarea>
						</div>
					</div>

					<div class="flex justify-end gap-4 pt-4 border-t border-indigo-100 dark:border-white/5">
						
						<Button type="submit" disabled={isSaving} class="px-8 py-3 rounded-xl font-black text-[10px] tracking-widest uppercase bg-white text-indigo-950 hover:bg-primary-500 hover:text-white dark:bg-primary-600 dark:text-white dark:hover:bg-primary-500 dark:border-none transition-all shadow-2xl flex items-center gap-3">
							{#if isSaving}
								<Spinner size="4" color="blue" />
								PROCESS...
							{:else}
								{editingDept ? 'Update Account' : 'EXECUTE REGISTRATION'}
								<CheckCircleOutline size="sm" />
							{/if}
						</Button>
					</div>
				</form>
			</Card>
		</div>
	{/if}

	<!-- Data Registry Table -->
	<Card size="md" class="w-full max-w-full bg-indigo-50/50 dark:bg-white/5 backdrop-blur-3xl border-indigo-200 dark:border-white/10 rounded-[2rem] border overflow-hidden shadow-2xl relative">
		<header class="p-8 border-b border-indigo-100 dark:border-white/5 flex items-center justify-between bg-indigo-50/30 dark:bg-white/[0.02]">
			<div>
				<h3 class="text-sm font-black text-indigo-950 dark:text-white tracking-[0.2em] uppercase">Structural Registry</h3>
				<p class="text-[9px] font-bold text-indigo-900/40 dark:text-white/20 uppercase tracking-widest mt-1">Verified Institutional Nodes</p>
			</div>
			<div class="flex items-center gap-4">
				<div class="relative hidden sm:block">
					<SearchOutline size="xs" class="absolute left-3 top-1/2 -translate-y-1/2 text-indigo-900/40 dark:text-white/20" />
					<input type="text" placeholder="FILTER NODES..." class="bg-indigo-50/50 dark:bg-white/5 border-indigo-200 dark:border-white/10 text-[10px] font-bold text-indigo-950 dark:text-white placeholder:text-indigo-900/30 dark:text-white/10 rounded-xl pl-9 pr-4 py-2 w-48 focus:ring-0 focus:border-primary-400 transition-all" />
				</div>
				<Button color="light" class="p-2 bg-indigo-50/50 dark:bg-white/5 border border-indigo-200 dark:border-white/10 text-indigo-900/60 dark:text-white/40 hover:text-indigo-950 dark:text-white rounded-xl transition-all">
					<FilterOutline size="xs" />
				</Button>
			</div>
		</header>

		{#if isLoading}
			<div class="p-8 space-y-4">
				{#each Array(5) as _}
					<Skeleton class="h-14 w-full bg-indigo-50/50 dark:bg-white/5 rounded-xl" />
				{/each}
			</div>
		{:else if departments.length === 0}
			<div class="p-20 text-center flex flex-col items-center justify-center gap-4 opacity-20">
				<BuildingOutline size="xl" />
				<p class="text-xs font-black tracking-[0.3em] uppercase">No Structural Data Found</p>
			</div>
		{:else}
			<div class="overflow-x-auto">
				<Table hoverable={true} class="bg-transparent">
					<TableHead class="bg-indigo-50/50 dark:bg-white/[0.03] border-b border-indigo-100 dark:border-white/5">
						<TableHeadCell class="px-8 py-5 text-[10px] font-black text-indigo-900/60 dark:text-white/40 uppercase tracking-widest border-none">Node ID</TableHeadCell>
						<TableHeadCell class="px-8 py-5 text-[10px] font-black text-indigo-900/60 dark:text-white/40 uppercase tracking-widest border-none">Official Designation</TableHeadCell>
						<TableHeadCell class="px-8 py-5 text-[10px] font-black text-indigo-900/60 dark:text-white/40 uppercase tracking-widest border-none hidden md:table-cell">Registry Date</TableHeadCell>
						<TableHeadCell class="px-8 py-5 text-[10px] font-black text-indigo-900/60 dark:text-white/40 uppercase tracking-widest border-none text-right">Operations</TableHeadCell>
					</TableHead>
					<TableBody>
						{#each departments as dept}
							<TableBodyRow class="border-b border-white/[0.03] hover:bg-indigo-50/30 dark:bg-white/[0.02] transition-colors group">
								<TableBodyCell class="px-8 py-6 border-none">
									<Badge color="blue" class="bg-primary-500/10 text-primary-400 border border-primary-500/20 font-mono font-bold text-[10px] tracking-widest px-3 py-1 rounded-lg shadow-xl">
										{dept.code || 'SYS-X'}
									</Badge>
								</TableBodyCell>
								<TableBodyCell class="px-8 py-6 border-none">
									<div class="flex flex-col">
										<span class="text-sm font-bold text-indigo-950 dark:text-white tracking-tight">{dept.name}</span>
										<span class="text-[9px] font-black text-indigo-900/40 dark:text-white/20 uppercase tracking-widest mt-1 truncate max-w-xs">{dept.description || 'No system notes established'}</span>
									</div>
								</TableBodyCell>
								<TableBodyCell class="px-8 py-6 border-none hidden md:table-cell">
									<span class="text-[10px] font-black text-indigo-900/60 dark:text-white/40 uppercase tracking-widest">
										{dept.created_at ? new Date(dept.created_at).toLocaleDateString() : 'LEGACY'}
									</span>
								</TableBodyCell>
								<TableBodyCell class="px-8 py-6 border-none text-right">
									<div class="flex items-center justify-end gap-2">
										<button class="p-2.5 bg-indigo-50/50 dark:bg-white/5 border border-indigo-200 dark:border-white/10 text-indigo-900/50 dark:text-white/30 hover:text-indigo-950 dark:text-white hover:bg-indigo-100/50 dark:bg-white/10 rounded-xl transition-all" onclick={() => startEdit(dept)} title="Edit Node">
											<EditOutline size="xs" />
										</button>
										<button class="p-2.5 bg-red-500/5 border border-red-500/10 text-red-500/40 hover:text-red-400 hover:bg-red-500/10 rounded-xl transition-all" onclick={() => promptDelete(dept)} title="Delete Node">
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
	</Card>
</div>

<Notification text={notification.text} type={notification.type} />

<ConfirmModal
	show={confirmState.show}
	title={confirmState.title}
	message={confirmState.message}
	onConfirm={confirmState.onConfirm}
	onCancel={() => (confirmState.show = false)}
/>
