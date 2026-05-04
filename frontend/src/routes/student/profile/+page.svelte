<script>
	import { onMount } from 'svelte';
	import { voterSession } from '$lib/stores/session.js';
	import { branding } from '$lib/stores/branding.js';
	import { Card, Badge, Avatar, Button } from 'flowbite-svelte';
	import { 
		ShieldCheckOutline, 
		ProfileCardOutline, 
		EnvelopeOutline, 
		GraduationCapOutline, 
		BookOutline, 
		FingerprintOutline,
		InfoCircleOutline,
		DatabaseOutline,
		UserOutline,
		EditOutline
	} from 'flowbite-svelte-icons';
	import { fade, fly, scale } from 'svelte/transition';
	import { formatFullName, formatDepartment } from '$lib/utils.js';

	import * as api from '$lib/api.js';
	import { toast } from '$lib/stores/toast.js';

	let student = $state({ full_name: '', student_id: '', photo_url: '', email: '', program: '', year_level: '' });
	
	onMount(async () => {
		if ($voterSession) {
			try {
				const data = await api.student.getMe();
				// Reconstruct full name since DB returns individual parts
				const fullName = formatFullName(data);
				student = { ...data, full_name: fullName };
			} catch (e) {
				console.error('Failed to fetch profile:', e);
				// Fallback to session data if API fails
				student = { ...$voterSession };
			}
		}
	});

	let isUploading = $state(false);

	async function handlePhotoUpload(e) {
		const file = e.target.files[0];
		if (!file) return;

		if (file.size > 2 * 1024 * 1024) {
			alert('Image must be under 2MB');
			return;
		}

		isUploading = true;
		try {
			const reader = new FileReader();
			reader.onload = async (event) => {
				const base64 = /** @type {string} */ (event.target.result);
				await api.student.uploadProfilePhoto(base64);
				student.photo_url = base64;
				voterSession.update(s => ({ ...s, photo_url: base64 }));
				toast.success('Profile photo updated!');
			};
			reader.readAsDataURL(file);
		} catch (err) {
			console.error('Failed to upload photo:', err);
		} finally {
			isUploading = false;
		}
	}

	let initials = $derived(
		(student.full_name || '?')
			.split(' ')
			.slice(0, 2)
			.map((w) => w[0]?.toUpperCase())
			.join('')
	);

</script>

<svelte:head><title>My Voter Profile | {$branding.appName}</title></svelte:head>

<div class="min-h-screen text-content-main p-4 md:p-8 relative flex flex-col">



	<div class="relative z-10 pb-32">
		<!-- Unified Student Info Card -->
		<div class="max-w-5xl mx-auto" in:fly={{ y: 40, delay: 200, duration: 1000 }}>
			<div class="bg-[var(--bg-card)]/50 backdrop-blur-3xl border border-[var(--border-main)] rounded-[3rem] overflow-hidden shadow-2xl relative">
				
				<!-- Header Accent -->
				<div class="h-32 md:h-48 bg-gradient-to-br from-[var(--brand-primary)] to-indigo-700 relative">
					<div class="absolute inset-0 opacity-10 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]"></div>
					<div class="absolute top-8 right-10 text-white/20 hidden md:block">
						<ShieldCheckOutline size="xl" />
					</div>
					
					<!-- Floating Avatar -->
					<div class="absolute -bottom-12 md:-bottom-16 left-6 md:left-12 p-1.5 md:p-2 bg-[var(--bg-card)] rounded-[2rem] md:rounded-[2.5rem] shadow-2xl">
						<label class="cursor-pointer block relative group/photo">
							<input type="file" accept="image/*" onchange={handlePhotoUpload} hidden disabled={isUploading} />
							<div class="w-20 h-20 md:w-32 md:h-32 rounded-[1.25rem] md:rounded-[2rem] bg-[var(--bg-elevated)] border-2 md:border-4 border-[var(--bg-card)] overflow-hidden relative">
								{#if student.photo_url}
									<img src={student.photo_url} alt={student.full_name} class="w-full h-full object-cover transition-transform duration-700 group-hover/photo:scale-110" />
								{:else}
									<div class="w-full h-full bg-primary-500/10 flex items-center justify-center text-brand-primary font-black text-2xl md:text-4xl">{initials}</div>
								{/if}

								{#if isUploading}
									<div class="absolute inset-0 bg-black/40 flex items-center justify-center z-20">
										<div class="w-6 h-6 border-2 border-white/30 border-t-white animate-spin rounded-full"></div>
									</div>
								{/if}

								<div class="absolute inset-0 bg-black/20 opacity-0 group-hover/photo:opacity-100 transition-opacity flex items-center justify-center z-10">
									<EditOutline size="md" class="text-white" />
								</div>
							</div>
						</label>
					</div>
				</div>

				<div class="pt-16 md:pt-24 pb-8 md:pb-12 px-6 md:px-12">
					<div class="flex flex-col md:flex-row justify-between items-start gap-6 md:gap-8 mb-10 md:mb-16">
						<div>
							<h2 class="text-xl md:text-4xl font-black text-content-main tracking-tighter uppercase italic leading-tight mb-1 break-words">{student.full_name}</h2>
							<p class="text-[10px] md:text-[11px] font-black uppercase tracking-[0.4em] italic mb-2" style="color: var(--brand-primary);">{student.student_id}</p>
						</div>
						<div class="flex flex-col items-start md:items-end md:text-right">
							<p class="text-[9px] md:text-[10px] font-black text-content-subtle uppercase tracking-widest opacity-50 mb-1">Email Address</p>
							<p class="text-base md:text-lg font-black text-content-main tracking-tight italic break-all">{student.email || 'N/A'}</p>
						</div>
					</div>

					<div class="flex items-center gap-4 mb-8 md:mb-10 pt-8 md:pt-10 border-t border-[var(--border-subtle)]">
						<div class="w-1.5 h-6 md:w-2 md:h-8 bg-[var(--brand-primary)] rounded-full"></div>
						<h3 class="text-xl md:text-2xl font-black text-content-main tracking-tighter uppercase italic">Academic <span class="text-brand-primary">Details</span></h3>
					</div>

					<div class="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12">
						<div class="space-y-1 md:space-y-2">
							<div class="flex items-center gap-2 mb-2 md:mb-3">
								<BookOutline size="xs" class="text-brand-primary" />
								<p class="text-[9px] md:text-[10px] font-black uppercase tracking-[0.2em] text-content-subtle">Course</p>
							</div>
							<p class="text-lg md:text-2xl font-black text-content-main uppercase tracking-tight leading-tight">{formatDepartment(student.program || 'BSIT')}</p>
						</div>

						<div class="space-y-1 md:space-y-2">
							<div class="flex items-center gap-2 mb-2 md:mb-3">
								<UserOutline size="xs" class="text-brand-primary" />
								<p class="text-[9px] md:text-[10px] font-black uppercase tracking-[0.2em] text-content-subtle">Year Level</p>
							</div>
							<p class="text-3xl md:text-4xl font-black text-content-main uppercase tracking-tighter">{student.year_level || 'N/A'}<span class="text-sm md:text-base text-content-subtle ml-2">Year</span></p>
						</div>

						<div class="space-y-1 md:space-y-2">
							<div class="flex items-center gap-2 mb-2 md:mb-3">
								<ShieldCheckOutline size="xs" class="text-brand-primary" />
								<p class="text-[9px] md:text-[10px] font-black uppercase tracking-[0.2em] text-content-subtle">Status</p>
							</div>
							<p class="text-lg md:text-2xl font-black text-emerald-500 uppercase tracking-tight italic text-glow">Verified</p>
						</div>
					</div>
				</div>

				<div class="bg-[var(--bg-elevated)]/30 py-6 px-12 border-t border-[var(--border-subtle)] flex justify-between items-center">
					<span class="text-[9px] font-black uppercase tracking-[0.3em] opacity-30">UniVote Identity Service</span>
					<div class="flex gap-2">
						<div class="w-2 h-2 rounded-full bg-emerald-500"></div>
						<div class="w-2 h-2 rounded-full bg-emerald-500 opacity-50"></div>
						<div class="w-2 h-2 rounded-full bg-emerald-500 opacity-20"></div>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	:global(body) {
		background-color: var(--bg-main);
	}
</style>
