<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { student as studentApi } from '$lib/api.js';
	import { voterSession } from '$lib/stores/session.js';
	import { branding } from '$lib/stores/branding.js';
	import { page } from '$app/state';
	import { fade, fly, scale, slide } from 'svelte/transition';
	import { sortPositions, calculateWinners } from '$lib/constants.js';
	import { formatFullName, formatDepartment } from '$lib/utils.js';
	import Notification from '$lib/components/Notification.svelte';
	import {
		Button,
		Card,
		Badge,
		Spinner,
		Select
	} from 'flowbite-svelte';
	import {
		ChartPieOutline,
		RefreshOutline,
		AwardOutline,
		UserOutline,
		ShieldCheckOutline,
		LockOutline,
		CalendarMonthOutline,
		DatabaseOutline
	} from 'flowbite-svelte-icons';

	let isLoading = $state(true);
	/** @type {Record<string, Record<string, number>>} */
	let results = $state({});
	/** @type {any[]} */
	let candidates = $state([]);
	let electionId = $state('');
	let lastUpdated = $state('');
	let statusMessage = $state('');
	let isFinalized = $state(false);

	/** @type {any[]} */
	let availableElections = $state([]);

	const positions = $derived(sortPositions(Object.keys(results)));
	const winnersData = $derived(calculateWinners(results, candidates));

	onMount(() => {
		const session = $voterSession;
		if (!session) { goto('/student/validate'); return; }
		availableElections = session.elections || [];

		const urlId = page.url.searchParams.get('election');
		const defaultId = session.elections?.[0]?.id ?? '';
		const targetId = urlId || defaultId;

		if (targetId) loadResults(targetId);
		else isLoading = false;
	});

	async function loadResults(targetId) {
		if (!targetId) return;
		electionId = targetId;
		isLoading = true;
		try {
			const [resData, candData] = await Promise.all([
				studentApi.getResults(targetId),
				studentApi.getCandidates(targetId)
			]);
			const fetched = resData.data || {};
			isFinalized = fetched.status === 'completed';
			
			if (isFinalized) {
				results = fetched.tallies || fetched;
				statusMessage = fetched.message || '';
			} else {
				results = {};
				statusMessage = fetched.status === 'active' 
					? "REAL-TIME TALLY ENCRYPTED: Results are legally restricted until the official completion of the voting period."
					: "AWAITING INITIATION: The election has not yet started.";
			}
			
			candidates = candData.data || [];
			lastUpdated = new Date().toLocaleTimeString();
		} catch (err) { 
			console.error('Results fetch error:', err); 
		} finally { 
			isLoading = false; 
		}
	}

	function handleElectionChange(e) {
		const newId = e.target.value;
		if (!newId) return;
		loadResults(newId);
	}

	function getPositionResults(position) {
		const posVotes = results[position] || {};
		const entries = Object.entries(posVotes).map(([candId, count]) => {
			const c = candidates.find((can) => can.id === candId);
			return {
				id: candId,
				name: c?.students?.full_name || formatFullName(c?.students),
				party: c?.partylists?.name || 'Independent',
				logo: c?.partylists?.logo_url,
				photo: c?.photo_url || c?.students?.photo_url,
				votes: Number(count)
			};
		});
		entries.sort((a, b) => b.votes - a.votes);
		const totalVotes = entries.reduce((sum, e) => sum + e.votes, 0);
		return { entries, totalVotes };
	}
</script>

<svelte:head><title>Registry: Results | {$branding.appName}</title></svelte:head>

<div class="min-h-screen text-[var(--text-main)] p-4 md:p-8 relative flex flex-col">


	<!-- Page Header -->
	<header class="relative z-10 flex flex-col lg:flex-row items-center justify-between gap-6 mb-10" in:fly={{ y: -30, duration: 1000 }}>
		<div class="w-full lg:w-auto">
			<h1 class="text-3xl md:text-4xl font-black text-[var(--text-main)] tracking-tighter uppercase leading-none italic">
				Live <span style="color: var(--brand-primary);">Results</span>
			</h1>
		</div>

		<div class="flex flex-col md:flex-row items-center gap-3 w-full lg:w-auto relative z-20">
			<!-- Integrated Selection Control -->
			<div class="flex items-center gap-2 p-1 bg-[var(--bg-card)]/40 backdrop-blur-3xl border border-[var(--border-main)] rounded-2xl shadow-2xl w-full md:w-auto hover:border-[var(--brand-primary)]/50 transition-all duration-500 group/select">
				<div class="flex items-center gap-3 pl-4 pr-2">
					<CalendarMonthOutline size="xs" class="text-[var(--brand-primary)] group-hover/select:scale-110 transition-transform duration-500" />
					<div class="h-4 w-[1px] bg-[var(--border-main)]"></div>
				</div>
				<Select 
					bind:value={electionId} 
					onchange={handleElectionChange} 
					placeholder="SELECT ELECTION..."
					class="bg-transparent border-none text-[9px] font-black text-[var(--text-main)] uppercase tracking-[0.2em] focus:ring-0 w-full md:w-64 cursor-pointer p-2 rounded-xl hover:bg-[var(--brand-primary-alpha-5)] transition-all"
				>
					{#each availableElections as e}
						<option value={e.id} class="bg-white text-black font-black uppercase text-[10px] tracking-widest">{e.name.toUpperCase()}</option>
					{/each}
				</Select>
			</div>

			<!-- Premium Refresh Button -->
			<Button 
				color="alternative" 
				class="w-full md:w-auto group relative overflow-hidden text-white px-6 py-3 rounded-2xl transition-all duration-300 font-black text-[9px] tracking-[0.3em] uppercase flex items-center justify-center gap-3" 
				style="background: var(--brand-gradient); box-shadow: 0 10px 30px -10px var(--brand-glow); --hover-shadow: 0 15px 40px -10px var(--brand-glow);"
				onclick={() => { loadResults(electionId); }}
				disabled={isLoading}
			>
				<div class="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
				<RefreshOutline size="xs" class="transition-transform duration-700 group-hover:rotate-180 {isLoading ? 'animate-spin' : ''}" />
				<span>Refresh</span>
			</Button>
		</div>
	</header>

	<div class="relative z-10 w-full max-w-full mx-auto flex-1 flex flex-col">
		{#if isLoading}
			<div class="flex-1 flex flex-col items-center justify-center gap-10 py-40" in:fade>
				<div class="relative w-32 h-32">
					<div class="absolute inset-0 rounded-full border-4 animate-ping" style="border-color: var(--brand-primary-alpha-10);"></div>
					<div class="absolute inset-2 rounded-full border-4 border-r-transparent border-b-transparent border-l-transparent animate-spin" style="border-top-color: var(--brand-primary);"></div>
					<div class="absolute inset-0 flex items-center justify-center" style="color: var(--brand-primary);">
						<DatabaseOutline size="xl" />
					</div>
				</div>
				<div class="text-center space-y-3">
					<h3 class="text-lg font-black tracking-[0.5em] uppercase text-[var(--text-main)] italic">Loading Results</h3>
					<p class="text-[10px] font-bold text-[var(--text-subtle)] uppercase tracking-[0.2em] max-w-xs leading-relaxed">
						Fetching election data from server...
					</p>
				</div>
			</div>
		{:else if positions.length > 0}
			<!-- Premium Results Grid -->
			<div class="grid grid-cols-1 lg:grid-cols-2 2xl:grid-cols-3 gap-10 pb-32">
				{#each positions as position, idx}
					{@const { entries, totalVotes } = getPositionResults(position)}
					{@const positionWinners = winnersData[position] || []}
					
					<div in:fly={{ y: 30, delay: idx * 100, duration: 800 }}>
						<div class="relative group h-full">
							<!-- Animated Border Glow -->
							<div class="absolute -inset-0.5 rounded-[2.5rem] opacity-0 group-hover:opacity-10 blur-xl transition-opacity duration-700" style="background: var(--brand-gradient);"></div>
							
							<div class="relative h-full bg-[var(--bg-card)]/20 backdrop-blur-3xl border border-[var(--border-main)] rounded-[2rem] md:rounded-[2.5rem] p-4 md:p-10 overflow-hidden transition-all duration-700 shadow-2xl hover:shadow-[0_30px_80px_-20px_rgba(0,0,0,0.4)] flex flex-col">
								
								<div class="absolute top-0 right-0 p-6 md:p-10 opacity-[0.03] group-hover:opacity-[0.08] transition-all group-hover:scale-110">
									<ChartPieOutline size="xl" />
								</div>

								<header class="flex items-center justify-between mb-6 md:mb-12 relative z-10">
									<div class="flex items-center gap-4 md:gap-6">
										<div class="w-10 h-10 md:w-14 md:h-14 rounded-xl md:rounded-2xl bg-[var(--bg-card)]/50 border-2 border-[var(--border-main)] flex items-center justify-center font-black text-lg md:text-xl group-hover:border-[var(--brand-primary)] transition-all shadow-xl" style="color: var(--brand-primary);">
											{String(idx + 1).padStart(2, '0')}
										</div>
										<div>
											<h3 class="text-lg md:text-2xl font-black tracking-tighter uppercase text-[var(--text-main)] italic">{position}</h3>
											<div class="flex items-center gap-3 mt-0.5 md:mt-1">
												<span class="text-[8px] md:text-[10px] font-black uppercase tracking-widest" style="color: var(--brand-primary);">{totalVotes} TOTAL VOTES</span>
											</div>
										</div>
									</div>
									{#if entries.length === 1}
										<Badge color="amber" class="bg-amber-500/10 text-amber-600 border border-amber-500/20 font-black px-2 md:px-4 py-0.5 md:py-1 uppercase tracking-widest text-[8px] md:text-[9px] rounded-lg">Unopposed</Badge>
									{/if}
								</header>

								<div class="space-y-6 md:space-y-12 relative z-10 flex-1">
									{#each entries as cand}
										{@const pct = totalVotes > 0 ? (cand.votes / totalVotes) * 100 : 0}
										{@const isWinner = positionWinners.some(w => w.id === cand.id)}
										
										<div class="space-y-3 md:space-y-4 group/cand">
											<div class="flex items-center justify-between gap-2 md:gap-6">
												<div class="flex-1 flex items-center gap-2 md:gap-4 min-w-0">
													<div class="relative shrink-0">
														<div class="w-8 h-8 md:w-12 md:h-12 rounded-lg md:rounded-2xl bg-[var(--bg-card)]/50 border-2 border-[var(--border-main)] p-0.5 group-hover/cand:scale-110 group-hover/cand:border-[var(--brand-primary)] transition-all duration-500 shadow-2xl relative overflow-hidden">
															{#if cand.photo}
																<img 
																	src={cand.photo} 
																	alt={cand.name} 
																	class="w-full h-full object-cover rounded-lg md:rounded-xl {isWinner ? '' : 'grayscale-[0.3] group-hover/cand:grayscale-0'}" 
																/>
															{:else}
														<div class="w-full h-full rounded-lg md:rounded-xl flex items-center justify-center font-black text-xl md:text-2xl" style="background-color: var(--brand-primary-alpha-10); color: var(--brand-primary);">
																	<UserOutline size="sm" />
																</div>
															{/if}
														</div>
														{#if isWinner}
															<div class="absolute -top-1 -right-1 md:-top-2 md:-right-2 w-5 h-5 md:w-7 md:h-7 rounded-md md:rounded-lg text-white flex items-center justify-center shadow-xl ring-2 ring-[var(--bg-card)]" style="background: var(--brand-gradient);" in:scale>
																<AwardOutline size="xs" />
															</div>
														{/if}
													</div>
													<div class="min-w-0">
														<h4 class="text-xs md:text-base font-black text-[var(--text-main)] tracking-tight uppercase truncate transition-all" style={isWinner ? `color: var(--brand-primary);` : `opacity: 0.7;`}>{cand.name}</h4>
														<p class="text-[8px] md:text-[9px] font-black text-[var(--text-subtle)] uppercase tracking-widest mt-0.5 opacity-50 truncate">{cand.party}</p>
													</div>
												</div>
												
												<div class="flex flex-col items-end gap-1 shrink-0">
													<span class="text-lg md:text-2xl font-black tabular-nums leading-none" style={isWinner ? `color: var(--brand-primary);` : `color: var(--text-main);`}>{cand.votes}</span>
													<span class="text-[7px] md:text-[9px] font-black text-[var(--text-subtle)] uppercase tracking-widest opacity-40">{Math.round(pct)}% SHARE</span>
												</div>
											</div>

											<div class="relative h-2.5 bg-[var(--bg-elevated)]/30 rounded-full overflow-hidden border border-[var(--border-main)] group-hover/cand:border-[var(--brand-primary)]/30 transition-colors">
												<div 
													class="absolute top-0 left-0 h-full transition-all duration-1000 ease-out" 
													style="width: {pct}%; background: {isWinner ? 'var(--brand-gradient)' : 'var(--text-muted)'}; opacity: {isWinner ? '1' : '0.2'}; box-shadow: {isWinner ? '0 0 15px -3px var(--brand-glow)' : 'none'};"
												></div>
												{#if isWinner}
													<div class="absolute inset-0 bg-white/20 animate-pulse pointer-events-none"></div>
												{/if}
											</div>
										</div>
									{/each}
								</div>

							</div>
						</div>
					</div>
				{/each}
			</div>
		{:else if electionId && (positions.length === 0 || statusMessage)}
			<div class="flex-1 flex items-start justify-center pt-4" in:scale>
				<Card size="xl" class="w-full max-w-2xl bg-[var(--bg-card)]/20 backdrop-blur-3xl border-[var(--border-main)] p-16 rounded-[4rem] text-center shadow-2xl relative overflow-hidden border-t-4" style="border-top-color: var(--brand-primary);">
					<div class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[var(--brand-primary)] to-transparent opacity-50"></div>
					
					{#if statusMessage}
						<div class="w-24 h-24 rounded-[2.5rem] bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-500 mx-auto mb-10 shadow-2xl">
							<LockOutline size="lg" />
						</div>
						<h3 class="text-3xl font-black text-[var(--text-main)] uppercase tracking-tighter mb-4 italic">Registry Locked</h3>
						<p class="text-sm font-bold text-[var(--text-muted)] uppercase tracking-[0.2em] leading-relaxed max-w-lg mx-auto">{statusMessage}</p>
					{:else}
						<div class="w-24 h-24 rounded-[2.5rem] border flex items-center justify-center mx-auto mb-10 shadow-2xl" style="background-color: var(--brand-primary-alpha-10); border-color: var(--brand-primary-alpha-20); color: var(--brand-primary);">
							<ChartPieOutline size="lg" />
						</div>
						<h3 class="text-3xl font-black text-[var(--text-main)] uppercase tracking-tighter mb-4 italic">Awaiting Registry Input</h3>
						<p class="text-sm font-bold text-[var(--text-muted)] uppercase tracking-[0.2em] leading-relaxed max-w-lg mx-auto">The synchronization process is active, but the institutional registry has not yet released the tally payload.</p>
					{/if}
				</Card>
			</div>
		{:else}
			<div class="flex-1 flex flex-col items-center justify-center gap-8 py-32" in:fade>
				<div class="w-24 h-24 rounded-[2.5rem] bg-[var(--bg-card)]/20 border border-[var(--border-main)] flex items-center justify-center text-[var(--text-muted)] opacity-20 shadow-inner">
					<DatabaseOutline size="xl" />
				</div>
				<div class="text-center space-y-3">
					<h3 class="text-2xl font-black text-[var(--text-main)] uppercase tracking-tighter italic">Initialize Monitoring</h3>
					<p class="text-[10px] font-bold text-[var(--text-subtle)] uppercase tracking-widest leading-relaxed max-w-xs mx-auto">Select an active election context from the control panel to engage live monitoring of the institutional registry.</p>
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	:global(body) {
		background-color: var(--bg-main);
	}
</style>
