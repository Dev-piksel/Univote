<script>
	import { onMount } from 'svelte';
	import { student as studentApi } from '$lib/api.js';
	import { voterSession } from '$lib/stores/session.js';
	import { formatDepartment } from '$lib/utils.js';
	import { branding } from '$lib/stores/branding.js';
	import { fade, fly, scale, slide } from 'svelte/transition';
	import {
		Badge, 
		Button, 
		Spinner
	} from 'flowbite-svelte';
	import {
		CalendarMonthOutline,
		CheckCircleOutline,
		ClockOutline,
		GridOutline,
		ChartPieOutline,
		FileSearchOutline,
		ArrowRightOutline,
		InfoCircleOutline,
		ClipboardCheckOutline,
		UserCircleOutline,
		ShieldCheckOutline,
		DatabaseOutline
	} from 'flowbite-svelte-icons';

	let isLoading = $state(!$voterSession?.student_id);
	/** @type {Array<{id: string, name: string, start_date?: string, end_date?: string, has_voted: boolean, status: string, is_unanimous?: boolean}>} */
	let elections = $derived($voterSession?.elections || []);
	let activeElections = $derived(elections.filter((e) => e.status === 'active'));
	let upcomingElections = $derived(elections.filter((e) => e.status === 'upcoming'));
	let voterName = $derived($voterSession?.full_name || 'Student');
	let program = $derived(formatDepartment($voterSession?.program) || 'General Program');
	let yearLevel = $derived($voterSession?.year_level ? `${$voterSession.year_level}th Year` : 'Academic Level');

	const stats = $derived({
		total: elections.length,
		voted: elections.filter((e) => e.has_voted).length,
		pending: activeElections.filter((e) => !e.has_voted && !e.is_unanimous).length
	});

	/** @param {string | undefined} dateStr */
	function getDaysLeft(dateStr) {
		if (!dateStr) return '';
		const diff = new Date(dateStr).getTime() - Date.now();
		const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
		if (days < 0) return 'EXPIRED';
		if (days === 0) return 'ENDS TODAY';
		return `${days} DAYS LEFT`;
	}

	/** @param {string} name */
	function getGreetingText() {
		const hour = new Date().getHours();
		if (hour < 12) return 'Good Morning';
		if (hour < 18) return 'Good Afternoon';
		return 'Good Evening';
	}

	// Receipt Drawer Logic
	let selectedSummaryId = $state(/** @type {string | null} */ (null));
	/** @type {any} */
	let receiptData = $state(null);
	let receiptLoading = $state(false);

	/** @param {string} electionId */
	async function toggleReceipt(electionId) {
		if (selectedSummaryId === electionId) {
			selectedSummaryId = null;
			receiptData = null;
			return;
		}

		receiptLoading = true;
		selectedSummaryId = electionId;
		try {
			const res = await studentApi.getVoteSummary($voterSession?.student_id || '', electionId);
			receiptData = res;
		} catch (err) {
			console.error('Failed to load receipt:', err);
		} finally {
			receiptLoading = false;
		}
	}

	onMount(async () => {
		try {
			if ($voterSession?.student_id) {
				await voterSession.sync($voterSession.student_id);
			}
		} catch (err) {
			console.error('Failed to sync session:', err);
		} finally {
			isLoading = false;
		}
	});
</script>

<svelte:head><title>Dashboard | {$branding.appName}</title></svelte:head>

<div class="min-h-screen text-[var(--text-main)] p-4 md:p-8 relative" in:fly={{ y: 20, duration: 450 }}>
	
	{#if isLoading}
		<div class="flex flex-col items-center justify-center min-h-[70vh] gap-8" in:fade>
			<div class="relative w-24 h-24">
				<div class="absolute inset-0 rounded-full border-4 border-[var(--brand-primary)]/10 animate-ping"></div>
				<div class="absolute inset-2 rounded-full border-4 border-t-[var(--brand-primary)] border-r-transparent border-b-transparent border-l-transparent animate-spin"></div>
			</div>
			<p class="font-black tracking-[0.2em] animate-pulse text-[10px] uppercase opacity-40">Loading Dashboard...</p>
		</div>
	{:else}
				<!-- Header Unit -->
		<header class="flex flex-col lg:flex-row items-center justify-between mb-10 md:mb-16 gap-6 md:gap-8" in:fly={{ y: -30, duration: 800 }}>
			<div class="flex-1 text-center lg:text-left">
				<h1 class="text-3xl md:text-7xl font-black tracking-tighter uppercase italic leading-tight mb-4 md:mb-6 text-[var(--text-main)]">
					{getGreetingText()}, <span style="color: var(--brand-primary);">{voterName.split(' ')[0]}</span>
				</h1>
			</div>
			
			<!-- User Context (Desktop Only) -->
			<div class="hidden lg:flex items-center gap-6" in:fly={{ x: 40, delay: 200, duration: 1000 }}>
				<div class="text-right border-r border-[var(--border-main)] pr-6">
					<p class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--text-subtle)] mb-1 opacity-50">Department</p>
					<p class="text-2xl font-black text-[var(--text-main)] uppercase tracking-tight leading-tight">{program}</p>
				</div>
				<div class="text-[var(--brand-primary)] opacity-40">
					<UserCircleOutline size="lg" />
				</div>
			</div>
		</header>

	<!-- Status Bento Grid -->
	<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-20 relative z-10">
		<!-- Card 1 -->
		<div class="bg-[var(--bg-card)]/20 backdrop-blur-3xl border border-[var(--border-main)] rounded-[2rem] p-6 shadow-xl flex items-center gap-5 group hover:border-[var(--brand-primary)] transition-all" in:fly={{ y: 30, delay: 300, duration: 800 }}>
			<div class="p-4 bg-emerald-500/10 text-emerald-600 rounded-2xl border border-emerald-500/20 group-hover:scale-110 transition-transform shadow-inner">
				<CheckCircleOutline size="md" />
			</div>
			<div>
				<p class="text-[9px] font-black text-[var(--text-subtle)] uppercase tracking-widest opacity-50 mb-0.5">Votes Recorded</p>
				<h4 class="text-3xl font-black text-[var(--text-main)] leading-none italic tabular-nums" in:scale={{ delay: 500 }}>{stats.voted}</h4>
			</div>
		</div>
		<!-- Card 2 -->
		<div class="bg-[var(--bg-card)]/20 backdrop-blur-3xl border border-[var(--border-main)] rounded-[2rem] p-6 shadow-xl flex items-center gap-5 group hover:border-amber-500 transition-all" in:fly={{ y: 30, delay: 450, duration: 800 }}>
			<div class="p-4 bg-amber-500/10 text-amber-600 rounded-2xl border border-amber-500/20 group-hover:scale-110 transition-transform shadow-inner">
				<ClockOutline size="md" />
			</div>
			<div>
				<p class="text-[9px] font-black text-[var(--text-subtle)] uppercase tracking-widest opacity-50 mb-0.5">Pending Votes</p>
				<h4 class="text-3xl font-black text-[var(--text-main)] leading-none italic tabular-nums" in:scale={{ delay: 650 }}>{stats.pending}</h4>
			</div>
		</div>
		<!-- Card 3 -->
		<div class="bg-[var(--bg-card)]/20 backdrop-blur-3xl border border-[var(--border-main)] rounded-[2rem] p-6 shadow-xl flex items-center gap-5 group hover:border-[var(--brand-primary)] transition-all" in:fly={{ y: 30, delay: 600, duration: 800 }}>
			<div class="p-4 bg-[var(--brand-primary)]/10 text-[var(--brand-primary)] rounded-2xl border border-[var(--border-primary)]/20 group-hover:scale-110 transition-transform shadow-inner">
				<DatabaseOutline size="md" />
			</div>
			<div>
				<p class="text-[9px] font-black text-[var(--text-subtle)] uppercase tracking-widest opacity-50 mb-0.5">Total Elections</p>
				<h4 class="text-3xl font-black text-[var(--text-main)] leading-none italic tabular-nums" in:scale={{ delay: 800 }}>{stats.total}</h4>
			</div>
		</div>
	</div>
		<!-- Active Elections Stream -->
		<div class="flex items-center gap-6 mb-12">
			<h2 class="text-3xl font-black text-[var(--text-main)] tracking-tighter uppercase italic">Active <span class="text-[var(--brand-primary)]">Elections</span></h2>
			<div class="flex-1 h-[2px] bg-gradient-to-r from-[var(--border-main)] to-transparent"></div>
		</div>

		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 mb-32">
			{#if activeElections.length === 0}
				<div class="col-span-full py-24 text-center border-2 border-dashed border-[var(--border-main)] rounded-[3.5rem] bg-[var(--bg-card)]/20" in:fade>
					<div class="w-20 h-20 bg-[var(--bg-elevated)] rounded-full flex items-center justify-center mx-auto mb-6 opacity-30">
						<GridOutline size="xl" />
					</div>
					<p class="text-[var(--text-subtle)] font-black text-xs uppercase tracking-[0.3em] opacity-40">No active elections found.</p>
				</div>
			{:else}
				{#each activeElections as election, idx}
					<div class="group relative" in:fly={{ y: 30, delay: 300 + (idx * 100), duration: 800 }}>
						<div class="absolute -inset-1 bg-gradient-to-br from-[var(--brand-primary)] to-indigo-600 rounded-[2.5rem] opacity-0 group-hover:opacity-10 blur-xl transition-opacity duration-500"></div>
						
						<div class="relative bg-[var(--bg-card)]/20 backdrop-blur-3xl border border-[var(--border-main)] rounded-[2.5rem] overflow-hidden shadow-2xl transition-all duration-500 group-hover:-translate-y-2 group-hover:border-[var(--brand-primary)]/50 flex flex-col h-full">
							<!-- Header: High-Tech Blue -->
							<div class="p-8 bg-gradient-to-br from-[var(--brand-primary)] to-indigo-700 text-white relative overflow-hidden">
								<div class="absolute inset-0 opacity-[0.05] bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]"></div>
								<div class="absolute -top-6 -right-6 p-4 opacity-10 rotate-12 group-hover:rotate-0 transition-transform duration-1000">
									<GridOutline size="xl" />
								</div>
								
								<div class="relative z-10">
									{#if election.has_voted}
										<div class="flex items-center gap-2 mb-3">
											<div class="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.5)]"></div>
											<span class="text-[8px] font-black text-emerald-400 uppercase tracking-widest">Vote Cast</span>
										</div>
									{/if}
									<h3 class="text-2xl font-black tracking-tighter uppercase leading-tight italic line-clamp-2">{election.name}</h3>
								</div>
							</div>

							<!-- Body -->
							<div class="p-6 flex flex-col flex-1 gap-6">
								<div class="flex items-center gap-2">
									<ClockOutline size="xs" class="text-amber-600" />
									<span class="text-[10px] font-black uppercase tracking-tight text-amber-600">{getDaysLeft(election.end_date)}</span>
								</div>

								<div class="flex items-center justify-between pt-4 mt-auto">
									{#if election.has_voted}
										<button class="text-[var(--brand-primary)] font-black text-[10px] uppercase tracking-widest flex items-center gap-2 hover:scale-105 transition-all p-0 bg-transparent border-none cursor-pointer" onclick={() => toggleReceipt(election.id)}>
											<FileSearchOutline size="xs" /> Receipt
										</button>
									{:else if election.is_unanimous}
										<div class="flex items-center gap-2">
											<InfoCircleOutline size="xs" class="text-amber-600" />
											<span class="text-[9px] font-black text-amber-600 uppercase tracking-widest">Unanimous</span>
										</div>
									{:else}
										<Button color="primary" class="px-6 py-2.5 rounded-xl font-black text-[10px] uppercase tracking-widest shadow-xl shadow-blue-500/20 hover:scale-105 transition-all flex items-center gap-2" href="/student/ballot?election={election.id}">
											Vote <ArrowRightOutline size="xs" />
										</Button>
									{/if}
									<button class="text-[var(--text-subtle)] hover:text-[var(--text-main)] font-black text-[10px] uppercase tracking-widest flex items-center gap-2 p-0 transition-colors bg-transparent border-none cursor-pointer" onclick={() => goto(`/student/results?election=${election.id}`)}>
										Results <ChartPieOutline size="xs" />
									</button>
								</div>
							</div>

							<!-- Expanded Receipt -->
							{#if selectedSummaryId === election.id}
								<div class="p-8 bg-[var(--bg-elevated)]/50 border-t border-[var(--border-subtle)]" in:slide>
									{#if receiptLoading}
										<div class="flex items-center justify-center py-8 gap-4 opacity-40">
											<Spinner size="4" color="blue" />
											<span class="text-[9px] font-black uppercase tracking-[0.2em]">Loading...</span>
										</div>
									{:else if receiptData}
										<div class="space-y-6">
											<div class="bg-[var(--bg-card)] p-5 rounded-2xl border border-[var(--border-subtle)] shadow-inner">
												<p class="text-[8px] font-black uppercase tracking-widest text-[var(--text-muted)] mb-2 opacity-50">Receipt ID</p>
												<code class="text-[9px] font-mono text-[var(--brand-primary)] break-all leading-tight">{receiptData.receipt_id}</code>
											</div>
											<div class="flex justify-center">
												<Button size="xs" color="alternative" class="rounded-xl font-black text-[9px] uppercase tracking-widest gap-2" onclick={() => window.print()}>
													<ClipboardCheckOutline size="xs" /> Generate Print Record
												</Button>
											</div>
										</div>
									{/if}
								</div>
							{/if}
						</div>
					</div>
				{/each}
			{/if}
		</div>

		<!-- Upcoming Elections -->
		{#if upcomingElections.length > 0}
			<div class="flex items-center gap-6 mb-12">
				<h2 class="text-2xl font-black text-[var(--text-subtle)] tracking-tighter uppercase italic opacity-40">Upcoming <span class="text-[var(--text-subtle)]">Elections</span></h2>
				<div class="flex-1 h-[1px] bg-[var(--border-main)] opacity-30"></div>
			</div>

			<div class="grid grid-cols-1 lg:grid-cols-2 gap-8 pb-32">
				{#each upcomingElections as election, idx}
					<div class="bg-[var(--bg-card)]/30 backdrop-blur-xl border border-[var(--border-main)] rounded-[3rem] p-10 opacity-60 grayscale-[0.4] hover:grayscale-0 hover:opacity-100 transition-all duration-700 group" in:fly={{ y: 30, delay: 800 + (idx * 150), duration: 1000 }}>
						<div class="flex items-start gap-8">
							<div class="w-20 h-20 rounded-[2rem] bg-[var(--bg-elevated)] border border-[var(--border-main)] flex items-center justify-center text-[var(--text-subtle)] group-hover:text-[var(--brand-primary)] group-hover:border-[var(--brand-primary)]/50 transition-all shadow-xl">
								<ClockOutline size="lg" />
							</div>
							<div class="flex-1 min-w-0">
								<h3 class="text-2xl font-black text-[var(--text-main)] truncate tracking-tighter uppercase italic mb-3">{election.name}</h3>
								<div class="flex items-center gap-4 text-[10px] font-black text-[var(--text-subtle)] uppercase tracking-widest">
									<div class="flex items-center gap-2 px-3 py-1 bg-[var(--bg-elevated)] rounded-lg">
										<CalendarMonthOutline size="xs" />
										{new Date(election.start_date || '').toLocaleDateString('en-US', { month: 'long', day: 'numeric' }).toUpperCase()}
									</div>
									<span class="opacity-30">•</span>
									<span>Pending Start</span>
								</div>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
</style>
