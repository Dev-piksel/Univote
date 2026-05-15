<script>
	import { onMount } from 'svelte';
	import { authSession } from '$lib/stores/auth.js';
	import { branding } from '$lib/stores/branding.js';
	import { adviser as adviserApi } from '$lib/api.js';
	import {
		Card,
		Button,
		FloatingLabelInput,
		Spinner,
		Avatar,
		Badge
	} from 'flowbite-svelte';
	import {
		UserOutline,
		LockOutline,
		ShieldCheckOutline,
		CameraPhotoOutline,
		CheckCircleOutline,
		ExclamationCircleOutline
	} from 'flowbite-svelte-icons';
	import Notification from '$lib/components/Notification.svelte';

	let session = $authSession;
	let initials = $derived(
		(session?.full_name || '?')
			.split(' ')
			.slice(0, 2)
			.map((w) => w[0]?.toUpperCase())
			.join('')
	);

	let notification = $state({ text: '', type: 'info' });
	let passwords = $state({ current: '', new: '', confirm: '' });
	let isChanging = $state(false);

	onMount(async () => {
		try {
			const data = await adviserApi.getMe();
			// Sync store with latest server data (includes department_name)
			authSession.update(s => ({ ...s, ...data }));
			session = $authSession;
		} catch (err) {
			console.error('Failed to sync profile:', err);
		}
	});

	async function handleChangePassword(e) {
		e.preventDefault();
		if (passwords.new !== passwords.confirm) return notify('Passwords do not match', 'error');
		
		isChanging = true;
		try {
			await adviserApi.changePassword({
				current_password: passwords.current,
				new_password: passwords.new
			});
			notify('Password updated successfully', 'success');
			passwords = { current: '', new: '', confirm: '' };
		} catch (err) {
			notify(err.message || 'Failed to change password', 'error');
		} finally {
			isChanging = false;
		}
	}

	function notify(text, type = 'info') {
		notification = { text, type };
		setTimeout(() => (notification = { text: '', type: 'info' }), 3000);
	}
</script>

<svelte:head><title>My Profile | {$branding.appName}</title></svelte:head>

<div class="dash space-y-8 animate-in fade-in duration-700">
	<header class="flex justify-between items-end">
		<div>
			<p class="text-[10px] font-black text-indigo-900/50 dark:text-white/30 uppercase tracking-[0.3em] mb-1">
				Management / <span class="text-primary-400">Account Control</span>
			</p>
			<h1 class="text-3xl font-black text-indigo-950 dark:text-white tracking-tighter uppercase">PERSONAL PROFILE</h1>
		</div>
		<Badge color="blue" rounded class="px-4 py-1.5 bg-primary-500/10 text-primary-400 border border-primary-500/20 shadow-xl">
			<ShieldCheckOutline size="xs" class="mr-2" />
			<span class="text-[9px] font-black uppercase tracking-widest">Active Session</span>
		</Badge>
	</header>

	<div class="grid lg:grid-cols-[1fr_1.5fr] gap-8 items-start">
		<!-- Profile Identity Card -->
		<Card size="none" class="w-full max-w-full bg-indigo-50/50 dark:bg-white/5 backdrop-blur-3xl border-indigo-200 dark:border-white/10 p-10 rounded-[2rem] text-center border relative overflow-hidden">
			<div class="absolute top-0 right-0 p-4 opacity-10">
				<UserOutline size="xl" />
			</div>
			
			<div class="relative inline-block mx-auto mb-8">
				<div class="w-32 h-32 rounded-[2rem] bg-gradient-to-br from-primary-500 to-indigo-600 p-1 shadow-2xl">
					<div class="w-full h-full rounded-[1.8rem] bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:bg-none dark:bg-[#0a0f1e] flex items-center justify-center overflow-hidden border border-indigo-200 dark:border-white/10">
						{#if session?.photo_url}
							<img src={session.photo_url} alt={session.full_name} class="w-full h-full object-cover" />
						{:else}
							<span class="text-4xl font-black text-indigo-950 dark:text-white tracking-tighter">{initials}</span>
						{/if}
					</div>
				</div>
				<button class="absolute -bottom-2 -right-2 bg-white text-black p-2 rounded-xl shadow-2xl hover:scale-110 transition-transform active:scale-95 border border-indigo-300 dark:border-white/20">
					<CameraPhotoOutline size="xs" />
				</button>
			</div>

			<h2 class="text-2xl font-black text-indigo-950 dark:text-white tracking-tighter mb-2 uppercase">{session?.full_name}</h2>
			<p class="text-[10px] font-black text-primary-400 uppercase tracking-[0.4em] mb-8">{session?.role}</p>

			<div class="space-y-4 pt-8 border-t border-indigo-100 dark:border-white/5 text-left">
				<div class="flex flex-col gap-1">
					<span class="text-[9px] font-black text-indigo-900/40 dark:text-white/20 uppercase tracking-widest">Employee ID</span>
					<span class="text-sm font-bold text-indigo-950 dark:text-white tracking-tight">{session?.user_id}</span>
				</div>
				<div class="flex flex-col gap-1">
					<span class="text-[9px] font-black text-indigo-900/40 dark:text-white/20 uppercase tracking-widest">Program</span>
					<span class="text-sm font-bold text-indigo-950 dark:text-white tracking-tight">{session?.program || '—'}</span>
				</div>
				<div class="flex flex-col gap-1">
					<span class="text-[9px] font-black text-indigo-900/40 dark:text-white/20 uppercase tracking-widest">Departmental Link</span>
					<span class="text-sm font-bold text-indigo-950 dark:text-white tracking-tight">{session?.department_name || 'Assigned Department'}</span>
				</div>
			</div>
		</Card>

		<!-- Security Management -->
		<Card size="none" class="w-full max-w-full bg-indigo-50/50 dark:bg-white/5 backdrop-blur-3xl border-indigo-200 dark:border-white/10 p-10 rounded-[2rem] border overflow-hidden relative">
			<div class="absolute top-0 right-0 p-4 opacity-5">
				<LockOutline size="xl" />
			</div>
			
			<header class="mb-10">
				<h3 class="text-xl font-black text-indigo-950 dark:text-white tracking-tighter uppercase mb-1">SECURITY</h3>
				<p class="text-[10px] font-bold text-indigo-900/50 dark:text-white/30 uppercase tracking-widest">Update your access credentials</p>
			</header>

			<form onsubmit={handleChangePassword} class="space-y-8">
				<div class="relative group">
					<FloatingLabelInput id="input-current" type="text" style="filled" bind:value={passwords.current} required class="bg-indigo-50/50 dark:bg-white/5 border-none dark:text-white text-indigo-950 dark:text-white focus:border-primary-400">
						Current Password
					</FloatingLabelInput>
				</div>
				
				<div class="grid md:grid-cols-2 gap-8">
					<div class="relative group">
						<FloatingLabelInput id="input-new" type="text" style="filled" bind:value={passwords.new} required class="bg-indigo-50/50 dark:bg-white/5 border-none dark:text-white text-indigo-950 dark:text-white focus:border-primary-400">
							New Secure Password
						</FloatingLabelInput>
					</div>
					<div class="relative group">
						<FloatingLabelInput id="input-confirm" type="text" style="filled" bind:value={passwords.confirm} required class="bg-transparent {passwords.confirm && passwords.confirm !== passwords.new ? 'border-red-500' : 'border-indigo-200 dark:border-white/10'} text-indigo-950 dark:text-white focus:border-primary-400">
							Confirm New Password
						</FloatingLabelInput>
					</div>
				</div>

				<div class="pt-4">
					<Button type="submit" disabled={isChanging} class="w-full md:w-auto px-10 py-4 rounded-2xl font-black text-[10px] tracking-[0.25em] uppercase bg-white text-indigo-950 hover:bg-primary-500 hover:text-white dark:bg-primary-600 dark:text-white dark:hover:bg-primary-500 dark:border-none transition-all shadow-2xl flex items-center justify-center gap-3">
						{#if isChanging}
							<Spinner size="4" color="current" />
							SYNCING...
						{:else}
							UPDATE SECURITY GATE
							<CheckCircleOutline size="sm" />
						{/if}
					</Button>
				</div>
			</form>
		</Card>
	</div>
</div>

<Notification text={notification.text} type={notification.type} />
