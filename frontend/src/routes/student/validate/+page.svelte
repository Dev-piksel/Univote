<script>
	import { goto } from '$app/navigation';
	import { student as studentApi } from '$lib/api.js';
	import { voterSession } from '$lib/stores/session.js';
	import { theme, toggleTheme } from '$lib/stores/theme.js';
	import { branding } from '$lib/stores/branding.js';
	import { fade, fly } from 'svelte/transition';
	import {
		Card,
		Button,
		FloatingLabelInput,
		Spinner,
		Alert,
		Badge
	} from 'flowbite-svelte';
	import {
		UserOutline,
		CheckCircleOutline,
		ExclamationCircleOutline,
		ChevronRightOutline,
		FingerprintOutline,
		ShieldCheckOutline,
		ChartPieOutline,
		ClockOutline
	} from 'flowbite-svelte-icons';
	import Ripples from '$lib/components/Ripples.svelte';

	let studentId = $state('');
	let isChecking = $state(false);
	let errorMessage = $state('');
	let retrySeconds = $state(0);

	async function checkStudentId(/** @type {SubmitEvent} */ e) {
		e.preventDefault();
		if (!studentId) { errorMessage = 'Please enter your Student ID.'; return; }
		isChecking = true;
		errorMessage = '';
		try {
			const data = await studentApi.validate(studentId);
			const elections = (data.active_elections || []).map(
				/** @param {any} e */ (e) => ({ id: e.id, name: e.name, has_voted: e.has_voted })
			);
			voterSession.login({ ...data.student, access_token: data.access_token, elections });
			goto('/student');
		} catch (/** @type {any} */ err) {
			if (err.retryAfter) {
				retrySeconds = err.retryAfter;
				errorMessage = `Too many attempts. Please wait ${retrySeconds}s.`;
			} else {
				errorMessage = 'ID not recognized. Please check your Student ID card and try again.';
			}
		} finally { isChecking = false; }
	}

	import { onMount, onDestroy } from 'svelte';
	/** @type {any} */ let timer;
	$effect(() => {
		if (retrySeconds > 0) {
			timer = setInterval(() => { retrySeconds -= 1; }, 1000);
			return () => clearInterval(timer);
		}
	});
</script>

<svelte:head>
	<title>Student Access | {$branding.appName}</title>
</svelte:head>

<div class="min-h-screen flex items-center justify-center p-6 relative selection:bg-primary-500/30 transition-colors duration-700" style="background-color: {$branding.showBgAnims ? '#050a1b' : 'color-mix(in srgb, #050a1b 92%, white)'}">
	<!-- Background layers (Global Ripples) -->
	<Ripples />
	<div class="absolute inset-0 pointer-events-none overflow-hidden">
		<div class="absolute inset-0 bg-[linear-gradient(to_right,#ffffff03_1px,transparent_1px),linear-gradient(to_bottom,#ffffff03_1px,transparent_1px)] bg-[size:48px_48px] [mask-image:radial-gradient(ellipse_80%_80%_at_50%_20%,#000_60%,transparent_100%)]"></div>
	</div>

	<Card size="none" class="w-full max-w-5xl bg-white/[0.03] backdrop-blur-3xl border border-white/10 shadow-[0_40px_100px_-20px_rgba(0,0,0,0.8)] rounded-[2.5rem] overflow-hidden grid grid-cols-1 lg:grid-cols-[42%_1fr] min-h-[600px] relative z-10">
		
		<!-- Left: Voter Panel (Order 2 on mobile, 1 on desktop) -->
		<div class="bg-white/[0.02] backdrop-blur-2xl p-12 flex flex-col justify-between relative overflow-hidden group border-r border-white/5 order-2 lg:order-1">
			<!-- Subtle glow -->
			<div class="absolute top-10 right-[-20%] w-64 h-64 rounded-full blur-[80px] group-hover:scale-125 transition-transform duration-[2000ms] opacity-20" style="background-color: var(--brand-primary);"></div>
			<div class="absolute bottom-[-10%] left-[-10%] w-64 h-64 rounded-full blur-[80px] opacity-10" style="background-color: var(--brand-secondary);"></div>
			
			<div class="flex items-center gap-4 relative z-10">
				<div class="bg-white/5 backdrop-blur-2xl p-2 rounded-2xl border border-white/10 shadow-2xl">
					<img src={$branding.logoUrl || "/favicon.svg"} alt="Logo" class="w-10 h-10 object-contain rounded-lg" />
				</div>
				<div class="flex flex-col">
					<span class="text-xl font-black text-white tracking-tighter leading-none">{$branding.appName.toUpperCase()}</span>
					<span class="text-[9px] font-black uppercase tracking-[0.3em] mt-1" style="color: var(--brand-primary);">Voter</span>
				</div>
			</div>

			<div class="relative z-10">
				<h2 class="text-5xl font-black !text-white leading-[0.95] tracking-tighter mb-6">
					YOUR VOTE,<br />
					<span class="italic text-glow" style="color: var(--brand-primary);">YOUR VOICE.</span>
				</h2>
				
				<p class="text-sm font-medium tracking-normal !text-white/80 leading-relaxed max-w-sm mb-12">
					Authenticate with your student ID to verify your identity and access the secure digital&nbsp;ballot.
				</p>
				
				<div class="space-y-6 mt-16">
					<div class="flex items-center gap-5 text-xs font-bold text-white/70 tracking-widest cursor-help uppercase group/feat" in:fly={{ x: -20, delay: 0 }} title="Your identity is never linked to your specific vote.">
						<div class="w-10 h-10 rounded-full border flex items-center justify-center transition-all duration-500 group-hover/feat:scale-110 group-hover/feat:border-[var(--brand-primary)] group-hover/feat:shadow-[0_0_20px_var(--brand-glow)]" style="background-color: var(--brand-primary-alpha-10); border-color: var(--brand-primary-alpha-20); color: var(--brand-primary);">
							<ShieldCheckOutline size="sm" />
						</div>
						<span class="group-hover/feat:text-white transition-colors">Anonymous balloting</span>
					</div>
					<div class="flex items-center gap-5 text-xs font-bold text-white/70 tracking-widest cursor-help uppercase group/feat" in:fly={{ x: -20, delay: 100 }} title="Each student is mathematically restricted to one unique submission.">
						<div class="w-10 h-10 rounded-full border flex items-center justify-center transition-all duration-500 group-hover/feat:scale-110 group-hover/feat:border-[var(--brand-primary)] group-hover/feat:shadow-[0_0_20px_var(--brand-glow)]" style="background-color: var(--brand-primary-alpha-10); border-color: var(--brand-primary-alpha-20); color: var(--brand-primary);">
							<UserOutline size="sm" />
						</div>
						<span class="group-hover/feat:text-white transition-colors">One student, one vote</span>
					</div>
					<div class="flex items-center gap-5 text-xs font-bold text-white/70 tracking-widest cursor-help uppercase group/feat" in:fly={{ x: -20, delay: 200 }} title="Verification happens in sub-seconds against the student database.">
						<div class="w-10 h-10 rounded-full border flex items-center justify-center transition-all duration-500 group-hover/feat:scale-110 group-hover/feat:border-[var(--brand-primary)] group-hover/feat:shadow-[0_0_20px_var(--brand-glow)]" style="background-color: var(--brand-primary-alpha-10); border-color: var(--brand-primary-alpha-20); color: var(--brand-primary);">
							<ClockOutline size="sm" />
						</div>
						<span class="group-hover/feat:text-white transition-colors">Instant verification</span>
					</div>
				</div>
			</div>

			<div class="h-4"></div>
		</div>

		<!-- Right: Validation Panel (Order 1 on mobile, 2 on desktop) -->
		<div class="p-8 md:p-16 flex flex-col justify-center items-center lg:items-start bg-transparent relative order-1 lg:order-2 overflow-hidden">
			<!-- Animated background light -->
			<div class="absolute -top-20 -right-20 w-[400px] h-[400px] bg-[var(--brand-primary)]/10 rounded-full blur-[120px] pointer-events-none"></div>
			
			<div class="w-full max-w-sm relative z-10" in:fade={{ duration: 600 }}>
				<header class="mb-12 text-center lg:text-left">

					<h1 class="text-5xl font-black !text-white tracking-tighter mb-2 italic">VOTER <span style="color: var(--brand-primary);">LOGIN</span></h1>
					<p class="text-[11px] font-bold text-white/40 uppercase tracking-[0.3em]">SECURE IDENTITY VERIFICATION</p>
				</header>

				<form onsubmit={checkStudentId} class="space-y-10">
					<div class="relative group">
						<!-- Input Ambient Glow -->
						<div class="absolute -inset-1 bg-[var(--brand-primary)]/20 rounded-2xl blur-lg opacity-0 group-focus-within:opacity-100 transition-all duration-700"></div>
						
						<div class="relative bg-white/[0.04] backdrop-blur-3xl border-2 border-white/20 rounded-2xl overflow-hidden group-focus-within:border-[var(--brand-primary)] group-focus-within:bg-white/[0.06] transition-all duration-500 shadow-[inset_0_2px_10px_rgba(255,255,255,0.02)]">
							
							<div class="absolute left-5 top-1/2 -translate-y-1/2 text-white/40 group-focus-within:text-[var(--brand-primary)] transition-colors z-20 pointer-events-none group-focus-within:scale-110 duration-500">
								<UserOutline size="md" />
							</div>
							
							<input
								id="student-id"
								type="text"
								name="studentId"
								bind:value={studentId}
								required
								placeholder=" "
								class="peer w-full pl-14 pr-6 py-6 bg-transparent text-white placeholder-transparent transition-all outline-none font-black text-lg tracking-[0.1em] focus:ring-0"
							/>
							
							<label 
								for="student-id"
								class="absolute left-14 top-1/2 -translate-y-1/2 font-black text-[10px] uppercase tracking-[0.4em] pointer-events-none transition-all duration-500 peer-focus:-translate-y-12 peer-focus:scale-75 peer-[:not(:placeholder-shown)]:-translate-y-12 peer-[:not(:placeholder-shown)]:scale-75 origin-left z-30 text-white/40 group-focus-within:!text-[var(--brand-primary)]"
							>
								VOTER_ID_IDENTITY
							</label>
						</div>
					</div>

					{#if errorMessage}
						<div in:fly={{ y: 5, duration: 400 }} class="relative">
							<div class="absolute inset-0 bg-red-500/20 blur-xl rounded-2xl"></div>
							<Alert color="red" class="relative rounded-2xl border border-red-500/20 bg-red-500/10 text-red-400 py-4 shadow-2xl overflow-hidden group">
								<div class="absolute left-0 top-0 w-1 h-full bg-red-500"></div>
								<ExclamationCircleOutline slot="icon" size="sm" class="animate-pulse" />
								<div class="flex items-center justify-between w-full">
									<span class="text-xs font-black tracking-tight uppercase">{errorMessage}</span>
									{#if retrySeconds > 0}
										<Badge color="red" class="ml-2 font-black bg-red-500 text-white border-none">{retrySeconds}S</Badge>
									{/if}
								</div>
							</Alert>
						</div>
					{/if}

					<Button
						type="submit"
						color="alternative"
						disabled={isChecking || !studentId || retrySeconds > 0}
						class="login-btn w-full py-5 rounded-[1.25rem] font-black text-[11px] tracking-[0.3em] uppercase active:scale-[0.98] group flex items-center justify-center gap-3 shadow-[0_15px_40px_-10px_var(--brand-glow)] border border-white/20 hover:border-[var(--brand-primary)] transition-all duration-300"
					>
						{#if isChecking}
							<Spinner size="4" color="white" />
							<span class="text-white drop-shadow-sm">Validating Access...</span>
						{:else}
							<span class="text-white drop-shadow-sm">Authenticate & Vote</span>
							<ChevronRightOutline size="sm" class="text-white group-hover:translate-x-1 transition-transform duration-500" />
						{/if}
					</Button>
				</form>

				<footer class="mt-16 flex flex-col items-center lg:items-start gap-8 w-full relative">
					<a href="/" class="group/back text-[10px] font-black text-white/40 hover:text-white transition-all uppercase tracking-[0.3em] no-underline flex items-center gap-2 py-4 -ml-2 px-2 rounded-xl hover:bg-white/5 border border-transparent hover:border-white/10 shadow-2xl">
						<ChevronRightOutline size="xs" class="rotate-180 group-hover/back:-translate-x-1 transition-transform duration-500" />
						<span>Back to Public Portal</span>
					</a>
					
					<div class="flex items-center gap-6 opacity-10 grayscale hover:grayscale-0 hover:opacity-40 transition-all duration-700">
						<ShieldCheckOutline size="sm" class="text-white" />
						<ChartPieOutline size="sm" class="text-white" />
						<ClockOutline size="sm" class="text-white" />
					</div>
				</footer>
			</div>
		</div>
	</Card>
</div>

<style>
	@reference "../../layout.css";
	/* Custom Floating Label logic handled by peer-focus utility */
	
	@keyframes wave {
		0% { transform: translate(0, 0) scale(1); }
		33% { transform: translate(2%, 4%) scale(1.1); }
		66% { transform: translate(-2%, 2%) scale(0.9); }
		100% { transform: translate(0, 0) scale(1); }
	}

	.login-btn {
		background: var(--brand-gradient) !important;
		color: white !important;
		box-shadow: 0 15px 40px -10px var(--brand-glow) !important;
		transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
		border: none !important;
		position: relative;
		overflow: hidden;
	}
	.login-btn::after {
		content: "";
		position: absolute;
		inset: 0;
		background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
		transform: translateX(-100%);
		transition: transform 0.6s ease;
	}
	.login-btn:hover:not(:disabled)::after {
		transform: translateX(100%);
	}
	.login-btn:hover:not(:disabled) {
		transform: translateY(-3px);
		box-shadow: 0 20px 50px -10px var(--brand-glow) !important;
	}
	.login-btn:active:not(:disabled) {
		transform: translateY(0) scale(0.98);
	}
</style>
