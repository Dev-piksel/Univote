<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth as authApi, superAdmin as superAdminApi } from '$lib/api.js';
	import { authSession } from '$lib/stores/auth.js';
	import { theme, toggleTheme } from '$lib/stores/theme.js';
	import { branding } from '$lib/stores/branding.js';
	import { fade, fly } from 'svelte/transition';
	import {
		Label,
		FloatingLabelInput,
		Button,
		Spinner,
		Hr,
		Card
	} from 'flowbite-svelte';
	import {
		UserOutline,
		LockOutline,
		EyeOutline,
		EyeSlashOutline,
		ExclamationCircleOutline,
		CheckCircleOutline,
		GridOutline,
		ChartPieOutline,
		FileSearchOutline
	} from 'flowbite-svelte-icons';
	import Ripples from '$lib/components/Ripples.svelte';

	onMount(async () => {
		// Redirect to setup if no super admin exists yet
		try {
			const status = await superAdminApi.getSetupStatus();
			if (!status.configured) { goto('/super-admin/setup'); return; }
		} catch { /* unreachable backend – let login page render normally */ }

		// Redirect already-logged-in staff away from login
		if ($authSession) goto($authSession.role === 'dept_admin' || $authSession.role === 'super_admin' ? '/admin' : '/adviser');
	});

	let id = $state('');
	let password = $state('');
	let showPassword = $state(false);
	let isSubmitting = $state(false);
	let errorMessage = $state('');

	async function handleLogin(/** @type {SubmitEvent} */ e) {
		e.preventDefault();
		if (!id || !password) { errorMessage = 'Please enter both ID and password.'; return; }
		isSubmitting = true; errorMessage = '';
		try {
			const data = await authApi.login(id, password);
			authSession.login(data);
			goto(data.role === 'dept_admin' || data.role === 'super_admin' ? '/admin' : '/adviser');
		} catch (/** @type {any} */ err) {
			errorMessage = 'Staff credentials not recognized. Please check your ID and password.';
		} finally { isSubmitting = false; }
	}
</script>

<svelte:head><title>Sign In | {$branding.appName}</title></svelte:head>

<div class="min-h-screen flex items-center justify-center p-6 overflow-hidden relative transition-colors duration-700" style="background-color: {$branding.showBgAnims ? '#050a1b' : 'color-mix(in srgb, #050a1b 92%, white)'}">
	<!-- Decorative background elements (Global Ripples) -->
	<Ripples />

	<Card size="none" class="w-full max-w-5xl bg-white/[0.03] backdrop-blur-3xl border border-white/10 shadow-[0_40px_100px_-20px_rgba(0,0,0,0.8)] rounded-[2.5rem] overflow-hidden grid grid-cols-1 lg:grid-cols-[42%_1fr] min-h-[600px] relative z-10">
		
		<!-- Left: Brand Panel (Order 2 on mobile, 1 on desktop) -->
		<div class="bg-white/[0.02] backdrop-blur-2xl p-12 flex flex-col justify-between relative overflow-hidden group order-2 lg:order-1 border-r border-white/5">
			<!-- Subtle glow -->
			<div class="absolute top-10 right-[-20%] w-64 h-64 rounded-full blur-[80px] group-hover:scale-125 transition-transform duration-[2000ms] opacity-20" style="background-color: var(--brand-primary);"></div>
			<div class="absolute bottom-[-10%] left-[-10%] w-64 h-64 rounded-full blur-[80px] opacity-10" style="background-color: var(--brand-secondary);"></div>
			
			<div class="flex items-center gap-4 relative z-10">
				<div class="bg-white/5 backdrop-blur-2xl p-2 rounded-2xl border border-white/10 shadow-2xl">
					<img src={$branding.logoUrl || "/favicon.svg"} alt="{$branding.appName} Logo" class="w-10 h-10 object-contain rounded-lg" />
				</div>
				<div class="flex flex-col">
					<span class="text-xl font-black text-white tracking-tighter leading-none">{$branding.appName.toUpperCase()}</span>
					<span class="text-[9px] font-black uppercase tracking-[0.3em] mt-1" style="color: var(--brand-primary);">System</span>
				</div>
			</div>

			<div class="relative z-10">
				<h2 class="text-5xl font-black !text-white leading-[0.95] tracking-tighter mb-6">
					MANAGE<br />
					<span class="italic text-glow" style="color: var(--brand-primary);">ELECTIONS.</span>
				</h2>
				
				<p class="text-sm font-medium tracking-normal !text-white/80 leading-relaxed max-w-sm mb-12">
					Sign in to create elections, manage candidates, and monitor voting results in&nbsp;real&nbsp;time.
				</p>
				
				<div class="space-y-6 mt-16">
					<div class="flex items-center gap-5 text-xs font-bold text-white/70 tracking-widest cursor-help uppercase group/feat" title="Create and configure multiple elections with customized dates and positions.">
						<div class="w-10 h-10 rounded-full border flex items-center justify-center transition-all duration-500 group-hover/feat:scale-110 group-hover/feat:border-[var(--brand-primary)] group-hover/feat:shadow-[0_0_20px_var(--brand-glow)]" style="background-color: var(--brand-primary-alpha-10); border-color: var(--brand-primary-alpha-20); color: var(--brand-primary);">
							<GridOutline size="sm" />
						</div>
						<span class="group-hover/feat:text-white transition-colors">Create & manage elections</span>
					</div>
					<div class="flex items-center gap-5 text-xs font-bold text-white/70 tracking-widest cursor-help uppercase group/feat" title="Monitor voter turnout and live results with secure, encrypted data streams.">
						<div class="w-10 h-10 rounded-full border flex items-center justify-center transition-all duration-500 group-hover/feat:scale-110 group-hover/feat:border-[var(--brand-primary)] group-hover/feat:shadow-[0_0_20px_var(--brand-glow)]" style="background-color: var(--brand-primary-alpha-10); border-color: var(--brand-primary-alpha-20); color: var(--brand-primary);">
							<ChartPieOutline size="sm" />
						</div>
						<span class="group-hover/feat:text-white transition-colors">Track votes in real time</span>
					</div>
					<div class="flex items-center gap-5 text-xs font-bold text-white/70 tracking-widest cursor-help uppercase group/feat" title="Access comprehensive voting logs and generate verified election reports.">
						<div class="w-10 h-10 rounded-full border flex items-center justify-center transition-all duration-500 group-hover/feat:scale-110 group-hover/feat:border-[var(--brand-primary)] group-hover/feat:shadow-[0_0_20px_var(--brand-glow)]" style="background-color: var(--brand-primary-alpha-10); border-color: var(--brand-primary-alpha-20); color: var(--brand-primary);">
							<FileSearchOutline size="sm" />
						</div>
						<span class="group-hover/feat:text-white transition-colors">Full audit trail & reports</span>
					</div>
				</div>
			</div>

			<p class="text-[9px] font-black tracking-[0.4em] text-white/20 uppercase relative z-10">
				© 2025 {$branding.appName}
			</p>
		</div>

		<!-- Right: Form Panel (Order 1 on mobile, 2 on desktop) -->
		<div class="p-8 md:p-16 flex flex-col justify-center items-center lg:items-start bg-transparent relative order-1 lg:order-2 overflow-hidden">
			<!-- Animated background light -->
			<div class="absolute -top-20 -right-20 w-[400px] h-[400px] bg-[var(--brand-primary)]/10 rounded-full blur-[120px] pointer-events-none"></div>
			
			<div class="w-full max-w-sm relative z-10" in:fade={{ duration: 600 }}>
				<header class="mb-12 text-center lg:text-left">
					<div class="inline-flex items-center gap-3 px-4 py-1.5 rounded-full bg-white/5 border border-white/10 mb-8 shadow-xl">
						<LockOutline size="xs" class="animate-pulse" style="color: var(--brand-primary);" />
						<span class="text-[10px] font-black text-white/60 uppercase tracking-[0.2em]">Security</span>
					</div>
					<h1 class="text-5xl font-black !text-white tracking-tighter mb-2 italic">STAFF <span style="color: var(--brand-primary);">LOGIN</span></h1>
					<p class="text-[11px] font-bold text-white/40 uppercase tracking-[0.3em]">SECURE ACCESS GATEWAY</p>
				</header>

				<form onsubmit={handleLogin} class="space-y-8">
					<div class="relative group">
						<div class="absolute -inset-1 bg-[var(--brand-primary)]/20 rounded-2xl blur-lg opacity-0 group-focus-within:opacity-100 transition-all duration-700"></div>
						<div class="relative bg-white/[0.04] backdrop-blur-3xl border-2 border-white/20 rounded-2xl overflow-hidden group-focus-within:border-[var(--brand-primary)] group-focus-within:bg-white/[0.06] transition-all duration-500 shadow-[inset_0_2px_10px_rgba(255,255,255,0.02)]">
							<div class="absolute left-5 top-1/2 -translate-y-1/2 text-white/40 group-focus-within:text-[var(--brand-primary)] transition-colors z-20 pointer-events-none group-focus-within:scale-110 duration-500">
								<UserOutline size="sm" />
							</div>
							<input
								id="auth-id"
								type="text"
								name="username"
								bind:value={id}
								required
								placeholder=" "
								class="peer w-full pl-12 pr-6 py-5 bg-transparent text-white placeholder-transparent transition-all outline-none font-bold text-sm tracking-[0.1em] focus:ring-0"
							/>
							<label 
								for="auth-id"
								class="absolute left-12 z-30 top-1/2 -translate-y-1/2 text-white/40 font-black text-[9px] uppercase tracking-[0.4em] pointer-events-none transition-all duration-500 peer-focus:-translate-y-10 peer-focus:scale-90 peer-[:not(:placeholder-shown)]:-translate-y-10 peer-[:not(:placeholder-shown)]:scale-90 origin-left"
								style="color: var(--brand-primary);"
							>
								OFFICIAL STAFF ID
							</label>
						</div>
					</div>

					<div class="relative group">
						<div class="absolute -inset-1 bg-[var(--brand-primary)]/20 rounded-2xl blur-lg opacity-0 group-focus-within:opacity-100 transition-all duration-700"></div>
						<div class="relative bg-white/[0.04] backdrop-blur-3xl border-2 border-white/20 rounded-2xl overflow-hidden group-focus-within:border-[var(--brand-primary)] group-focus-within:bg-white/[0.06] transition-all duration-500 shadow-[inset_0_2px_10px_rgba(255,255,255,0.02)]">
							<div class="absolute left-5 top-1/2 -translate-y-1/2 text-white/40 group-focus-within:text-[var(--brand-primary)] transition-colors z-20 pointer-events-none group-focus-within:scale-110 duration-500">
								<LockOutline size="sm" />
							</div>
							<div class="relative">
								<input
									id="auth-password"
									type={showPassword ? 'text' : 'password'}
									name="password"
									bind:value={password}
									required
									placeholder=" "
									class="peer w-full pl-12 pr-12 py-5 bg-transparent text-white placeholder-transparent transition-all outline-none font-bold text-sm tracking-[0.1em] focus:ring-0"
								/>
								<label 
									for="auth-password"
									class="absolute left-12 z-30 top-1/2 -translate-y-1/2 text-white/40 font-black text-[9px] uppercase tracking-[0.4em] pointer-events-none transition-all duration-500 peer-focus:-translate-y-10 peer-focus:scale-90 peer-[:not(:placeholder-shown)]:-translate-y-10 peer-[:not(:placeholder-shown)]:scale-90 origin-left"
									style="color: var(--brand-primary);"
								>
									PASSWORD_KEY
								</label>
								<button
									type="button"
									onclick={() => (showPassword = !showPassword)}
									class="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-[var(--brand-primary)] transition-colors z-20"
									aria-label="Toggle password visibility"
								>
									{#if showPassword}
										<EyeSlashOutline size="sm" />
									{:else}
										<EyeOutline size="sm" />
									{/if}
								</button>
							</div>
						</div>
					</div>

					{#if errorMessage}
						<div in:fly={{ y: 5, duration: 400 }} class="relative">
							<div class="absolute inset-0 bg-red-500/20 blur-xl rounded-2xl"></div>
							<div class="relative rounded-2xl border border-red-500/20 bg-red-500/10 text-red-400 py-4 px-4 shadow-2xl overflow-hidden flex items-center gap-3">
								<div class="absolute left-0 top-0 w-1 h-full bg-red-500"></div>
								<ExclamationCircleOutline size="sm" class="animate-pulse flex-shrink-0" />
								<span class="text-[10px] font-black tracking-tight uppercase">{errorMessage}</span>
							</div>
						</div>
					{/if}

					<Button
						type="submit"
						color="alternative"
						disabled={isSubmitting}
						class="w-full py-5 rounded-[1.25rem] font-black text-[11px] tracking-[0.3em] uppercase active:scale-[0.98] group flex items-center justify-center gap-3 shadow-[0_15px_40px_-10px_var(--brand-glow)] border border-white/20 hover:border-[var(--brand-primary)] transition-all duration-300"
						style="background: var(--brand-gradient); border: 2px solid rgba(255,255,255,0.2);"
					>
						{#if isSubmitting}
							<Spinner size="4" color="white" />
							<span class="text-white drop-shadow-sm">Validating Access...</span>
						{:else}
							<span class="text-white drop-shadow-sm">SECURE SIGN IN</span>
							<CheckCircleOutline size="sm" class="text-white group-hover:scale-110 transition-transform duration-500" />
						{/if}
					</Button>
				</form>

				<footer class="mt-12 flex flex-col items-center lg:items-start gap-8 w-full relative">
					<a href="/" class="group/back text-[10px] font-black text-white/40 hover:text-white transition-all uppercase tracking-[0.3em] no-underline flex items-center gap-2 py-4 -ml-2 px-2 rounded-xl hover:bg-white/5 border border-transparent hover:border-white/10 shadow-2xl">
						<span class="group-hover/back:-translate-x-1 transition-transform duration-500">←</span>
						<span>Back to Public Portal</span>
					</a>
					
					<div class="flex items-center gap-4 opacity-10 hover:opacity-40 transition-all duration-700">
						<div class="w-1.5 h-1.5 rounded-full bg-white"></div>
						<a href="/super-admin/setup" class="text-[9px] font-black text-white uppercase tracking-[0.3em] no-underline">System Initialization</a>
					</div>
				</footer>
			</div>
		</div>
	</Card>
</div>
<style>
	@reference "../layout.css";

	@keyframes wave {
		0% { transform: translate(0, 0) scale(1); }
		33% { transform: translate(2%, 4%) scale(1.1); }
		66% { transform: translate(-2%, 2%) scale(0.9); }
		100% { transform: translate(0, 0) scale(1); }
	}


	
	.text-glow {
		text-shadow: 0 0 30px var(--brand-glow);
	}
</style>
