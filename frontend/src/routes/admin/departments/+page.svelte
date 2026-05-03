<script>
	import { onMount } from 'svelte';
	import { admin as adminApi } from '$lib/api.js';
	import { branding } from '$lib/stores/branding.js';
	import { dataCache } from '$lib/stores/data.js';
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
		Textarea,
		Helper
	} from 'flowbite-svelte';
	import {
		PlusOutline,
		RefreshOutline,
		CloseOutline,
		EditOutline,
		TrashBinOutline,
		BuildingOutline,
		SearchOutline,
		FilterOutline
	} from 'flowbite-svelte-icons';

	let departments = $state([]);
	let isLoading = $state(true);
	let isSaving = $state(false);
	let showForm = $state(false);
	let editingDept = $state(null);
	let newDept = $state({ name: '', code: '', description: '' });

	/** @type {{ text: string, type: 'info' | 'success' | 'error' }} */
	let notification = $state({ text: '', type: 'info' });

	let confirmState = $state({
		show: false,
		title: '',
		message: '',
		onConfirm: () => {},
		id: ''
	});

	$effect(() => {
		if ($dataCache.departments.length > 0) {
			departments = $dataCache.departments;
			isLoading = false;
		}
	});

	onMount(async () => {
		await loadDepartments();
	});

	async function loadDepartments() {
		try {
			const res = await adminApi.getDepartments();
			const data = res.data ?? [];
			dataCache.setDepartments(data);
			departments = data;
		} catch (err) {
			notify('Failed to load departments', 'error');
		} finally {
			isLoading = false;
		}
	}

	function notify(text = '', type = 'info') {
		notification = { text, type };
		setTimeout(() => (notification = { text: '', type: 'info' }), 3500);
	}

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
		} catch (err) {
			notify(err.message ?? 'Failed to save department', 'error');
		} finally {
			isSaving = false;
		}
	}

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
				dataCache.setDepartments(departments);
				try {
					await adminApi.deleteDepartment(targetId);
					notify('Department removed', 'success');
				} catch (err) {
					departments = originalDepts;
					dataCache.setDepartments(departments);
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
			<Button color="none" class="bg-indigo-50/50 dark:bg-white/5 border border-indigo-200 dark:border-white/10 text-indigo-900/80 dark:text-white/60 hover:text-indigo-950 dark:text-white hover:bg-indigo-100/50 dark:bg-white/10 px-4 py-2 rounded-xl transition-all font-bold text-[10px] tracking-widest uppercase" onclick={loadDepartments}>
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
			<Card size="none" class="w-full max-w-full bg-indigo-50/50 dark:bg-white/5 backdrop-blur-3xl border-indigo-200 dark:border-white/10 p-8 rounded-[2rem] border relative overflow-hidden shadow-2xl">
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
						<div class="space-y-8">
							<div class="relative group">
								<FloatingLabelInput id="input-name" type="text" style="filled" bind:value={newDept.name} required class="bg-indigo-50/50 dark:bg-white/5 border-none dark:text-white text-indigo-950 dark:text-white focus:border-primary-400 font-bold">
									Full Department Name
								</FloatingLabelInput>
								<Helper class="mt-2 text-[9px] font-bold text-indigo-900/40 dark:text-white/20 tracking-widest uppercase">Official Academic Title</Helper>
							</div>
							
							<div class="relative group">
								<FloatingLabelInput id="input-code" type="text" style="filled" bind:value={newDept.code} required class="bg-indigo-50/50 dark:bg-white/5 border-none dark:text-white text-indigo-950 dark:text-white focus:border-primary-400 font-bold">
									Institutional Code
								</FloatingLabelInput>
								<Helper class="mt-2 text-[9px] font-bold text-indigo-900/40 dark:text-white/20 tracking-widest uppercase">E.G. CAS, CITE, CBA</Helper>
							</div>
						</div>

						<div class="relative group h-full">
							<Label for="dept-desc" class="text-[10px] font-black text-indigo-900/60 dark:text-white/40 uppercase tracking-widest mb-3 block">Structural Overview</Label>
							<Textarea id="dept-desc" bind:value={newDept.description} rows={5} placeholder="Brief description of the department's role..." class="bg-indigo-50/50 dark:bg-white/5 border-none text-indigo-950 dark:text-white focus:border-primary-400 rounded-2xl resize-none" />
						</div>
					</div>

					<div class="flex justify-end gap-4 pt-4 border-t border-indigo-100 dark:border-white/5">
						
						<Button type="submit" disabled={isSaving} class="px-8 py-3 rounded-xl font-black text-[10px] tracking-widest uppercase bg-white text-indigo-950 hover:bg-primary-500 hover:text-white dark:bg-primary-600 dark:text-white dark:hover:bg-primary-500 dark:border-none transition-all shadow-2xl flex items-center gap-3">
							{#if isSaving}
								<Spinner size="4" color="current" />
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
	<Card size="none" class="w-full max-w-full bg-indigo-50/50 dark:bg-white/5 backdrop-blur-3xl border-indigo-200 dark:border-white/10 rounded-[2rem] border overflow-hidden shadow-2xl relative">
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
				<Button color="none" class="p-2 bg-indigo-50/50 dark:bg-white/5 border border-indigo-200 dark:border-white/10 text-indigo-900/60 dark:text-white/40 hover:text-indigo-950 dark:text-white rounded-xl transition-all">
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
