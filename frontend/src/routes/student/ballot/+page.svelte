<script>
	import { onMount, onDestroy } from 'svelte';
	import { goto, invalidateAll } from '$app/navigation';
	import { student as studentApi } from '$lib/api.js';
	import { voterSession } from '$lib/stores/session.js';
	import { branding } from '$lib/stores/branding.js';
	import { page } from '$app/state';
	import { fade, fly, scale, slide } from 'svelte/transition';
	import { sortPositions } from '$lib/constants.js';
	import { formatFullName, formatDepartment } from '$lib/utils.js';
	import Notification from '$lib/components/Notification.svelte';
	import {
		Button,
		Badge,
		Spinner,
		Label
	} from 'flowbite-svelte';
	import {
		ShieldCheckOutline,
		LockOutline,
		CheckCircleOutline,
		ChevronRightOutline,
		FingerprintOutline,
		ExclamationCircleOutline,
		UserOutline,
		ArrowLeftOutline,
		ChartPieOutline,
		DatabaseOutline,
		ShieldOutline,
		EyeOutline,
		EyeSlashOutline,
		InfoCircleOutline
	} from 'flowbite-svelte-icons';

	// State Management
	let isSubmitting = $state(false);
	let hasSubmitted = $state(false);
	let isLoading = $state(true); 
	let errorMessage = $state('');
	let showConfirm = $state(false);
	let alreadyVoted = $state(false);
	let electionId = $state('');
	let receiptId = $state('');

	// Auth State
	let isAuthorized = $state(false);
	let adviserPin = $state('');
	let passcodeId = $state('');
	let adviserId = $state('');
	let sessionPasscode = $state('');
	let isVerifyingPasscode = $state(false);
	let showPin = $state(false);

	// Data State
	/** @type {Record<string, any[]>} */
	let candidatesGrouped = $state({});
	/** @type {Record<string, string | null>} */
	let selectedVotes = $state({});
	let electionName = $state('');

	// Derived State
	let voterName = $derived($voterSession?.full_name || 'Voter');
	const positionOrder = $derived(sortPositions(Object.keys(candidatesGrouped)));
	const selectedCount = $derived(Object.values(selectedVotes).filter((v) => v).length);
	const totalPositions = $derived(positionOrder.length);
	const progress = $derived(totalPositions > 0 ? (selectedCount / totalPositions) * 100 : 0);
	const allSelected = $derived(selectedCount === totalPositions && totalPositions > 0);

	function selectCandidate(position, candidateId) {
		selectedVotes[position] = candidateId;
	}

	function getReviewList() {
		return positionOrder.filter((pos) => selectedVotes[pos]).map((pos) => ({
			position: pos,
			candidate: (candidatesGrouped[pos] || []).find((c) => c.id === selectedVotes[pos])
		})).filter((r) => r.candidate);
	}

	onMount(() => { 
		if (!$voterSession) goto('/student/validate'); 
	});

	$effect(() => {
		if (page.url.pathname !== '/student/ballot') return;
		const session = $voterSession;
		if (!session) return;
		
		const id = page.url.searchParams.get('election') || '';
		
		if (id !== electionId) {
			isAuthorized = false;
			hasSubmitted = false;
			showConfirm = false;
			alreadyVoted = false;
			errorMessage = '';
			adviserPin = '';
			passcodeId = '';
			adviserId = '';
			sessionPasscode = '';
			candidatesGrouped = {};
			selectedVotes = {};
		}

		electionId = id;
		if (!id) { 
			isLoading = false; 
			return; 
		}

		isLoading = true;
		errorMessage = '';
		const electionInfo = (session.elections || []).find((e) => e.id === id);
		electionName = electionInfo?.name || 'Election';

		if (electionInfo?.status === 'upcoming') {
			errorMessage = 'BALLOT_LOCKED: Election has not initiated.';
			isLoading = false; 
			return;
		}

		if (electionInfo?.has_voted) {
			alreadyVoted = true; 
			isLoading = false; 
			return;
		}

		studentApi.getCandidates(id).then((res) => {
			const data = res.data || [];
			const grouped = {};
			data.forEach((c) => {
				if (!grouped[c.position]) grouped[c.position] = [];
				grouped[c.position].push({
					id: c.id,
					name: c.students?.full_name || formatFullName(c.students),
					party: c.partylists?.name || 'Independent'
				});
			});
			candidatesGrouped = grouped;
			const initialVotes = {};
			Object.keys(grouped).forEach((pos) => { 
				initialVotes[pos] = null; 
			});
			selectedVotes = initialVotes;
		}).catch((err) => { 
			errorMessage = err.message || 'Unable to access candidate registry.'; 
		}).finally(() => { 
			isLoading = false; 
		});
	});

	async function verifyPasscode() {
		if (!adviserPin || adviserPin.length < 6) return;
		isVerifyingPasscode = true;
		errorMessage = '';
		try {
			const res = await studentApi.verifyPasscode(electionId, adviserPin);
			passcodeId = res.passcode_id;
			adviserId = res.adviser_id;
			isAuthorized = true;
		} catch (err) { 
			errorMessage = err.message || 'INVALID PIN'; 
		} finally { 
			isVerifyingPasscode = false; 
		}
	}

	async function submitVote() {
		if (isSubmitting || !allSelected || sessionPasscode.length < 8) return;
		
		const session = $voterSession;
		if (!session) return;
		
		isSubmitting = true; 
		errorMessage = '';
		
		const votes = Object.entries(selectedVotes)
			.filter(([_, id]) => id !== null)
			.map(([position, candidate_id]) => ({ candidate_id, position }));
		
		try {
			const resp = await studentApi.vote(
				session.student_id ?? '', 
				electionId, 
				passcodeId, 
				adviserId, 
				votes, 
				sessionPasscode.trim()
			);
			
			if (resp?.receipt_id) receiptId = resp.receipt_id;
			voterSession.markVoted(electionId);
			
			// Clear sensitive keys from memory immediately
			sessionPasscode = '';
			adviserPin = '';
			
			showConfirm = false; 
			hasSubmitted = true;
		} catch (err) { 
			errorMessage = err.message || 'Voting failure. Please retry.'; 
		} finally { 
			isSubmitting = false; 
		}
	}
</script>

<svelte:head><title>Secure Ballot | {$branding.appName}</title></svelte:head>

<div class="min-h-screen text-[var(--text-main)] p-6 md:p-8 relative flex flex-col font-sans">
	


	<!-- Main Interface -->
	<div class="relative z-10 flex-1 flex flex-col w-full max-w-full mx-auto px-4 md:px-12">
		
		<!-- Top Navigation Bar -->
		<nav class="flex items-center justify-between mb-8" in:fly={{ y: -20, duration: 1000 }}>
			<div class="flex items-center gap-8">
				<div>
					<h1 class="text-xl md:text-2xl font-black tracking-tighter uppercase italic flex items-center gap-3">
						Official <span style="color: var(--brand-primary);">Ballot</span>
					</h1>
				</div>
			</div>

			<div class="hidden md:flex items-center gap-6">
				<div class="text-right">
					<p class="text-[8px] font-black text-[var(--text-subtle)] uppercase tracking-[0.2em] mb-1">Status</p>
					<h2 class="text-[10px] font-black uppercase tracking-tight opacity-70">{electionName || 'Loading...'}</h2>
				</div>
				<div class="w-12 h-12 rounded-2xl bg-[var(--bg-card)] border border-[var(--border-main)] flex items-center justify-center text-[var(--brand-primary)] shadow-2xl">
					<ShieldCheckOutline size="md" />
				</div>
			</div>
		</nav>


		{#if isLoading}
			<div class="flex-1 flex flex-col items-center justify-center gap-10" in:fade>
				<div class="relative w-32 h-32">
					<div class="absolute inset-0 rounded-full border-4 animate-ping" style="border-color: var(--brand-primary-alpha-10);"></div>
					<div class="absolute inset-2 rounded-full border-4 border-r-transparent border-b-transparent border-l-transparent animate-spin" style="border-top-color: var(--brand-primary);"></div>
					<div class="absolute inset-0 flex items-center justify-center drop-shadow-[0_0_15px_rgba(var(--brand-primary-rgb),0.5)]" style="color: var(--brand-primary);">
						<DatabaseOutline size="xl" />
					</div>
				</div>
				<div class="text-center space-y-2">
					<h3 class="text-base font-black tracking-[0.3em] uppercase text-[var(--text-main)] italic">Loading</h3>
					<p class="text-[9px] font-bold text-[var(--text-muted)] uppercase tracking-[0.15em] max-w-xs leading-relaxed">
						Opening secure ballot access...
					</p>
				</div>
			</div>
		{:else if hasSubmitted || alreadyVoted}
			<div class="flex-1 flex items-center justify-center" in:scale={{ duration: 800, start: 0.95 }}>
				<Card size="xl" class="w-full max-w-xl bg-[var(--bg-card)]/40 backdrop-blur-3xl border border-[var(--border-main)] p-16 rounded-[4rem] text-center shadow-2xl relative overflow-hidden border-t-8 border-t-emerald-500">
					<div class="absolute -top-24 -right-24 w-64 h-64 bg-emerald-500/10 rounded-full blur-3xl"></div>
					
					<div class="w-32 h-32 rounded-[3rem] bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-500 mx-auto mb-12 shadow-2xl relative group">
						<CheckCircleOutline size="xl" class="group-hover:scale-110 transition-transform" />
						<div class="absolute inset-0 bg-emerald-500/20 rounded-[3rem] blur-2xl animate-pulse"></div>
					</div>
					
					<h2 class="text-4xl font-black tracking-tighter uppercase mb-4 italic leading-none">VOTE CAST</h2>
					<p class="text-xs font-bold text-[var(--text-muted)] leading-relaxed uppercase tracking-widest mb-10 px-6 opacity-60">
						Your vote has been recorded successfully.
					</p>

					<div class="bg-[var(--bg-elevated)]/50 rounded-[2rem] p-8 border border-[var(--border-subtle)] mb-12 text-left group hover:border-emerald-500/30 transition-colors">
						<div class="flex items-center justify-between mb-4">
							<div class="flex items-center gap-3">
								<ShieldOutline size="xs" class="text-emerald-500" />
								<span class="text-[9px] font-black text-[var(--text-subtle)] uppercase tracking-widest">Receipt ID</span>
							</div>
							<Badge color="emerald" class="bg-emerald-500/10 text-emerald-500 border-none text-[8px] font-black">Official</Badge>
						</div>
						<code class="text-[11px] font-mono text-[var(--text-main)] break-all opacity-80 leading-relaxed">
							{receiptId || "NODES_SYNCHRONIZING_HASH_..._44x92"}
						</code>
					</div>

					<div class="grid grid-cols-2 gap-6">
						<Button color="alternative" class="py-6 rounded-3xl font-black text-[11px] tracking-widest uppercase bg-[var(--bg-elevated)] border border-[var(--border-main)] text-[var(--text-main)] hover:bg-[var(--bg-hover)] transition-all shadow-xl" onclick={async () => { await goto('/student'); await invalidateAll(); }}>
							Dashboard
						</Button>
						<Button color="primary" class="py-6 rounded-3xl font-black text-[11px] tracking-widest uppercase shadow-2xl" style="background: var(--brand-gradient); box-shadow: 0 10px 30px -10px var(--brand-glow);" onclick={async () => { await goto(`/student/results?election=${electionId}`); await invalidateAll(); }}>
							Live Tally
						</Button>
					</div>
				</Card>
			</div>
		{:else if !isAuthorized}
			<div class="flex-1 flex flex-col items-center justify-center p-4 w-full" in:fade={{ duration: 800 }}>
				<div class="w-full max-w-6xl xl:max-w-[1400px] relative">
					<!-- Ambient Glow -->
					<div class="absolute -inset-10 bg-gradient-to-tr from-[var(--brand-primary)]/20 to-[var(--brand-secondary)]/20 blur-[100px] opacity-30 rounded-[4rem] animate-pulse"></div>
					
					<div class="w-full relative overflow-hidden bg-[var(--bg-card)]/40 backdrop-blur-3xl border-2 border-[var(--border-main)] rounded-[3.5rem] shadow-[0_40px_100px_-20px_rgba(0,0,0,0.5)] group">
						
						<div class="p-4 md:p-12">
							<!-- Header Section -->
							<div class="flex flex-col items-center text-center mb-4 md:mb-10">
								<div class="w-16 h-16 rounded-3xl bg-[var(--bg-elevated)]/60 border-2 border-[var(--border-main)] flex items-center justify-center mb-6 shadow-2xl group-hover:scale-110 transition-transform duration-700">
									<LockOutline size="lg" style="color: var(--brand-primary);" />
								</div>
								<h2 class="text-3xl md:text-4xl font-black tracking-tighter uppercase italic mb-3">
									Access <span style="color: var(--brand-primary);">Restricted</span>
								</h2>
								<div class="flex items-center gap-3 bg-[var(--brand-primary-alpha-5)] px-4 py-2 rounded-full border border-[var(--brand-primary-alpha-10)]">
									<div class="w-2 h-2 rounded-full animate-pulse" style="background-color: var(--brand-primary);"></div>
									<span class="text-[9px] font-black uppercase tracking-[0.2em]" style="color: var(--brand-primary);">Secured Session Active</span>
								</div>
							</div>

							<!-- PIN Input Section -->
							<div class="space-y-4 md:space-y-8">
								<div class="text-center">
									<p class="text-[9px] font-black text-[var(--text-subtle)] uppercase tracking-[0.3em] mb-4 md:mb-8 opacity-60">
										Enter the 6-digit biometric PIN from your proctor
									</p>
									
									<div class="flex justify-center items-center gap-1 sm:gap-2 md:gap-8 lg:gap-12 pin-grid">
										{#each Array(6) as _, i}
											<div class="relative group/pin">
												<input
													type={showPin ? 'text' : 'password'}
													maxlength="1"
													value={adviserPin[i] || ''}
													oninput={(e) => {
														const val = e.target.value.replace(/[^0-9]/g, '');
														if (val) {
															let pinArr = (adviserPin || '').split('');
															while (pinArr.length < 6) pinArr.push('');
															pinArr[i] = val;
															adviserPin = pinArr.join('');
															if (i < 5) e.target.closest('.pin-grid').querySelectorAll('input')[i + 1].focus();
														}
													}}
													onkeydown={(e) => {
														if (e.key === 'Backspace' && !adviserPin[i] && i > 0) {
															e.target.closest('.pin-grid').querySelectorAll('input')[i - 1].focus();
														} else if (e.key === 'Backspace') {
															let pinArr = (adviserPin || '').split('');
															while (pinArr.length < 6) pinArr.push('');
															pinArr[i] = '';
															adviserPin = pinArr.join('');
														}
													}}
													class="w-8 h-10 sm:w-12 sm:h-14 md:w-16 md:h-20 lg:w-20 lg:h-28 rounded-xl md:rounded-[2rem] border-2 border-[var(--border-main)] bg-[var(--bg-elevated)]/40 text-center font-black text-lg md:text-4xl focus:outline-none focus:border-[var(--brand-primary)] focus:ring-4 focus:ring-[var(--brand-primary-alpha-10)] transition-all duration-300 placeholder:opacity-10"
													placeholder="•"
												/>
												<div class="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-1 rounded-full transition-all duration-500 {adviserPin[i] ? 'bg-[var(--brand-primary)] w-8 shadow-[0_0_10px_var(--brand-primary)]' : 'bg-transparent'}"></div>
											</div>
										{/each}
									</div>
								</div>

								{#if errorMessage}
									<div class="rounded-2xl border-2 border-red-500/20 bg-red-500/5 p-4 text-center animate-shake" in:slide>
										<p class="text-[10px] font-black text-red-500 uppercase tracking-widest">{errorMessage}</p>
									</div>
								{/if}

								<div class="pt-4 flex flex-col gap-6">
									<Button
										color="blue"
										class="w-full rounded-2xl md:rounded-[1.75rem] py-4 md:py-6 font-black text-[10px] md:text-[11px] tracking-[0.2em] md:tracking-[0.3em] uppercase transition-all active:scale-[0.98] shadow-2xl relative overflow-hidden group/btn disabled:opacity-30"
										style="background: var(--brand-gradient); color: white; box-shadow: 0 20px 40px -10px var(--brand-glow);"
										disabled={isVerifyingPasscode || (adviserPin?.length || 0) < 6}
										onclick={verifyPasscode}
									>
										<div class="absolute inset-0 bg-white/20 translate-x-[-100%] group-hover/btn:translate-x-[100%] transition-transform duration-1000 skew-x-12"></div>
										<div class="relative z-10 flex items-center justify-center gap-4">
											{#if isVerifyingPasscode}
												<Spinner size="4" color="white" />
												<span>Authenticating...</span>
											{:else}
												<span>Enter Secure Ballot</span>
												<ShieldCheckOutline size="sm" />
											{/if}
										</div>
									</Button>

									<button 
										type="button" 
										class="text-[9px] font-black uppercase tracking-[0.2em] text-[var(--text-subtle)] hover:text-[var(--brand-primary)] transition-colors flex items-center justify-center gap-2"
										onclick={() => showPin = !showPin}
									>
										{#if showPin}
											<EyeSlashOutline size="xs" /> Hide Characters
										{:else}
											<EyeOutline size="xs" /> Reveal Characters
										{/if}
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		{:else}
			<!-- High-Fidelity Ballot Interface -->
			<div class="flex-1 flex flex-col pt-4">

				<!-- Ballot Instructions (Now Inside the Form) -->
				<div class="mb-12 p-8 bg-[var(--bg-card)]/40 backdrop-blur-3xl border-l-4 border-[var(--brand-primary)] rounded-r-[2rem] shadow-xl" in:fly={{ x: -30, delay: 200, duration: 1000 }}>
					<div class="flex items-start gap-6">
						<div class="w-12 h-12 rounded-full flex items-center justify-center" style="background-color: var(--brand-primary-alpha-10); color: var(--brand-primary);">
							<InfoCircleOutline size="sm" />
						</div>
						<div>
							<h3 class="text-sm font-black uppercase tracking-widest mb-2" style="color: var(--brand-primary);">Voting Instructions</h3>
							<ul class="text-[10px] font-bold text-[var(--text-subtle)] uppercase tracking-widest space-y-2 opacity-70">
								<li class="flex items-center gap-2"><div class="w-1 h-1 rounded-full bg-[var(--brand-primary)]"></div> Select exactly one candidate for each position.</li>
								<li class="flex items-center gap-2"><div class="w-1 h-1 rounded-full bg-[var(--brand-primary)]"></div> Review your selections in the final summary before submission.</li>
								<li class="flex items-center gap-2"><div class="w-1 h-1 rounded-full bg-[var(--brand-primary)]"></div> Once cast, your digital ballot is permanent and tamper-proof.</li>
							</ul>
						</div>
					</div>
				</div>
				
				<!-- Progress Dock -->
				<header class="flex flex-col md:flex-row items-center justify-between gap-6 md:gap-8 mb-10 md:mb-16 px-2 md:px-4" in:fly={{ y: 20, duration: 1000 }}>
					<div class="max-w-md text-center md:text-left">
						<h3 class="text-xl md:text-2xl font-black tracking-tighter uppercase italic mb-1">Ballot</h3>
						<p class="text-[9px] md:text-[10px] font-bold text-[var(--text-subtle)] uppercase tracking-[0.15em] opacity-60">Review candidates carefully. Your selection is permanent once cast.</p>
					</div>
					
					<div class="flex items-center gap-6 md:gap-8 bg-[var(--bg-card)]/40 backdrop-blur-3xl border border-[var(--border-main)] p-4 md:p-6 rounded-[2rem] md:rounded-[2.5rem] shadow-2xl">
						<div class="flex flex-col items-end">
							<span class="text-[8px] md:text-[9px] font-black uppercase tracking-widest mb-1" style="color: var(--brand-primary);">{selectedCount} / {totalPositions} Selected</span>
							<div class="flex gap-1">
								{#each Array(totalPositions) as _, i}
									<div class="w-2 md:w-2.5 h-1 rounded-full transition-all duration-500 {i < selectedCount ? 'bg-emerald-500' : 'bg-[var(--border-main)]'}"></div>
								{/each}
							</div>
						</div>
						<div class="w-10 h-10 md:w-12 md:h-12 rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-main)] flex items-center justify-center text-lg md:text-xl font-black text-[var(--text-main)] shadow-inner">
							{Math.round(progress)}<span class="text-[8px] opacity-30">%</span>
						</div>
					</div>
				</header>

				<!-- Candidates Stream -->
				<div class="space-y-16 md:space-y-24 pb-64">
					{#each positionOrder as position, idx}
						<section class="space-y-6 md:space-y-10 group/section" in:fly={{ y: 50, delay: idx * 150, duration: 1000 }}>
							<div class="flex items-center gap-4 md:gap-6">
								<div class="w-14 h-14 md:w-20 md:h-20 rounded-[1.5rem] md:rounded-[2rem] bg-[var(--bg-card)] border-2 border-[var(--border-main)] flex items-center justify-center font-black text-xl md:text-3xl text-[var(--brand-primary)] shadow-2xl transition-all group-hover/section:border-[var(--brand-primary)] group-hover/section:scale-105 duration-700">
									{String(idx + 1).padStart(2, '0')}
								</div>
								<div>
									<h4 class="text-xl md:text-2xl font-black tracking-tighter uppercase italic leading-none mb-1">{position}</h4>
									<div class="flex items-center gap-2">
										<div class="w-1 h-1 md:w-1.5 md:h-1.5 rounded-full bg-[var(--brand-primary)] animate-pulse"></div>
										<p class="text-[8px] md:text-[9px] font-black text-[var(--text-subtle)] uppercase tracking-[0.15em] opacity-60">Select one candidate</p>
									</div>
								</div>
							</div>

							<div class="grid grid-cols-2 gap-3 sm:gap-4 md:grid-cols-3 lg:grid-cols-4">
								{#each candidatesGrouped[position] as cand									<button
										class="relative flex flex-col items-center p-3 md:p-4 transition-all duration-300 border-2 cursor-pointer rounded-2xl md:rounded-3xl active:scale-95 text-center {selectedVotes[position] === cand.id ? 'border-[var(--brand-primary)] shadow-[0_0_15px_var(--brand-glow)]' : 'border-[var(--border-main)] hover:border-[var(--text-subtle)]'}"
										style={selectedVotes[position] === cand.id ? 'background-color: var(--brand-primary-alpha-5); backdrop-filter: blur(16px);' : 'background-color: var(--bg-card); opacity: 0.9; backdrop-filter: blur(16px);'}
										onclick={() => selectCandidate(position, cand.id)}
									>
										<!-- Avatar -->
										<div class="relative mb-2 md:mb-3 shrink-0">
											<div class="w-14 h-14 md:w-20 md:h-20 rounded-full border-2 overflow-hidden {selectedVotes[position] === cand.id ? 'border-[var(--brand-primary)]' : 'border-[var(--border-main)]'} bg-[var(--bg-elevated)] relative">
												<img
													src={studentApi.getCandidatePhotoUrl ? studentApi.getCandidatePhotoUrl(cand.id) : `/api/common/candidates/${cand.id}/photo`}
													alt={cand.name}
													class="w-full h-full object-cover {selectedVotes[position] === cand.id ? '' : 'grayscale-[0.4]'} transition-all duration-500"
													onerror={(e) => { e.currentTarget.style.display='none'; e.currentTarget.nextElementSibling.style.display='flex'; }}
												/>
												<div class="w-full h-full bg-[var(--brand-primary)]/10 items-center justify-center font-black text-xl text-[var(--brand-primary)]" style="display:none;">{cand.name[0]}</div>
											</div>
											{#if selectedVotes[position] === cand.id}
												<div class="absolute -top-1 -right-1 w-5 h-5 bg-[var(--brand-primary)] rounded-full flex items-center justify-center shadow-lg ring-2 ring-[var(--bg-card)]" in:scale>
													<CheckCircleOutline size="xs" class="text-white" />
												</div>
											{/if}
										</div>
										<span class="text-xs md:text-sm font-bold leading-tight mb-1 line-clamp-2 {selectedVotes[position] === cand.id ? 'text-[var(--brand-primary)]' : 'text-[var(--text-main)]'}">{cand.name}</span>
										<span class="text-[8px] md:text-[9px] uppercase tracking-wider text-[var(--text-subtle)] line-clamp-1">{cand.party}</span>
									</button>
								{/each}
							</div>
						</section>
					{/each}
				</div>

				<!-- Floating Progress Dock -->
				<div class="fixed bottom-20 md:bottom-6 left-3 right-3 max-w-xl md:max-w-3xl mx-auto z-50">
					<div class="flex items-center justify-between p-3 pl-4 bg-[var(--bg-card)]/90 backdrop-blur-2xl border border-[var(--border-main)] rounded-2xl shadow-2xl">
						<div class="flex flex-col flex-1 mr-3">
							<div class="flex justify-between items-center mb-1.5">
								<span class="text-[9px] font-black uppercase tracking-widest text-[var(--text-subtle)]">Progress</span>
								<span class="text-[9px] font-black" style="color: var(--brand-primary);">{selectedCount}/{totalPositions} Selected</span>
							</div>
							<div class="w-full h-1.5 bg-[var(--border-main)] rounded-full overflow-hidden">
								<div class="h-full transition-all duration-500 ease-out rounded-full" style="width: {progress}%; background: var(--brand-gradient); box-shadow: 0 0 10px var(--brand-glow);"></div>
							</div>
						</div>
						<Button
							color="blue"
							class="px-4 md:px-6 py-2.5 rounded-xl font-black text-[10px] tracking-[0.15em] uppercase transition-all active:scale-95 flex items-center gap-2 text-white disabled:opacity-30 disabled:grayscale shrink-0"
							style="background: var(--brand-gradient); box-shadow: 0 8px 20px -5px var(--brand-glow);"
							disabled={!allSelected}
							onclick={() => showConfirm = true}
						>
							Review <ShieldCheckOutline size="xs" />
						</Button>
					</div>
				</div>
			</div>
		{/if}
	</div>

	<!-- Secure Confirmation Overlay -->
	{#if showConfirm}
		<div class="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8 bg-[var(--bg-main)]/95 backdrop-blur-3xl animate-in fade-in duration-500">
			<div in:scale={{ duration: 600, start: 0.9 }} class="w-full max-w-2xl">
				<Card size="none" class="w-full bg-[var(--bg-card)]/50 border-2 border-[var(--border-main)] p-6 md:p-16 rounded-[2rem] md:rounded-[5rem] shadow-[0_100px_150px_-30px_rgba(0,0,0,0.7)] relative overflow-hidden group">
					
					<!-- Security Texture -->
					<div class="absolute inset-0 opacity-[0.03] pointer-events-none group-hover:opacity-[0.05] transition-opacity">
						<div class="grid grid-cols-10 gap-6 p-6">
							{#each Array(60) as _}
								<ShieldOutline size="xl" />
							{/each}
						</div>
					</div>

					<header class="text-center mb-10 md:mb-16 relative z-10">
						<div class="w-16 h-16 md:w-20 md:h-20 rounded-[1.5rem] md:rounded-[2rem] bg-[var(--brand-primary)]/10 border-2 border-[var(--brand-primary)]/20 flex items-center justify-center text-[var(--brand-primary)] mx-auto mb-4 md:mb-8 shadow-xl group-hover:rotate-12 transition-transform duration-1000">
							<ShieldCheckOutline size="md" />
						</div>
						<h2 class="text-2xl md:text-4xl font-black tracking-tighter uppercase mb-2 italic leading-none">Review</h2>
						<p class="text-[9px] md:text-[10px] font-bold text-[var(--text-subtle)] uppercase tracking-[0.15em] md:tracking-[0.2em] leading-relaxed max-w-md mx-auto opacity-60">
							Review your selected candidates and enter the session key to cast your vote.
						</p>
					</header>

					<div class="space-y-12 relative z-10">
						<!-- Summary Grid -->
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-80 overflow-y-auto p-8 bg-[var(--bg-elevated)]/40 rounded-[3.5rem] border-2 border-[var(--border-main)] shadow-inner custom-scrollbar">
							{#each getReviewList() as item}
								<div class="bg-[var(--bg-card)]/60 border border-[var(--border-subtle)] p-6 rounded-3xl flex flex-col gap-2 shadow-xl hover:border-[var(--brand-primary)]/40 transition-all hover:-translate-y-1 group/item">
									<span class="text-[9px] font-black text-[var(--brand-primary)] uppercase tracking-widest opacity-60">{item.position}</span>
									<span class="text-base font-black text-[var(--text-main)] uppercase line-clamp-1 italic tracking-tight">{item.candidate.name}</span>
								</div>
							{/each}
						</div>

						<div class="space-y-6 pt-6 border-t border-[var(--border-main)]">
							<div class="flex items-center justify-between mb-1">
								<Label class="text-[10px] font-black text-[var(--text-subtle)] uppercase tracking-[0.2em]">Session Key</Label>
								<div class="flex gap-2">
									{#each Array(8) as _, i}
										<div class="w-2.5 h-2.5 rounded-full {sessionPasscode.length > i ? 'bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]' : 'bg-[var(--border-main)]'} transition-all duration-300"></div>
									{/each}
								</div>
							</div>
							<input 
								type="text" 
								maxlength="8" 
								bind:value={sessionPasscode} 
								placeholder="SESSION_KEY" 
								class="w-full bg-[var(--bg-elevated)]/60 border-2 border-[var(--border-main)] text-[var(--text-main)] rounded-[1.5rem] px-4 md:px-6 py-4 md:py-5 text-xl md:text-2xl font-black tracking-widest md:tracking-[0.4em] focus:border-[var(--brand-primary)] focus:ring-0 transition-all uppercase placeholder:opacity-5 text-center font-mono shadow-xl" 
							/>
						</div>

						<div class="grid grid-cols-2 gap-8 pt-6">
							<button class="py-6 text-[var(--text-subtle)] hover:text-[var(--text-main)] font-black text-[13px] tracking-[0.3em] uppercase transition-all hover:scale-105" onclick={() => showConfirm = false}>
								Abort
							</button>
							<Button 
								color="primary" 
								class="py-4 rounded-[1.5rem] font-black text-[12px] tracking-[0.2em] uppercase shadow-xl bg-white text-black hover:bg-emerald-500 hover:text-white transition-all flex items-center justify-center gap-3 relative overflow-hidden group/btn border-b-6 border-gray-200 hover:border-emerald-700" 
								disabled={isSubmitting || sessionPasscode.length < 8} 
								onclick={submitVote}
							>
								{#if isSubmitting}
									<Spinner size="3" color="current" /> Processing...
								{:else}
									Cast <FingerprintOutline size="xs" class="group-hover/btn:scale-125 transition-transform duration-500" />
								{/if}
							</Button>
						</div>
					</div>
				</Card>
			</div>
		</div>
	{/if}
</div>

<Notification text={errorMessage} type="error" />

<style>
	:global(body) {
		background-color: var(--bg-main);
		font-family: 'Inter', sans-serif;
	}

	:global(.custom-scrollbar::-webkit-scrollbar) {
		width: 8px;
	}
	:global(.custom-scrollbar::-webkit-scrollbar-track) {
		background: transparent;
	}
	:global(.custom-scrollbar::-webkit-scrollbar-thumb) {
		background: var(--border-main);
		border-radius: 20px;
	}
	:global(.custom-scrollbar::-webkit-scrollbar-thumb:hover) {
		background: var(--brand-primary);
	}

	@keyframes shimmer {
		0% { transform: translateX(-100%); }
		100% { transform: translateX(100%); }
	}
	.animate-shimmer {
		animation: shimmer 2s infinite;
	}

	@keyframes shake {
		0%, 100% { transform: translateX(0); }
		20%, 60% { transform: translateX(-5px); }
		40%, 80% { transform: translateX(5px); }
	}
	.animate-shake {
		animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
	}
</style>
