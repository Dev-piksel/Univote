<script>
	import { goto } from '$app/navigation';
	import { authSession } from '$lib/stores/auth.js';
	import { voterSession } from '$lib/stores/session.js';
	import { branding } from '$lib/stores/branding.js';
	import { page } from '$app/state';
	import { toggleTheme } from '$lib/stores/theme.js';
	import { fade } from 'svelte/transition';
	import { auth, student as studentApi } from '$lib/api.js';
	import { 
		Sidebar as FbSidebar, 
		SidebarGroup, 
		SidebarWrapper, 
		Avatar, 
		Badge, 
		Spinner,
		Tooltip
	} from 'flowbite-svelte';
	import {
		GridOutline,
		UsersGroupOutline,
		UserCircleOutline,
		ChartPieOutline,
		ClipboardListOutline,
		CogOutline,
		SunOutline,
		MoonOutline,
		ArrowRightToBracketOutline,
		ChevronLeftOutline,
		BuildingOutline,
		UserOutline,
		EnvelopeOutline,
		GraduationCapOutline
	} from 'flowbite-svelte-icons';

	/** @type {{ role: 'super_admin' | 'dept_admin' | 'adviser' | 'student', student_info?: any, sseStatus?: 'connected' | 'reconnecting' | 'error', children: import('svelte').Snippet }} */
	let { role, student_info, sseStatus = 'connected', children } = $props();

	let collapsed = $state(false);
	let mobileMenuOpen = $state(false);

	const links = {
		super_admin: [
			{ section: 'MANAGE' },
			{ name: 'Dashboard',   path: '/admin',            icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
			{ name: 'Departments',  path: '/admin/departments', icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4' },
			{ name: 'Dept Admins',  path: '/admin/dept-admins', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' },
			{ name: 'Voters',      path: '/admin/voters',     icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' },
			{ name: 'Results',     path: '/admin/results',    icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
			{ section: 'SYSTEM' },
			{ name: 'Audit Log',    path: '/admin/audit',      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4' },
			{ name: 'App Settings', path: '/admin/settings',   icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
			{ name: 'Switch Theme', action: 'toggleTheme',    icon: 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707m12.728 12.728L5.12 5.12' },
			{ section: 'ACCOUNT' },
			{ name: 'My Profile',   path: '/admin/profile',    icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' }
		],
		dept_admin: [
			{ section: 'MANAGE' },
			{ name: 'Dashboard', path: '/admin',           icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
			{ name: 'Elections', path: '/admin/elections', icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' },
			{ name: 'Voters',    path: '/admin/voters',    icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' },
			{ name: 'Advisers',  path: '/admin/advisers',  icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' },
			{ name: 'Results',   path: '/admin/results',   icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
			{ section: 'SYSTEM' },
			{ name: 'Switch Theme', action: 'toggleTheme', icon: 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707m12.728 12.728L5.12 5.12' },
			{ section: 'ACCOUNT' },
			{ name: 'My Profile', path: '/admin/profile',  icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' }
		],
		adviser: [
			{ section: 'MANAGE' },
			{ name: 'Dashboard',  path: '/adviser',             icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
			{ name: 'Candidates', path: '/adviser/candidates',  icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
			{ name: 'Partylists', path: '/adviser/partylists',  icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' },
			{ name: 'Results',    path: '/adviser/results',     icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
			{ section: 'SYSTEM' },
			{ name: 'Switch Theme', action: 'toggleTheme', icon: 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707m12.728 12.728L5.12 5.12' },
			{ section: 'ACCOUNT' },
			{ name: 'My Profile', path: '/adviser/profile',     icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' }
		],
		student: [
			{ section: 'STATIC' },
			{ name: 'Dashboard', path: '/student',         icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
			{ name: 'Cast Vote', path: '/student/ballot',  icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' },
			{ name: 'Results',   path: '/student/results', icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' },
			{ section: 'SYSTEM' },
			{ name: 'Switch Theme', action: 'toggleTheme', icon: 'M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707m12.728 12.728L5.12 5.12' },
			{ section: 'ACCOUNT' },
			{ name: 'My Profile', path: '/student/profile', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' }
		]
	};

	function handleLogout() {
		if (role === 'student') {
			voterSession.logout();
			goto('/student/validate');
		} else {
			authSession.logout();
			goto('/login');
		}
		mobileMenuOpen = false;
	}

	function handleNav() {
		mobileMenuOpen = false;
	}

	const navItems = $derived(links[/** @type {keyof typeof links} */ (role)] || []);
	const roleBadge = {
		super_admin: { label: 'Super Admin',  color: '#7c3aed' },
		dept_admin:  { label: 'Dept Admin',   color: '#0b75fe' },
		adviser:     { label: 'Adviser',      color: '#059669' },
		student:     { label: 'Student',      color: '#d97706' },
	};

	const initials = $derived(
		[
			(student_info?.first_name || student_info?.full_name || '?')[0],
			(student_info?.last_name || '')[0]
		].filter(Boolean).map(/** @type {(c:string)=>string} */ c => c.toUpperCase()).join('') || '?'
	);
	const sidebarWidth = $derived(collapsed ? '70px' : '260px');

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
				const base64 = event.target.result;
				if (role === 'student') {
					await studentApi.uploadProfilePhoto(base64);
					voterSession.update(s => ({ ...s, student: { ...s.student, photo_url: base64 } }));
				} else {
					await auth.updateProfile({ photo_url: base64 });
					authSession.update(s => ({ ...s, photo_url: base64 }));
				}
			};
			reader.readAsDataURL(file);
		} catch (err) {
			console.error('Failed to upload photo:', err);
		} finally {
			isUploading = false;
		}
	}
</script>

<!-- Mobile overlay -->
{#if mobileMenuOpen}
	<div
		onclick={() => (mobileMenuOpen = false)}
		onkeydown={(e) => e.key === 'Escape' && (mobileMenuOpen = false)}
		role="button"
		tabindex="0"
		aria-label="Close menu"
		class="fixed inset-0 z-[60] bg-white/80 dark:bg-black/60 backdrop-blur-sm md:hidden"
		in:fade={{ duration: 200 }}
		out:fade={{ duration: 200 }}
	></div>
{/if}

<!-- Sidebar container -->
<aside 
	aria-label="Sidebar navigation"
	class="transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)] fixed top-0 left-0 h-screen z-[100] bg-white/[0.04] dark:bg-white/[0.02] backdrop-blur-3xl border-r border-black/[0.08] dark:border-white/20 shadow-[1px_0_0_rgba(0,0,0,0.05)] dark:shadow-[1px_0_0_rgba(255,255,255,0.15)] text-slate-900 dark:text-white {collapsed ? 'w-[88px]' : 'w-[280px]'} {mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}"
>
	<div class="flex flex-col h-full px-4 py-8 relative overflow-hidden">
		<!-- Internal Glow -->
		<div class="absolute -top-24 -left-24 w-48 h-48 bg-[var(--brand-primary)]/10 rounded-full blur-[80px] pointer-events-none"></div>

		<!-- Brand Section -->
		<div class="mb-10 px-2 flex items-center justify-between relative z-10">
			<a href={role === 'student' ? '/student' : (role === 'adviser' ? '/adviser' : '/admin')} onclick={handleNav} class="flex items-center gap-4 no-underline group/brand">
				<div class="bg-white/5 backdrop-blur-2xl p-1.5 rounded-xl border border-white/10 shadow-2xl group-hover/brand:scale-110 transition-transform duration-500">
					<img
						src={$branding.logoUrl || '/Messenger_creation_1261776042047231.jpeg'}
						alt="Logo"
						class="w-8 h-8 object-contain rounded-lg"
					/>
				</div>
				{#if !collapsed}
					<div class="flex flex-col" in:fade={{ duration: 400 }}>
						<span class="text-xl font-black tracking-tighter text-slate-900 dark:text-white uppercase italic leading-none">
							{$branding.appName}
						</span>
					</div>
				{/if}
			</a>
		</div>

		<!-- User Profile Card -->
		<div class="mb-10 p-4 rounded-[2rem] bg-black/[0.03] dark:bg-white/[0.04] border border-black/[0.05] dark:border-white/10 backdrop-blur-3xl group transition-all duration-500 hover:bg-black/[0.05] dark:hover:bg-white/[0.06] hover:border-black/[0.1] dark:hover:border-white/20 {collapsed ? 'px-2' : 'shadow-2xl'} relative z-10 overflow-hidden">
			<div class="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>
			<div class="flex items-center gap-4 relative z-10">
				<label class="relative cursor-pointer shrink-0" title="Click to upload photo">
					<input type="file" accept="image/*" onchange={handlePhotoUpload} hidden disabled={isUploading} />
					<div class="relative group/avatar">
						<Avatar 
							src={student_info?.photo_url} 
							rounded 
							size={collapsed ? "sm" : "md"} 
							class="ring-2 ring-white/10 group-hover/avatar:ring-[var(--brand-primary)] transition-all duration-500 shadow-2xl"
						>
							{initials}
						</Avatar>
						<div class="absolute inset-0 bg-[var(--brand-primary)]/20 rounded-full blur-md opacity-0 group-hover/avatar:opacity-100 transition-all duration-500"></div>
					</div>
					{#if isUploading}
						<div class="absolute inset-0 bg-black/60 rounded-full flex items-center justify-center backdrop-blur-sm">
							<Spinner size="4" color="white" />
						</div>
					{/if}
				</label>
				{#if !collapsed}
					<div class="flex-1 min-w-0" in:fade={{ duration: 400 }}>
						<p class="text-xs font-black text-slate-900 dark:text-white truncate tracking-wide">
							{(student_info?.full_name || 'Administrator').toUpperCase()}
						</p>
						<div class="flex items-center gap-2 mt-1.5">
							<div class="w-1.5 h-1.5 rounded-full {$branding.showBgAnims ? 'animate-pulse' : ''} shadow-[0_0_8px_var(--brand-glow)]" style="background: {roleBadge[role]?.color}"></div>
							<span class="text-[9px] font-black uppercase tracking-[0.2em] text-slate-900/40 dark:text-white/40">
								{roleBadge[role]?.label}
							</span>
						</div>
					</div>
				{/if}
			</div>
		</div>

		<!-- Navigation Links -->
		<nav class="flex-1 overflow-y-auto space-y-3 custom-scrollbar px-1 mt-2 relative z-10">
			{#each navItems as item}
				{#if item.section}
					{#if !collapsed}
						<p class="text-[10px] font-black text-slate-900/20 dark:text-white/20 tracking-[0.4em] uppercase mt-10 mb-4 ml-4">
							{item.section}
						</p>
					{:else}
						<div class="h-[1px] bg-black/[0.05] dark:bg-white/5 my-8 mx-4"></div>
					{/if}
				{:else if item.path}
					{@const isActive = page.url.pathname === item.path.split('?')[0]}
					<div class="relative group/nav">
						<a
							href={item.path}
							onclick={handleNav}
							class="flex items-center gap-5 px-3 py-2.5 rounded-[1.5rem] transition-all duration-500 relative overflow-hidden group {isActive ? 'bg-white dark:bg-white/10 text-[var(--brand-primary)] dark:text-white shadow-xl' : 'text-slate-900/40 dark:text-white/40 hover:text-slate-900 dark:hover:text-white hover:bg-black/[0.02] dark:hover:bg-white/[0.02]'}"
						>
							<div class="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-2xl transition-all duration-500 relative {isActive ? 'bg-[var(--brand-primary)] text-white shadow-lg' : 'bg-black/[0.03] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/5 group-hover:scale-110 group-hover:bg-black/[0.05] dark:group-hover:bg-white/5'}">
								<svg class="w-5 h-5 transition-transform duration-500 {isActive ? 'scale-110' : 'group-hover:scale-110'}" fill="none" stroke="currentColor" stroke-width={isActive ? '2.5' : '2'} viewBox="0 0 24 24">
									<path stroke-linecap="round" stroke-linejoin="round" d={item.icon} />
								</svg>
							</div>
							
							{#if !collapsed}
								<span class="truncate font-black tracking-widest text-[11px] uppercase transition-colors duration-500">{item.name}</span>
								{#if isActive}
									<div class="ml-auto w-1.5 h-1.5 bg-[var(--brand-primary)] rounded-full shadow-[0_0_8px_var(--brand-glow)] animate-pulse"></div>
								{/if}
							{/if}
						</a>
						{#if collapsed}
							<Tooltip placement="right" class="z-[200] font-black text-[10px] tracking-widest uppercase bg-black/90 border border-white/10 backdrop-blur-xl">{item.name}</Tooltip>
						{/if}
					</div>
				{:else if item.action === 'toggleTheme'}
					<div class="relative group/nav">
						<button
							onclick={toggleTheme}
							class="w-full flex items-center gap-5 px-3 py-2.5 rounded-[1.5rem] transition-all duration-500 relative overflow-hidden group text-slate-900/40 dark:text-white/40 hover:text-slate-900 dark:hover:text-white hover:bg-black/[0.02] dark:hover:bg-white/[0.02]"
						>
							<div class="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-2xl transition-all duration-500 bg-black/[0.03] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/5 group-hover:scale-110 group-hover:rotate-90 group-hover:bg-black/[0.05] dark:group-hover:bg-white/5 group-hover:text-yellow-500">
								<SunOutline size="sm" class="transition-colors" />
							</div>
							
							{#if !collapsed}
								<span class="truncate font-black tracking-widest text-[11px] uppercase transition-colors duration-500">{item.name}</span>
							{/if}
						</button>
						{#if collapsed}
							<Tooltip placement="right" class="z-[200] font-black text-[10px] tracking-widest uppercase bg-black/90 border border-white/10 backdrop-blur-xl">Toggle Theme</Tooltip>
						{/if}
					</div>
				{/if}
			{/each}
		</nav>

		<!-- Footer -->
		<div class="mt-auto pt-8 border-t border-white/5 pb-4 relative z-10">
			<button
				onclick={handleLogout}
				class="w-full flex items-center gap-5 px-5 py-4 rounded-[1.5rem] text-slate-900/30 dark:text-white/30 hover:text-red-500 hover:bg-red-500/10 transition-all duration-500 group relative overflow-hidden border border-transparent hover:border-red-500/20 shadow-2xl"
			>
				<div class="flex items-center justify-center w-8 h-8 rounded-xl bg-black/[0.05] dark:bg-white/5 group-hover:bg-red-500 group-hover:text-white transition-all duration-500 group-hover:shadow-[0_0_20px_rgba(239,68,68,0.4)]">
					<ArrowRightToBracketOutline size="sm" class="rotate-180 group-hover:-translate-x-1 transition-transform duration-500" />
				</div>
				{#if !collapsed}<span class="font-black text-[11px] tracking-[0.3em] uppercase transition-colors duration-500">Sign Out</span>{/if}
			</button>
		</div>

		<!-- Collapse Toggle -->
		<button
			onclick={() => (collapsed = !collapsed)}
			class="absolute -right-3 top-12 w-7 h-7 bg-[#02040a] border border-white/10 rounded-full hidden md:flex items-center justify-center text-white/30 hover:text-[var(--brand-primary)] hover:border-[var(--brand-primary)] hover:scale-110 shadow-2xl transition-all duration-500 z-50 ring-4 ring-[#02040a] group/toggle"
			title={collapsed ? 'Expand' : 'Collapse'}
		>
			<ChevronLeftOutline size="xs" class="transition-transform duration-500 {collapsed ? 'rotate-180' : ''} group-hover/toggle:scale-125" />
		</button>
	</div>
</aside>

<!-- Mobile Topbar -->
<div class="md:hidden fixed top-0 left-0 right-0 h-16 bg-[#02040a]/80 backdrop-blur-2xl border-b border-white/10 px-4 flex items-center justify-between z-[40]">
	<div class="flex items-center gap-4">
		<button
			onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
			class="p-2.5 text-white/60 hover:text-white hover:bg-white/5 rounded-xl transition-all border border-white/5"
		>
			<GridOutline size="md" />
		</button>
		<img
			src={$branding.logoUrl || '/Messenger_creation_1261776042047231.jpeg'}
			alt="Logo"
			class="w-8 h-8 object-contain rounded-lg shadow-2xl"
		/>
	</div>
	
	<div class="flex items-center gap-4 bg-white/5 p-1.5 rounded-2xl border border-white/10 shadow-xl">
		<div class="text-right px-2">
			<p class="text-[9px] font-black text-white truncate max-w-[100px] uppercase tracking-wider leading-none">
				{(student_info?.full_name || 'Admin').split(' ')[0]}
			</p>
			<p class="text-[7px] font-black uppercase tracking-[0.2em] text-[var(--brand-primary)] mt-1">
				{roleBadge[role]?.label}
			</p>
		</div>
		<Avatar src={student_info?.photo_url} rounded size="sm" border class="border-white/10 shadow-2xl ring-1 ring-white/5">
			{initials}
		</Avatar>
	</div>
</div>

<!-- Main Content Area -->
<main class="main-container {collapsed ? 'md:pl-[88px]' : 'md:pl-[280px]'} transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)] relative z-10">
	<div class="min-h-screen bg-transparent p-6 md:p-10 lg:p-12 relative">
		<!-- Inner content glow -->
		<div class="absolute top-0 right-0 w-[600px] h-[600px] bg-[var(--brand-primary)]/5 rounded-full blur-[150px] pointer-events-none -z-10"></div>
		
		{@render children()}
	</div>
</main>
<style>
	/* Sidebar specific layout tweaks */
	aside {
		display: flex !important;
		visibility: visible !important;
		opacity: 1 !important;
	}

	:global(body) {
		background-color: var(--bg-main);
		overflow-x: hidden;
	}

	.custom-scrollbar {
		scrollbar-width: none;
		-ms-overflow-style: none;
	}
	.custom-scrollbar::-webkit-scrollbar {
		display: none;
	}
</style>
