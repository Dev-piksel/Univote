<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { superAdmin as superAdminApi } from '$lib/api.js';
	import { branding } from '$lib/stores/branding.js';
	import { toggleTheme } from '$lib/stores/theme.js';
	import { fade, fly } from 'svelte/transition';
	import {
		Card,
		Button,
		Spinner,
		Alert,
		Badge
	} from 'flowbite-svelte';
	import {
		ShieldCheckOutline,
		UserOutline,
		LockOutline,
		EyeOutline,
		EyeSlashOutline,
		CheckCircleOutline,
		ExclamationCircleOutline,
		ChevronRightOutline,
		InfoCircleOutline
	} from 'flowbite-svelte-icons';

	let idNumber = $state('');
	let firstName = $state('');
	let lastName = $state('');
	let middleInitial = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let showPassword = $state(false);
	let isSubmitting = $state(false);
	let errorMsg = $state('');
	let successMsg = $state('');
	let alreadyConfigured = $state(false);
	let isChecking = $state(true);

	onMount(async () => {
		try {
			const status = await superAdminApi.getSetupStatus();
			alreadyConfigured = status.configured;
		} catch {
			// If endpoint fails, allow setup attempt anyway
		} finally {
			isChecking = false;
		}
	});

	/** Password strength derived state */
	const strength = $derived((() => {
		if (!password) return { label: '', color: 'gray', width: '0%' };
		let score = 0;
		if (password.length >= 8) score++;
		if (password.length >= 12) score++;
		if (/[A-Z]/.test(password)) score++;
		if (/[0-9]/.test(password)) score++;
		if (/[^A-Za-z0-9]/.test(password)) score++;
		if (score <= 1) return { label: 'Weak', color: 'red', width: '20%' };
		if (score === 2) return { label: 'Fair', color: 'yellow', width: '40%' };
		if (score === 3) return { label: 'Good', color: 'blue', width: '65%' };
		return { label: 'Strong', color: 'green', width: '100%' };
	})());

	async function handleSetup(/** @type {SubmitEvent} */ e) {
		e.preventDefault();
		errorMsg = '';

		if (!firstName || !lastName) { errorMsg = 'First and last name are required.'; return; }
		if (password.length < 8) { errorMsg = 'Password must be at least 8 characters.'; return; }
		if (password !== confirmPassword) { errorMsg = 'Passwords do not match.'; return; }

		isSubmitting = true;
		try {
			const res = await superAdminApi.setup({
				id_number: idNumber,
				first_name: firstName,
				last_name: lastName,
				middle_initial: middleInitial || undefined,
				password
			});
			successMsg = res.message;
			setTimeout(() => { goto('/login'); }, 2500);
		} catch (/** @type {any} */ err) {
			errorMsg = err.message ?? 'Setup failed. Please try again.';
			if (err.message?.includes('already configured')) {
				alreadyConfigured = true;
			}
		} finally {
			isSubmitting = false;
		}
	}
</script>

<svelte:head><title>System Initialization | {$branding.appName}</title></svelte:head>

<div class="min-h-screen flex items-center justify-center bg-[#0a0f1e] p-6 relative overflow-hidden selection:bg-primary-500/30">
	<!-- Dynamic Mesh Background -->
	<div class="absolute inset-0 pointer-events-none overflow-hidden">
		<div class="absolute top-[-20%] left-[-10%] w-[70%] h-[70%] bg-primary-600/15 rounded-full blur-[140px] animate-pulse"></div>
		<div class="absolute bottom-[-20%] right-[-10%] w-[60%] h-[60%] bg-indigo-500/10 rounded-full blur-[120px] animate-pulse delay-1000"></div>
		<div class="absolute inset-0 bg-[linear-gradient(to_right,#ffffff03_1px,transparent_1px),linear-gradient(to_bottom,#ffffff03_1px,transparent_1px)] bg-[size:48px_48px] [mask-image:radial-gradient(ellipse_80%_80%_at_50%_20%,#000_60%,transparent_100%)]"></div>
	</div>

	<Card size="xl" class="w-full max-w-4xl bg-white/5 backdrop-blur-3xl border-white/10 shadow-2xl rounded-[2.5rem] overflow-hidden relative z-10 border flex flex-col md:flex-row min-h-[650px]">
		
		<!-- Left: Branding Panel -->
		<div class="md:w-1/3 bg-gradient-to-br from-primary-600/20 to-indigo-800/10 p-10 flex flex-col justify-between border-b md:border-b-0 md:border-r border-white/5">
			<div class="flex items-center gap-4">
				<button onclick={toggleTheme} class="bg-white/10 backdrop-blur-xl p-2 rounded-2xl border border-white/10 hover:border-white/20 transition-all duration-300">
					<img src={$branding.logoUrl || "/favicon.svg"} alt="Logo" class="w-10 h-10 object-contain rounded-lg shadow-2xl" />
				</button>
				<div class="flex flex-col">
					<span class="text-xl font-black text-white tracking-tighter leading-none">{$branding.appName.toUpperCase()}</span>
					<span class="text-[9px] font-black text-primary-400 uppercase tracking-[0.3em] mt-1">Core Architecture</span>
				</div>
			</div>

			<div class="my-12">
				<div class="w-16 h-16 rounded-2xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center text-primary-400 mb-6 shadow-2xl">
					<ShieldCheckOutline size="lg" />
				</div>
				<h2 class="text-3xl font-black text-white leading-none tracking-tighter mb-4">SYSTEM INITIALIZATION</h2>
				<p class="text-[10px] font-bold tracking-[0.2em] text-white/40 leading-relaxed uppercase">
					Establish the primary Super Administrator account to begin managing the election infrastructure.
				</p>
			</div>

			<div class="text-[9px] font-black text-white/20 tracking-[0.5em] uppercase">
				UNIVOTE SECURE CORE
			</div>
		</div>

		<!-- Right: Form Panel -->
		<div class="flex-1 p-8 md:p-12">
			{#if isChecking}
				<div class="h-full flex items-center justify-center">
					<Spinner color="blue" size="8" />
				</div>
			{:else if alreadyConfigured}
				<div class="h-full flex flex-col items-center justify-center text-center" in:fade>
					<div class="w-20 h-20 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-400 mb-6 border border-blue-500/20 shadow-2xl">
						<CheckCircleOutline size="xl" />
					</div>
					<h3 class="text-2xl font-black text-white tracking-tighter mb-4 uppercase">SETUP ALREADY COMPLETE</h3>
					<p class="text-sm text-white/40 max-w-sm mb-8 font-medium">A Super Admin account is already configured for this system.</p>
					<Button href="/login" class="px-8 py-3 rounded-xl font-black text-xs tracking-widest bg-white text-black hover:bg-primary-500 hover:text-indigo-950 transition-all uppercase">
						Go to Login
						<ChevronRightOutline size="sm" class="ml-2" />
					</Button>
				</div>
			{:else if successMsg}
				<div class="h-full flex flex-col items-center justify-center text-center" in:fade>
					<div class="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-400 mb-6 border border-emerald-500/20 shadow-2xl">
						<CheckCircleOutline size="xl" />
					</div>
					<h3 class="text-2xl font-black text-white tracking-tighter mb-4 uppercase">ACCOUNT CREATED</h3>
					<p class="text-sm text-white/40 max-w-sm mb-8 font-medium">{successMsg} Redirecting to login...</p>
					<Spinner color="green" size="6" />
				</div>
			{:else}
				<div in:fade>
					<header class="mb-8 flex items-center justify-between">
						<div>
							<h1 class="text-2xl font-black text-white tracking-tighter mb-1">SUPER ADMIN SETUP</h1>
							<p class="text-[9px] font-black text-white/30 uppercase tracking-widest">Permanent System Credential</p>
						</div>
						<Badge color="red" rounded class="bg-red-500/10 text-red-400 border border-red-500/20 flex items-center gap-2 px-3 py-1">
							<InfoCircleOutline size="xs" />
							<span class="text-[9px] font-black uppercase">One-Time Access</span>
						</Badge>
					</header>

					{#if errorMsg}
						<div in:fly={{ y: -10 }}>
							<Alert color="red" class="mb-8 rounded-2xl border-none bg-red-500/10 text-red-400 py-4">
								<ExclamationCircleOutline size="sm" />
								<span class="text-xs font-bold tracking-tight">{errorMsg}</span>
							</Alert>
						</div>
					{/if}

					<form onsubmit={handleSetup} class="space-y-4">
						<!-- Row 1: Admin ID + Last Name -->
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							<!-- Admin / Employee ID -->
							<div class="relative group">
								<div class="absolute -inset-px bg-primary-500/20 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-all duration-500 pointer-events-none"></div>
								<div class="relative bg-white/[0.04] border border-white/10 rounded-2xl overflow-hidden group-focus-within:border-primary-400 transition-all duration-300">
									<div class="absolute left-4 top-1/2 -translate-y-1/2 text-white/30 group-focus-within:text-primary-400 transition-colors z-10 pointer-events-none">
										<UserOutline size="sm" />
									</div>
									<input
										id="sa-id"
										type="text"
										bind:value={idNumber}
										required
										placeholder=" "
										class="peer w-full pl-10 pr-4 pt-6 pb-2 bg-transparent text-white placeholder-transparent outline-none font-semibold text-sm tracking-wide focus:ring-0"
									/>
									<label for="sa-id" class="absolute left-10 top-1/2 -translate-y-1/2 text-white/40 font-black text-[9px] uppercase tracking-[0.3em] pointer-events-none transition-all duration-300 peer-focus:-translate-y-[1.1rem] peer-focus:scale-90 peer-[:not(:placeholder-shown)]:-translate-y-[1.1rem] peer-[:not(:placeholder-shown)]:scale-90 origin-left">
										Admin / Employee ID
									</label>
								</div>
							</div>

							<!-- Last Name -->
							<div class="relative group">
								<div class="absolute -inset-px bg-primary-500/20 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-all duration-500 pointer-events-none"></div>
								<div class="relative bg-white/[0.04] border border-white/10 rounded-2xl overflow-hidden group-focus-within:border-primary-400 transition-all duration-300">
									<input
										id="sa-lastname"
										type="text"
										bind:value={lastName}
										required
										placeholder=" "
										class="peer w-full px-4 pt-6 pb-2 bg-transparent text-white placeholder-transparent outline-none font-semibold text-sm tracking-wide focus:ring-0"
									/>
									<label for="sa-lastname" class="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 font-black text-[9px] uppercase tracking-[0.3em] pointer-events-none transition-all duration-300 peer-focus:-translate-y-[1.1rem] peer-focus:scale-90 peer-[:not(:placeholder-shown)]:-translate-y-[1.1rem] peer-[:not(:placeholder-shown)]:scale-90 origin-left">
										Last Name
									</label>
								</div>
							</div>
						</div>

						<!-- Row 2: First Name + Middle Initial -->
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							<!-- First Name -->
							<div class="relative group">
								<div class="absolute -inset-px bg-primary-500/20 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-all duration-500 pointer-events-none"></div>
								<div class="relative bg-white/[0.04] border border-white/10 rounded-2xl overflow-hidden group-focus-within:border-primary-400 transition-all duration-300">
									<input
										id="sa-firstname"
										type="text"
										bind:value={firstName}
										required
										placeholder=" "
										class="peer w-full px-4 pt-6 pb-2 bg-transparent text-white placeholder-transparent outline-none font-semibold text-sm tracking-wide focus:ring-0"
									/>
									<label for="sa-firstname" class="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 font-black text-[9px] uppercase tracking-[0.3em] pointer-events-none transition-all duration-300 peer-focus:-translate-y-[1.1rem] peer-focus:scale-90 peer-[:not(:placeholder-shown)]:-translate-y-[1.1rem] peer-[:not(:placeholder-shown)]:scale-90 origin-left">
										First Name
									</label>
								</div>
							</div>

							<!-- Middle Initial -->
							<div class="relative group">
								<div class="absolute -inset-px bg-primary-500/20 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-all duration-500 pointer-events-none"></div>
								<div class="relative bg-white/[0.04] border border-white/10 rounded-2xl overflow-hidden group-focus-within:border-primary-400 transition-all duration-300">
									<input
										id="sa-mi"
										type="text"
										bind:value={middleInitial}
										placeholder=" "
										class="peer w-full px-4 pt-6 pb-2 bg-transparent text-white placeholder-transparent outline-none font-semibold text-sm tracking-wide focus:ring-0"
									/>
									<label for="sa-mi" class="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 font-black text-[9px] uppercase tracking-[0.3em] pointer-events-none transition-all duration-300 peer-focus:-translate-y-[1.1rem] peer-focus:scale-90 peer-[:not(:placeholder-shown)]:-translate-y-[1.1rem] peer-[:not(:placeholder-shown)]:scale-90 origin-left">
										Middle Initial (Opt)
									</label>
								</div>
							</div>
						</div>

						<!-- Row 3: Master Password + Confirm Password -->
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
							<!-- Master Password + strength -->
							<div class="space-y-2">
								<div class="relative group">
									<div class="absolute -inset-px bg-primary-500/20 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-all duration-500 pointer-events-none"></div>
									<div class="relative bg-white/[0.04] border border-white/10 rounded-2xl overflow-hidden group-focus-within:border-primary-400 transition-all duration-300">
										<div class="absolute left-4 top-1/2 -translate-y-1/2 text-white/30 group-focus-within:text-primary-400 transition-colors z-10 pointer-events-none">
											<LockOutline size="sm" />
										</div>
										<input
											id="sa-pw"
											type={showPassword ? 'text' : 'password'}
											bind:value={password}
											required
											placeholder=" "
											class="peer w-full pl-10 pr-10 pt-6 pb-2 bg-transparent text-white placeholder-transparent outline-none font-semibold text-sm tracking-wide focus:ring-0"
										/>
										<label for="sa-pw" class="absolute left-10 top-1/2 -translate-y-1/2 text-white/40 font-black text-[9px] uppercase tracking-[0.3em] pointer-events-none transition-all duration-300 peer-focus:-translate-y-[1.1rem] peer-focus:scale-90 peer-[:not(:placeholder-shown)]:-translate-y-[1.1rem] peer-[:not(:placeholder-shown)]:scale-90 origin-left">
											Master Password
										</label>
										<button
											type="button"
											onclick={() => (showPassword = !showPassword)}
											class="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 hover:text-white transition-colors z-10"
										>
											{#if showPassword}<EyeSlashOutline size="sm" />{:else}<EyeOutline size="sm" />{/if}
										</button>
									</div>
								</div>
								{#if password}
									<div class="h-1 w-full bg-white/5 rounded-full overflow-hidden">
										<div class="h-full transition-all duration-500 rounded-full" style="width: {strength.width}; background: {strength.color === 'red' ? '#ef4444' : strength.color === 'yellow' ? '#eab308' : strength.color === 'blue' ? '#3b82f6' : '#22c55e'};"></div>
									</div>
									<div class="flex justify-between items-center px-1">
										<span class="text-[8px] font-black uppercase tracking-widest text-white/20">Security Grade</span>
										<span class="text-[8px] font-black uppercase tracking-widest" style="color: {strength.color === 'red' ? '#ef4444' : strength.color === 'yellow' ? '#eab308' : strength.color === 'blue' ? '#3b82f6' : '#22c55e'};">{strength.label}</span>
									</div>
								{/if}
							</div>

							<!-- Confirm Password -->
							<div class="space-y-2">
								<div class="relative group">
									<div class="absolute -inset-px bg-primary-500/20 rounded-2xl blur-md opacity-0 group-focus-within:opacity-100 transition-all duration-500 pointer-events-none"></div>
									<div class="relative bg-white/[0.04] border border-white/10 rounded-2xl overflow-hidden group-focus-within:border-primary-400 transition-all duration-300" class:!border-red-500={confirmPassword && confirmPassword !== password}>
										<input
											id="sa-cpw"
											type="password"
											bind:value={confirmPassword}
											required
											placeholder=" "
											class="peer w-full px-4 pt-6 pb-2 bg-transparent text-white placeholder-transparent outline-none font-semibold text-sm tracking-wide focus:ring-0"
										/>
										<label for="sa-cpw" class="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 font-black text-[9px] uppercase tracking-[0.3em] pointer-events-none transition-all duration-300 peer-focus:-translate-y-[1.1rem] peer-focus:scale-90 peer-[:not(:placeholder-shown)]:-translate-y-[1.1rem] peer-[:not(:placeholder-shown)]:scale-90 origin-left">
											Confirm Master Password
										</label>
									</div>
								</div>
								{#if confirmPassword && confirmPassword !== password}
									<p class="text-[9px] font-black uppercase tracking-widest text-red-400 px-1">Passwords mismatch</p>
								{/if}
							</div>
						</div>

						<Button
							type="submit"
							disabled={isSubmitting || !!(confirmPassword && confirmPassword !== password)}
							class="w-full py-4 mt-2 rounded-2xl font-black text-xs tracking-[0.2em] uppercase bg-white text-black hover:bg-primary-500 hover:text-indigo-950 transition-all shadow-2xl active:scale-95 flex items-center justify-center gap-3"
						>
							{#if isSubmitting}
								<Spinner size="4" color="gray" />
								INITIALIZING CORE...
							{:else}
								ESTABLISH SUPER ADMIN
								<ChevronRightOutline size="sm" />
							{/if}
						</Button>
					</form>
				</div>
			{/if}
		</div>
	</Card>
</div>
