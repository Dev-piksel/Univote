<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { auth as authApi } from '$lib/api.js';
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
		Card,
		Badge
	} from 'flowbite-svelte';
	import {
		UserOutline,
		LockOutline,
		CheckCircleOutline,
		ExclamationCircleOutline,
		InfoCircleOutline
	} from 'flowbite-svelte-icons';

	onMount(() => { if ($authSession) goto($authSession.role === 'dept_admin' || $authSession.role === 'super_admin' ? '/admin' : '/adviser'); });

	let firstName = $state('');
	let lastName = $state('');
	let middleInitial = $state('');
	let id = $state('');
	let password = $state('');
	let role = $state(/** @type {'dept_admin' | 'adviser'} */ ('adviser'));
	let department = $state('');
	let isSubmitting = $state(false);
	let errorMessage = $state('');
	let successMessage = $state('');

	async function handleRegister(/** @type {SubmitEvent} */ e) {
		e.preventDefault();
		if (!id || !password || !firstName || !lastName) { errorMessage = 'Please fill out all required fields.'; return; }
		if (id.length < 3) { errorMessage = 'ID must be at least 3 characters.'; return; }
		if (password.length < 6) { errorMessage = 'Password must be at least 6 characters.'; return; }
		isSubmitting = true; errorMessage = ''; successMessage = '';
		try {
			const payload = {
				id, password,
				first_name: firstName,
				last_name: lastName,
				middle_initial: middleInitial || undefined,
				role,
				...(role === 'adviser' && department ? { department } : {})
			};
			const data = await authApi.register(payload);
			successMessage = data.message;
			setTimeout(() => { goto('/login'); }, 2000);
		} catch (/** @type {any} */ err) {
			errorMessage = err.message ?? 'Registration failed.';
		} finally { isSubmitting = false; }
	}
</script>

<svelte:head><title>Register | {$branding.appName} Staff Portal</title></svelte:head>

<div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900 p-6 overflow-hidden relative">
	<!-- Decorative background elements -->
	<div class="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-50/50 dark:bg-white/5 rounded-full blur-3xl animate-pulse"></div>
	<div class="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary-400/10 rounded-full blur-3xl animate-pulse delay-700"></div>

	<Card size="none" class="w-full max-w-5xl bg-white/95 dark:bg-gray-900/95 border-indigo-300 dark:border-white/20 shadow-2xl rounded-[2.5rem] overflow-hidden grid lg:grid-cols-[40%_1fr] min-h-[650px] relative z-10">
		
		<!-- Left: Brand Panel -->
		<div class="bg-gradient-to-br from-primary-600/90 to-primary-800/95 p-10 flex flex-col justify-between relative overflow-hidden group">
			<div class="absolute bottom-10 left-[-20%] w-64 h-64 bg-indigo-100/50 dark:bg-white/10 rounded-full blur-2xl group-hover:scale-110 transition-transform duration-1000"></div>
			
			<div class="flex items-center gap-4 relative z-10">
				<button onclick={toggleTheme} class="bg-white/20 backdrop-blur-xl p-2 rounded-2xl hover:scale-110 hover:bg-white/30 transition-all duration-300 shadow-lg">
					<img src={$branding.logoUrl || "/favicon.svg"} alt="{$branding.appName} Logo" class="w-10 h-10 object-contain rounded-lg" />
				</button>
				<span class="text-xl font-black text-indigo-950 dark:text-white tracking-widest uppercase">{$branding.appName}</span>
			</div>

			<div class="relative z-10">
				<h2 class="text-5xl font-black text-indigo-950 dark:text-white leading-[0.95] tracking-tighter mb-6">
					JOIN THE<br />
					<span class="text-indigo-900/60 dark:text-white/40 italic">TEAM.</span>
				</h2>
				<p class="text-[10px] font-bold tracking-[0.2em] text-indigo-900/80 dark:text-white/60 leading-relaxed max-w-xs mb-8 uppercase">
					Register as an Admin or Adviser to manage elections and oversee student voting.
				</p>
				
				<div class="space-y-4">
					{#each ['ADMIN & ADVISER ROLES', 'FULL ELECTION MANAGEMENT', 'LIVE RESULT MONITORING'] as feature}
						<div class="flex items-center gap-3 text-[10px] font-black text-white/80 tracking-widest">
							<div class="w-6 h-6 rounded-lg bg-white/20 flex items-center justify-center text-indigo-950 dark:text-white">
								<CheckCircleOutline size="xs" />
							</div>
							<span>{feature}</span>
						</div>
					{/each}
				</div>
			</div>

			<p class="text-[9px] font-black tracking-[0.4em] text-indigo-900/50 dark:text-white/30 uppercase relative z-10">
				© 2025 {$branding.appName}
			</p>
		</div>

		<!-- Right: Form Panel -->
		<div class="p-8 md:p-12 flex flex-col justify-center bg-white dark:bg-gray-900 relative overflow-y-auto">
			<div class="w-full max-w-xl mx-auto" in:fade={{ duration: 400 }}>
				<header class="mb-8">
					<h1 class="text-4xl font-black text-indigo-950 dark:text-white tracking-tighter mb-2 uppercase drop-shadow-[0_0_15px_rgba(255,255,255,0.1)]">STAFF REGISTRATION</h1>
					<p class="text-[11px] font-bold text-gray-400 dark:text-white/50 uppercase tracking-[0.3em]">ESTABLISH PERSONNEL CREDENTIALS</p>
				</header>

				<!-- Role Selection -->
				<div class="flex p-1 bg-gray-100 dark:bg-gray-800 rounded-2xl mb-8 gap-1">
					<button 
						type="button" 
						onclick={() => (role = 'adviser')} 
						class="flex-1 py-3 rounded-xl text-[10px] font-black tracking-widest uppercase transition-all {role === 'adviser' ? 'bg-white dark:bg-gray-700 text-primary-600 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}"
					>
						Adviser
					</button>
					<button 
						type="button" 
						onclick={() => (role = 'dept_admin')} 
						class="flex-1 py-3 rounded-xl text-[10px] font-black tracking-widest uppercase transition-all {role === 'dept_admin' ? 'bg-white dark:bg-gray-700 text-primary-600 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}"
					>
						Admin
					</button>
				</div>

				<form onsubmit={handleRegister} class="space-y-6">
					<div class="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-10">
						<div class="staff-input-wrap">
							<FloatingLabelInput id="firstName" style="outlined" bind:value={firstName} required class="py-4 bg-gray-50 border-gray-200 text-gray-900 dark:bg-white/5 dark:border-white/10 dark:text-white focus:border-primary-400 rounded-2xl">First Name</FloatingLabelInput>
						</div>
						<div class="staff-input-wrap">
							<FloatingLabelInput id="lastName" style="outlined" bind:value={lastName} required class="py-4 bg-gray-50 border-gray-200 text-gray-900 dark:bg-white/5 dark:border-white/10 dark:text-white focus:border-primary-400 rounded-2xl">Last Name</FloatingLabelInput>
						</div>
						<div class="staff-input-wrap">
							<FloatingLabelInput id="midInit" style="outlined" bind:value={middleInitial} class="py-4 bg-gray-50 border-gray-200 text-gray-900 dark:bg-white/5 dark:border-white/10 dark:text-white focus:border-primary-400 rounded-2xl">Middle Initial</FloatingLabelInput>
						</div>
						
						{#if role === 'adviser'}
							<div in:fly={{ y: -10, duration: 200 }} class="staff-input-wrap">
								<FloatingLabelInput id="department" style="outlined" bind:value={department} class="py-4 bg-gray-50 border-gray-200 text-gray-900 dark:bg-white/5 dark:border-white/10 dark:text-white focus:border-primary-400 rounded-2xl">Department</FloatingLabelInput>
							</div>
						{:else}
							<div class="flex items-center gap-3 p-4 bg-primary-50 dark:bg-primary-900/10 rounded-2xl text-primary-600 dark:text-primary-400 border border-primary-500/10" in:fly={{ y: -10, duration: 200 }}>
								<InfoCircleOutline size="sm" class="shrink-0" />
								<p class="text-[9px] font-bold leading-relaxed uppercase tracking-tight">
									Department assignment is managed by the Super Admin after creation.
								</p>
							</div>
						{/if}

						<div class="md:col-span-2 grid md:grid-cols-2 gap-10 pt-2">
							<div class="staff-input-wrap">
								<FloatingLabelInput id="regId" style="outlined" bind:value={id} required class="py-4 bg-gray-50 border-gray-200 text-gray-900 dark:bg-white/5 dark:border-white/10 dark:text-white focus:border-primary-400 rounded-2xl">Staff / Employee ID</FloatingLabelInput>
							</div>
							<div class="staff-input-wrap">
								<FloatingLabelInput id="regPassword" type="password" style="outlined" bind:value={password} required class="py-4 bg-gray-50 border-gray-200 text-gray-900 dark:bg-white/5 dark:border-white/10 dark:text-white focus:border-primary-400 rounded-2xl">Security Key (Password)</FloatingLabelInput>
							</div>
						</div>
					</div>

					{#if errorMessage}
						<div in:fly={{ y: 5, duration: 200 }}>
							<div class="rounded-2xl border border-red-200 bg-red-50 dark:bg-red-900/20 dark:border-red-800/40 py-4 px-4 flex items-center gap-3">
								<ExclamationCircleOutline size="sm" class="text-red-500 flex-shrink-0" />
								<span class="text-xs font-bold tracking-tight text-red-700 dark:text-red-400">{errorMessage}</span>
							</div>
						</div>
					{/if}

					{#if successMessage}
						<div in:fade>
							<div class="rounded-2xl border border-green-200 bg-green-50 dark:bg-green-900/20 dark:border-green-800/40 py-4 px-4 flex items-center gap-3">
								<CheckCircleOutline size="sm" class="text-green-500 flex-shrink-0" />
								<span class="text-xs font-bold tracking-tight text-green-700 dark:text-green-400">{successMessage}</span>
							</div>
						</div>
					{/if}

					<Button
						type="submit"
						disabled={isSubmitting || !!successMessage}
						class="w-full py-5 rounded-[1.25rem] font-black text-[11px] tracking-[0.3em] uppercase bg-gray-900 hover:bg-black dark:bg-white dark:text-black dark:hover:bg-primary-500 dark:hover:text-indigo-950 dark:text-white transition-all shadow-[0_15px_40px_-10px_rgba(0,0,0,0.15)] dark:shadow-[0_15px_40px_-10px_rgba(255,255,255,0.1)] active:scale-[0.98] group flex items-center justify-center gap-3"
					>
						{#if isSubmitting}
							<Spinner size="4" color="current" />
							ESTABLISHING NODE...
						{:else}
							REGISTER PERSONNEL
							<CheckCircleOutline size="sm" class="group-hover:scale-110 transition-transform" />
						{/if}
					</Button>
				</form>

				<Hr class="my-8" labelClass="bg-white dark:bg-gray-900 px-4 text-[10px] font-black tracking-[0.3em] text-gray-300 dark:text-gray-600 uppercase">OR</Hr>

				<a href="/login" class="block w-full py-4 rounded-2xl border-2 border-gray-100 dark:border-gray-800 text-center text-[10px] font-black tracking-[0.2em] text-indigo-950 dark:text-white uppercase hover:bg-gray-50 dark:hover:bg-gray-800 transition-all no-underline">
					Sign In Instead
				</a>

				<footer class="mt-8 text-center">
					<a href="/" class="text-[10px] font-black text-gray-400 hover:text-gray-900 dark:hover:text-indigo-950 dark:text-white transition-colors uppercase tracking-[0.1em] no-underline">Back to Home →</a>
				</footer>
			</div>
		</div>
	</Card>
</div>
<style>
	@reference "../layout.css";
	:global(.staff-input-wrap .flowbite-floating-label-input) {
		@apply transition-all duration-500 rounded-2xl px-6;
	}
	:global(.dark .staff-input-wrap .flowbite-floating-label-input) {
		@apply bg-indigo-50/50 dark:bg-white/5 border-indigo-200 dark:border-white/10 text-indigo-950 dark:text-white;
	}
	:global(.dark .staff-input-wrap .flowbite-floating-label-input:focus) {
		@apply border-primary-500 ring-4 ring-primary-500/20 scale-[1.02];
		box-shadow: 0 0 30px -10px rgba(59,130,246,0.5);
	}
	:global(.staff-input-wrap label) {
		@apply font-black tracking-widest uppercase text-[10px] left-6 text-gray-500;
	}
	:global(.dark .staff-input-wrap label) {
		@apply text-primary-400;
	}
</style>
