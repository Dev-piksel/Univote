<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { voterSession } from '$lib/stores/session.js';
	import { branding } from '$lib/stores/branding.js';
	import { student as studentApi } from '$lib/api.js';
	import { fade, fly, scale } from 'svelte/transition';
	import { 
		Avatar,
		Tooltip
	} from 'flowbite-svelte';
	import {
		GridOutline,
		ClockOutline,
		ChartPieOutline,
		UserCircleOutline,
		ArrowRightToBracketOutline,
		ChevronLeftOutline,
		FingerprintOutline,
		ShieldCheckOutline
	} from 'flowbite-svelte-icons';

	let student_info = $derived($voterSession);
	let collapsed = $state(false);

	onMount(() => {
		const saved = sessionStorage.getItem('sb');
		if (saved === '1') {
			collapsed = true;
			document.body.classList.add('col');
		}
	});

	function toggleSB() {
		collapsed = !collapsed;
		document.body.classList.toggle('col');
		sessionStorage.setItem('sb', collapsed ? '1' : '0');
	}

	function handleLogout() {
		voterSession.logout();
		goto('/student/validate', { replaceState: true });
	}

	const initials = $derived(
		(student_info?.full_name || '')
			.split(' ')
			.filter(Boolean)
			.slice(0, 2)
			.map((w) => w[0]?.toUpperCase() || '')
			.join('') || '??'
	);

	const navItems = [
		{
			name: 'Dashboard',
			path: '/student',
			icon: GridOutline,
			id: 'nav-dash'
		},
		{
			name: 'Cast Vote',
			path: '/student/ballot',
			icon: FingerprintOutline,
			id: 'nav-vote'
		},
		{
			name: 'Results',
			path: '/student/results',
			icon: ChartPieOutline,
			id: 'nav-res'
		}
	];

</script>

<aside class="sidebar-container" class:collapsed>
	<!-- Tactile Toggle Button -->
	<button class="toggle-btn" onclick={toggleSB} aria-label={collapsed ? 'Expand' : 'Collapse'}>
		<ChevronLeftOutline size="xs" class="transition-transform duration-500 {collapsed ? 'rotate-180' : ''}" />
	</button>

	<div class="sb-inner">
		<!-- Brand Identity -->
		<div class="sb-brand">
			<div class="logo-wrapper">
				<img src={$branding.logoUrl || "/favicon.svg"} alt="Logo" />
				<div class="logo-glow"></div>
			</div>
			{#if !collapsed}
				<div class="brand-meta flex flex-col" in:fade>
					<span class="brand-text">{$branding.appName}</span>
					<span class="text-[8px] font-black uppercase tracking-[0.3em] mt-1" style="color: var(--brand-primary);">Student Portal</span>
				</div>
			{/if}
		</div>

		<!-- User Identity Card -->
		<div class="sb-user-card" class:collapsed-user={collapsed}>
			<div class="avatar-container">
				<div class="avatar-ring">
					<Avatar 
						src={student_info?.photo_url} 
						size={collapsed ? "xs" : "md"}
						class="rounded-full transition-all duration-500"
					>
						{initials}
					</Avatar>
				</div>
			</div>
			
			{#if !collapsed}
				<div class="user-info" in:fly={{ x: -10 }}>
					<p class="user-name">{student_info?.full_name || 'Student'}</p>
				</div>
			{/if}
		</div>

		<!-- Navigation Stream -->
		<nav class="sb-nav">
			{#if !collapsed}
				<p class="nav-label" in:fade>Navigation</p>
			{/if}
			
			<div class="nav-list">
				{#each navItems as item}
					{@const activeElections = $voterSession?.elections?.filter(e => e.status === 'active' && !e.has_voted) || []}
					{@const href = (item.name === 'Cast Vote' && activeElections.length === 0) ? '/student' : 
								  (item.name === 'Cast Vote' && activeElections.length === 1) ? `${item.path}?election=${activeElections[0].id}` : 
								  item.path}
					
					<a {href} class="nav-link" class:active={page.url.pathname === item.path} id={item.id} data-sveltekit-preload-data="hover">
						<div class="icon-box">
							<item.icon size="sm" />
						</div>
						{#if !collapsed}
							<span class="link-text" in:fade>{item.name}</span>
						{/if}
						{#if page.url.pathname === item.path && !collapsed}
							<div class="active-indicator animate" in:scale></div>
						{/if}
					</a>
					{#if collapsed}
						<Tooltip triggeredBy={item.id} placement="right">{item.name}</Tooltip>
					{/if}
				{/each}
			</div>

			<div class="nav-divider"></div>

			<div class="nav-list">
				<a href="/student/profile" class="nav-link" class:active={page.url.pathname === '/student/profile'} id="nav-prof">
					<div class="icon-box">
						<UserCircleOutline size="sm" />
					</div>
					{#if !collapsed}<span class="link-text">My Profile</span>{/if}
				</a>
				{#if collapsed}<Tooltip triggeredBy="nav-prof" placement="right">Profile Context</Tooltip>{/if}
			</div>
		</nav>

		<!-- Bottom Action -->
		<div class="sb-footer">
			<button class="logout-btn" onclick={handleLogout} id="nav-out">
				<div class="icon-box">
					<ArrowRightToBracketOutline size="sm" class="rotate-180" />
				</div>
				{#if !collapsed}<span>Logout</span>{/if}
			</button>
			{#if collapsed}<Tooltip triggeredBy="nav-out" placement="right">Sign Out</Tooltip>{/if}
		</div>
	</div>
</aside>

<style>
	.sidebar-container {
		display: none;
	}

	@media (min-width: 1025px) {
		.sidebar-container {
			display: flex;
			position: fixed;
			top: 0;
			left: 0;
			bottom: 0;
			width: 280px;
			background: transparent !important;
			border-right: 1px solid rgba(0, 0, 0, 0.06) !important;
			box-shadow: none !important;
			backdrop-filter: none !important;
			-webkit-backdrop-filter: none !important;
			z-index: 50;
			transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
		}

		.sidebar-container.collapsed {
			width: 88px;
		}

		.sb-inner {
			display: flex;
			flex-direction: column;
			height: 100%;
			width: 100%;
			padding: 24px 16px;
			overflow-y: auto;
			scrollbar-width: none;
			-ms-overflow-style: none;
		}
		.sb-inner::-webkit-scrollbar {
			display: none;
		}

		.toggle-btn {
			position: absolute;
			top: 32px;
			right: -12px;
			width: 24px;
			height: 24px;
			background: white;
			border: 1px solid var(--border-main);
			border-radius: 6px;
			display: flex;
			align-items: center;
			justify-content: center;
			color: var(--text-muted);
			cursor: pointer;
			box-shadow: 0 4px 12px rgba(0,0,0,0.1);
			z-index: 60;
			transition: all 0.3s;
		}
		.toggle-btn:hover {
			color: var(--brand-primary);
			transform: scale(1.1);
		}

		/* Brand Section */
		.sb-brand {
			display: flex;
			align-items: center;
			gap: 16px;
			padding: 8px 8px 32px;
		}
		.logo-wrapper {
			position: relative;
			width: 40px;
			height: 40px;
			flex-shrink: 0;
		}
		.logo-wrapper img {
			width: 100%;
			height: 100%;
			border-radius: 12px;
			object-fit: cover;
			position: relative;
			z-index: 2;
			box-shadow: 0 4px 12px rgba(0,0,0,0.1);
		}
		.logo-glow {
			position: absolute;
			inset: -4px;
			background: var(--brand-primary);
			opacity: 0.2;
			filter: blur(12px);
			border-radius: 12px;
		}
		.brand-meta {
			display: flex;
			flex-direction: column;
		}
		.brand-text {
			font-weight: 900;
			font-size: 1.1rem;
			color: var(--text-main);
			letter-spacing: -0.02em;
			line-height: 1;
		}
		.brand-tagline {
			font-size: 0.6rem;
			font-weight: 800;
			color: var(--brand-primary);
			text-transform: uppercase;
			letter-spacing: 0.2em;
			margin-top: 4px;
		}

		/* User Card */
		.sb-user-card {
			margin-top: 32px;
			padding: 16px;
			background: rgba(255, 255, 255, 0.5);
			border: 1px solid rgba(255, 255, 255, 0.8);
			border-radius: 24px;
			display: flex;
			align-items: center;
			gap: 16px;
			transition: all 0.4s;
			box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
		}
		.collapsed-user {
			background: transparent;
			border-color: transparent;
			padding: 8px;
			justify-content: center;
			box-shadow: none;
		}
		.avatar-ring {
			position: relative;
			padding: 2px;
			background: white;
			border-radius: 18px;
			box-shadow: 0 4px 12px rgba(0,0,0,0.05);
		}

		.user-info {
			min-width: 0;
		}
		.user-name {
			font-weight: 800;
			font-size: 0.9rem;
			color: var(--text-main);
			white-space: nowrap;
			overflow: hidden;
			text-overflow: ellipsis;
			line-height: 1.2;
		}
		.user-status {
			display: flex;
			align-items: center;
			gap: 6px;
			margin-top: 4px;
		}
		.status-dot {
			width: 6px;
			height: 6px;
			background: #10b981;
			border-radius: 50%;
			box-shadow: 0 0 8px #10b981;
		}
		.user-status span {
			font-size: 0.65rem;
			font-weight: 700;
			color: #10b981;
			text-transform: uppercase;
			letter-spacing: 0.05em;
		}

		/* Navigation */
		.sb-nav {
			flex: 1;
			margin-top: 40px;
			display: flex;
			flex-direction: column;
		}
		.nav-label {
			font-size: 0.65rem;
			font-weight: 900;
			color: var(--text-subtle);
			text-transform: uppercase;
			letter-spacing: 0.2em;
			padding: 0 16px 12px;
			opacity: 0.5;
		}
		.nav-list {
			display: flex;
			flex-direction: column;
			gap: 8px;
		}
		.nav-link {
			display: flex;
			align-items: center;
			gap: 16px;
			padding: 12px;
			border-radius: 16px;
			color: var(--text-subtle);
			text-decoration: none;
			transition: all 0.3s;
			position: relative;
		}
		.icon-box {
			width: 40px;
			height: 40px;
			display: flex;
			align-items: center;
			justify-content: center;
			border-radius: 12px;
			background: transparent;
			transition: all 0.3s;
			flex-shrink: 0;
		}
		.link-text {
			font-size: 0.9rem;
			font-weight: 700;
			letter-spacing: -0.01em;
		}

		.nav-link:hover {
			color: var(--text-main);
			background: rgba(255, 255, 255, 0.5);
		}
		.nav-link:hover .icon-box {
			color: var(--brand-primary);
			background: white;
			box-shadow: 0 4px 12px rgba(0,0,0,0.05);
		}

		.nav-link.active {
			background: white;
			color: var(--brand-primary);
			box-shadow: 0 8px 24px rgba(0,0,0,0.04);
		}
		.nav-link.active .icon-box {
			background: var(--brand-primary);
			color: white;
			box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
		}
		.active-indicator {
			position: absolute;
			right: 12px;
			width: 6px;
			height: 6px;
			background: var(--brand-primary);
			border-radius: 50%;
		}
		.active-indicator.animate {
			box-shadow: 0 0 12px var(--brand-primary);
		}

		.nav-divider {
			height: 1px;
			margin: 24px 16px;
		}

		/* Footer */
		.sb-footer {
			margin-top: auto;
			padding-top: 24px;
		}
		.logout-btn {
			width: 100%;
			display: flex;
			align-items: center;
			gap: 16px;
			padding: 12px;
			border-radius: 16px;
			color: var(--text-subtle);
			font-weight: 700;
			font-size: 0.9rem;
			cursor: pointer;
			border: none;
			background: transparent;
			transition: all 0.3s;
		}
		.logout-btn:hover {
			background: #fee2e2;
			color: #ef4444;
		}
		.logout-btn:hover .icon-box {
			background: white;
			color: #ef4444;
		}
	}
</style>
