<script>
	import { goto } from '$app/navigation';
	import { authSession } from '$lib/stores/auth.js';
	import { voterSession } from '$lib/stores/session.js';
	import { branding } from '$lib/stores/branding.js';
	import { page } from '$app/state';
	import { toggleTheme } from '$lib/stores/theme.js';
	import { fade } from 'svelte/transition';

	/** @type {{ role: 'admin' | 'adviser' | 'student', student_info?: any, sseStatus?: 'connected' | 'reconnecting' | 'error', children: import('svelte').Snippet }} */
	let { role, student_info, sseStatus = 'connected', children } = $props();

	let collapsed = $state(false);
	let mobileMenuOpen = $state(false);

	// Adding 'section' objects to create the "MENU" and "OTHERS" dividers
	const links = {
		admin: [
			{ section: 'MENU' },
			{
				name: 'Dashboard',
				path: '/admin',
				icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6'
			},
			{
				name: 'Elections',
				path: '/admin/elections',
				icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z'
			},
			{
				name: 'Voters',
				path: '/admin/voters',
				icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z'
			},
			{
				name: 'Advisers',
				path: '/admin/advisers',
				icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z'
			},
			{ section: 'OTHERS' },
			{
				name: 'Audit Logs',
				path: '/admin/audit',
				icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4'
			},
			{
				name: 'App Settings',
				path: '/admin/settings',
				icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z'
			}
		],
		adviser: [
			{ section: 'MENU' },
			{
				name: 'Dashboard',
				path: '/adviser',
				icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6'
			},
			{
				name: 'Candidates',
				path: '/adviser/candidates',
				icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z'
			},
			{
				name: 'Partylists',
				path: '/adviser/partylists',
				icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z'
			},
			{
				name: 'Results',
				path: '/adviser/results',
				icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
			},
			{ section: 'OTHERS' },
			{
				name: 'Audit Logs',
				path: '/adviser/audit',
				icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4'
			}
		],
		student: [
			{ section: 'STATIC' },
			{
				name: 'Dashboard',
				path: '/student',
				icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6'
			},
			{
				name: 'Cast Vote',
				path: '/student/ballot',
				icon: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
			},
			{
				name: 'Results',
				path: '/student/results',
				icon: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'
			}
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
	const initials = $derived(
		(student_info?.full_name || '?')
			.split(' ')
			.slice(0, 2)
			.map((/** @type {string} */ w) => w[0]?.toUpperCase())
			.join('')
	);
	const sidebarWidth = $derived(collapsed ? '70px' : '260px');
</script>

<!-- Mobile overlay -->
{#if mobileMenuOpen}
	<div
		onclick={() => (mobileMenuOpen = false)}
		onkeydown={(e) => e.key === 'Escape' && (mobileMenuOpen = false)}
		role="button"
		tabindex="0"
		aria-label="Close menu"
		class="fixed inset-0 z-[60] bg-black/40 md:hidden"
		in:fade={{ duration: 200 }}
		out:fade={{ duration: 200 }}
	></div>
{/if}

<!-- Sidebar -->
<aside class="sidebar {collapsed ? 'collapsed' : 'expanded'} {mobileMenuOpen ? 'mobile-open' : ''}">
	<!-- Brand / Logo (Top) -->
	<div class="sidebar-brand" style="display: flex; flex-direction: column; align-items: flex-start; gap: 1rem; padding: 1.5rem 0.875rem 1rem; flex-shrink: 0; border-bottom: 2px solid rgba(0, 0, 0, 0.03); height: auto;">
		<a href={role === 'student' ? '/student' : (role === 'adviser' ? '/adviser' : '/admin')} onclick={handleNav} style="display:flex;align-items:center;gap:0.75rem;text-decoration:none; width: 100%;">
			<img
				src={$branding.logoUrl || '/Messenger_creation_1261776042047231.jpeg'}
				alt="{$branding.appName} Logo"
				style="width: 32px; height: 32px; object-fit: contain; border-radius: 6px;"
			/>
			{#if !collapsed || mobileMenuOpen}
				<span
					style="font-size: 1.125rem; font-weight: 800; color: var(--text-main); letter-spacing: -0.02em;"
					>{$branding.appName}</span
				>
			{/if}
		</a>
		<div style="border-top: 1px solid var(--border-subtle); width: 100%; margin-top: 1rem;"></div>
		<div
			class="flex items-center gap-3"
			style="width: 100%;"
		>
			<button
				onclick={toggleTheme}
				class="user-avatar"
				class:avatar-initial={!student_info?.photo_url}
				style="width: 32px; height: 32px; font-size: 0.75rem; flex-shrink: 0; cursor: pointer; transition: transform 0.2s; overflow: hidden; display: grid; place-items: center; padding: 0; border: {student_info?.photo_url ? '1px solid var(--border-main)' : 'none'};"
				title="Toggle Dark Mode"
				aria-label="Toggle Dark Mode"
			>
				{#if student_info?.photo_url}
					<img src={student_info.photo_url} alt={student_info.full_name} style="width: 100%; height: 100%; object-fit: cover;" />
				{:else}
					{initials}
				{/if}
			</button>
			{#if !collapsed || mobileMenuOpen}
				<div
					class="user-details"
					in:fade={{ duration: 150 }}
					style="flex: 1; min-width: 0;"
				>
					<p
						class="user-name"
						style="font-size: 0.875rem; font-weight: 600; color: var(--text-main); white-space: nowrap; text-overflow: ellipsis; overflow: hidden;"
					>
						{student_info?.full_name || 'Loading…'}
					</p>
					<p
						class="user-role"
						style="font-size: 0.625rem; font-weight: 600; color: var(--text-subtle); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.125rem;"
					>
						{role}
					</p>
				</div>
			{/if}
		</div>
	</div>

	<!-- Collapse toggle (desktop only) -->
	<button
		onclick={() => (collapsed = !collapsed)}
		class="collapse-btn"
		title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
	>
		<svg
			class="h-4 w-4 {collapsed ? 'rotate-180' : ''}"
			fill="none"
			stroke="currentColor"
			viewBox="0 0 24 24"
		>
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 19l-7-7 7-7" />
		</svg>
	</button>

	<!-- Nav Links with Sections -->
	<nav class="sidebar-nav">
		{#each navItems as item}
			{#if item.section}
				{#if (!collapsed || mobileMenuOpen) && item.section !== 'STATIC'}
					<p class="nav-section-title">{item.section}</p>
				{:else if item.section !== 'STATIC'}
					<div style="height:2rem;"></div>
					<!-- Spacer for collapsed mode -->
				{/if}
			{:else if item.path}
				{@const isActive = page.url.pathname === item.path.split('?')[0]}
				<a
					href={item.path}
					onclick={handleNav}
					class="nav-item {isActive ? 'active' : ''} {collapsed && !mobileMenuOpen
						? 'icon-only'
						: ''}"
					title={collapsed && !mobileMenuOpen ? item.name : ''}
				>
					{#if isActive && (!collapsed || mobileMenuOpen)}
						<div class="nav-bg"></div>
					{/if}

					<div class="nav-icon-wrap {isActive ? 'active-icon' : ''}">
						<svg
							class="nav-icon"
							fill="none"
							stroke="currentColor"
							stroke-width={isActive ? '2.5' : '2'}
							viewBox="0 0 24 24"
						>
							<path stroke-linecap="round" stroke-linejoin="round" d={item.icon} />
						</svg>
					</div>

					{#if !collapsed || mobileMenuOpen}
						<span class="nav-label">{item.name}</span>
					{/if}
				</a>
			{/if}
		{/each}
	</nav>

	<!-- User / Footer Section -->
	<div class="sidebar-footer">
		<button
			onclick={handleLogout}
			class="nav-item {collapsed && !mobileMenuOpen ? 'icon-only' : ''}"
			title="Sign Out"
			style="margin-bottom: 0.5rem;"
		>
			<div class="nav-icon-wrap">
				<svg
					class="nav-icon"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75"
					/>
				</svg>
			</div>
			{#if !collapsed || mobileMenuOpen}
				<span class="nav-label">Sign Out</span>
			{/if}
		</button>
	</div>
</aside>

<!-- Mobile topbar -->
<div class="mobile-topbar">
	<div style="display:flex;align-items:center;gap:0.75rem;">
		<button
			onclick={() => (mobileMenuOpen = !mobileMenuOpen)}
			class="topbar-btn"
			aria-label="Toggle menu"
		>
			{#if mobileMenuOpen}
				<svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
					><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" /></svg
				>
			{:else}
				<svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
					><path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
					/></svg
				>
			{/if}
		</button>
		<a href={role === 'student' ? '/student' : (role === 'adviser' ? '/adviser' : '/admin')} style="display:flex;align-items:center;gap:0.75rem;text-decoration:none;">
			<img
				src={$branding.logoUrl || '/Messenger_creation_1261776042047231.jpeg'}
				alt="{$branding.appName} Logo"
				style="width: 28px; height: 28px; object-fit: contain; border-radius: 4px;"
			/>
		</a>
	</div>

	<div style="display:flex;align-items:center;gap:0.5rem;">
		{#if sseStatus === 'reconnecting'}
			<span class="reconnect-pill">⟳ Reconnecting…</span>
		{:else if sseStatus === 'error'}
			<span class="reconnect-pill error">⚠ Connection lost</span>
		{/if}
		<div style="text-align: right; display: flex; flex-direction: column; justify-content: center;">
			<span
				style="font-size: 0.8125rem; font-weight: 600; color: var(--text-main); line-height: 1.2;"
				>{student_info?.full_name || 'Loading…'}</span
			>
			<span
				style="font-size: 0.625rem; font-weight: 600; color: var(--text-subtle); text-transform: uppercase; letter-spacing: 0.08em; line-height: 1.2;"
				>{role}</span
			>
		</div>
		<button
			onclick={toggleTheme}
			class="user-avatar"
			class:avatar-initial={!student_info?.photo_url}
			style="width:32px;height:32px;font-size:0.75rem;cursor:pointer; overflow: hidden; display: grid; place-items: center; padding: 0; border: {student_info?.photo_url ? '1px solid var(--border-main)' : 'none'};"
			title="Toggle Dark Mode"
			aria-label="Toggle Dark Mode"
		>
			{#if student_info?.photo_url}
				<img src={student_info.photo_url} alt={student_info.full_name} style="width: 100%; height: 100%; object-fit: cover;" />
			{:else}
				{initials}
			{/if}
		</button>
	</div>
</div>

<!-- Main content -->
<main class="main-content {collapsed ? 'sidebar-collapsed' : 'sidebar-expanded'}">
	{@render children()}
</main>

<style>
	/* 
   * PURITY UI (GoodFood) Inspired Sidebar 
   */

	:global(.dark) aside.sidebar {
		background-color: var(--bg-main); /* #0B1120 deep navy — admin/adviser theme */
		border-right-color: var(--border-main);
	}

	aside.sidebar {
		position: fixed;
		left: 0;
		top: 0;
		height: 100vh;
		display: flex;
		flex-direction: column;
		z-index: 70;
		/* Soft light mode background like the screenshot */
		background-color: #f8f9fa;
		border-right: none;
		transition: width 0.25s ease;
		overflow: hidden;
	}
	aside.sidebar.expanded {
		width: 260px;
	}
	aside.sidebar.collapsed {
		width: 70px;
	}
	@media (max-width: 767px) {
		aside.sidebar {
			transform: translateX(-100%);
			width: 260px !important;
			transition: transform 0.25s ease;
		}
		aside.sidebar.mobile-open {
			transform: translateX(0);
		}
	}

	/* ── BRAND HEADER ── */
	.sidebar-brand {
		display: flex;
		align-items: center;
		gap: 0.625rem;
		padding: 1.5rem 0.875rem 1rem;
		flex-shrink: 0;
		border-bottom: 2px solid rgba(0, 0, 0, 0.03);
	}
	:global(.dark) .sidebar-brand {
		border-bottom-color: rgba(255, 255, 255, 0.03);
	}

	.user-avatar {
		border-radius: 6px;
	}
	.user-details {
		min-width: 0;
	}
	.user-name {
		font-size: 0.8125rem;
		font-weight: 600;
		color: var(--text-main);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.user-role {
		font-size: 0.625rem;
		font-weight: 600;
		color: var(--text-subtle);
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}

	/* ── COLLAPSE BUTTON ── */
	.collapse-btn {
		position: absolute;
		right: -12px;
		top: 32px;
		width: 24px;
		height: 24px;
		background-color: #fff;
		border: 1px solid var(--border-subtle);
		border-radius: 50%;
		display: none;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		z-index: 80;
		transition: all 0.2s;
		color: var(--text-muted);
		padding: 0;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
	}
	:global(.dark) .collapse-btn {
		background-color: var(--bg-elevated);
	}
	@media (min-width: 768px) {
		.collapse-btn {
			display: flex;
		}
	}
	.collapse-btn:hover {
		background-color: var(--bg-hover);
		color: var(--text-main);
		transform: scale(1.1);
	}
	.collapse-btn svg {
		transition: transform 0.25s;
	}

	/* ── NAVIGATION LIST ── */
	.sidebar-nav {
		flex: 1;
		padding: 1rem 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		overflow-y: auto;
	}

	.nav-section-title {
		font-size: 0.75rem;
		font-weight: 700;
		color: #a3aed0;
		letter-spacing: 0.1em;
		margin: 1.25rem 0 0.5rem 0.5rem;
	}
	:global(.dark) .nav-section-title {
		color: var(--text-muted);
	}

	.nav-item {
		display: flex;
		align-items: center;
		gap: 0.875rem;
		padding: 0.75rem 1rem;
		border: none;
		background: transparent;
		color: #a3aed0;
		border-radius: 12px;
		cursor: pointer;
		text-align: left;
		position: relative;
		transition: all 0.2s;
		width: 100%;
		text-decoration: none;
	}

	.nav-item:hover {
		color: #8f9bba;
	}

	/* Active state mimics the #E2E8F0 light blue rounded rec */
	.nav-item.active {
		color: var(--brand-primary, #4318ff);
		font-weight: 700;
	}
	:global(.dark) .nav-item.active {
		color: #fff;
	}

	.nav-bg {
		position: absolute;
		inset: 0;
		background: var(--brand-primary-light, #e9e3ff); /* Derived from primary color */
		border-radius: 12px;
		z-index: 0;
	}
	:global(.dark) .nav-bg {
		background: var(--brand-primary-light, rgba(67, 24, 255, 0.15));
	}

	.nav-icon-wrap {
		width: 24px;
		height: 24px;
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1;
		color: inherit;
	}

	.nav-icon {
		width: 1.25rem;
		height: 1.25rem;
	}
	.nav-label {
		font-size: 0.9375rem;
		font-weight: inherit;
		z-index: 1;
	}

	.nav-item.icon-only {
		justify-content: center;
		padding: 0.75rem 0;
	}

	/* ── FOOTER ── */
	.sidebar-footer {
		padding: 1rem 1.5rem;
		display: flex;
		flex-direction: column;
		flex-shrink: 0;
	}

	/* Mobile topbar */
	.mobile-topbar {
		display: none;
		align-items: center;
		justify-content: space-between;
		height: 60px;
		padding: 0 1rem;
		background-color: var(--bg-card);
		border-bottom: 1px solid var(--border-main);
		position: sticky;
		top: 0;
		z-index: 50;
	}
	@media (max-width: 767px) {
		.mobile-topbar {
			display: flex;
		}
	}
	.topbar-btn {
		width: 36px;
		height: 36px;
		background: transparent;
		border: 1px solid var(--border-main);
		border-radius: 8px;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--text-main);
		cursor: pointer;
	}

	/* Main */
	.main-content {
		min-height: 100vh;
		background-color: var(--bg-main);
		transition: padding-left 0.25s ease;
	}
	:global(.dark) .main-content {
		background-color: var(--bg-main);
	}

	/* SSE Reconnection indicator */
	.reconnect-pill {
		display: inline-flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.2rem 0.6rem;
		background: rgba(245, 158, 11, 0.15);
		color: #b45309;
		border: 1px solid rgba(245, 158, 11, 0.3);
		border-radius: 999px;
		font-size: 0.625rem;
		font-weight: 600;
		animation: pulse-fade 1.5s ease-in-out infinite;
	}
	:global(.dark) .reconnect-pill {
		background: rgba(250, 204, 21, 0.12);
		color: #facc15;
		border-color: rgba(250, 204, 21, 0.25);
	}
	.reconnect-pill.error {
		background: rgba(239, 68, 68, 0.12);
		color: #dc2626;
		border-color: rgba(239, 68, 68, 0.25);
	}
	:global(.dark) .reconnect-pill.error {
		color: #f87171;
		border-color: rgba(248, 113, 113, 0.25);
	}
	@keyframes pulse-fade {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.55;
		}
	}

	@media (min-width: 768px) {
		.main-content.sidebar-expanded {
			padding-left: 260px;
		}
		.main-content.sidebar-collapsed {
			padding-left: 70px;
		}
	}
</style>
