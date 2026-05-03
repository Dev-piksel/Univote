<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';
	import { voterSession } from '$lib/stores/session.js';
	import { branding } from '$lib/stores/branding.js';

	/** @type {{ student_info?: any }} */
	let { student_info } = $props();

	let collapsed = $state(false);

	onMount(() => {
		const saved = localStorage.getItem('sb');
		if (saved === '1') {
			collapsed = true;
			document.body.classList.add('col');
		}
	});

	function toggleSB() {
		collapsed = !collapsed;
		document.body.classList.toggle('col');
		localStorage.setItem('sb', collapsed ? '1' : '0');
	}

	function handleLogout() {
		voterSession.logout();
		goto('/student/validate');
	}

	const initials = $derived(
		(student_info?.full_name || '??')
			.split(' ')
			.slice(0, 2)
			.map((/** @type {string} */ w) => w[0]?.toUpperCase())
			.join('')
	);

	const navItems = [
		{
			name: 'Dashboard',
			path: '/student',
			icon: 'M3 3h7v7H3V3zm11 0h7v7h-7V3zm0 11h7v7h-7v-7zM3 14h7v7H3v-7z'
		},
		{
			name: 'Cast Vote',
			path: '/student/ballot',
			icon: 'M12 2a10 10 0 100 20 10 10 0 000-20zm0 4v6l4 2'
		},
		{
			name: 'Results',
			path: '/student/results',
			icon: 'M18 20V10M12 20V4M6 20v-6'
		},
		{
			name: 'Profile',
			path: '/student/profile',
			icon: 'M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'
		}
	];
</script>

<aside class="sidebar">
	<button class="toggle" onclick={toggleSB} title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>
		<svg
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2.5"
			stroke-linecap="round"
			stroke-linejoin="round"
			style="transform: {collapsed ? 'rotate(180deg)' : 'none'}; transition: transform var(--ease);"
		>
			<polyline points="15 18 9 12 15 6" />
		</svg>
	</button>

	<a href="/student" class="sb-logo" style="text-decoration: none;">
		<img src={$branding.logoUrl || "/Messenger_creation_1261776042047231.jpeg"} alt="{$branding.appName} Logo" class="sb-logo-img" />
		<span class="sb-logo-text">{$branding.appName}</span>
	</a>

	<div class="sb-user-card">
		<div class="sb-avatar">
			{#if student_info?.photo_url}
				<img src={student_info.photo_url} alt={student_info.full_name} class="sb-avatar-img" />
			{:else}
				{initials}
			{/if}
		</div>
		<div class="sb-uinfo">
			<div class="name">{student_info?.full_name || 'Voter Session'}</div>
			<div class="role">STUDENT</div>
		</div>
	</div>

	<nav class="sb-nav">
		<div class="sb-nav-label">Navigation</div>
		{#each navItems as item}
			{@const isActive = page.url.pathname === item.path}
			<a
				href={item.path}
				class="nav-item"
				class:active={isActive}
				data-tip={item.name}
			>
				<svg
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<path d={item.icon} />
				</svg>
				<span class="lbl">{item.name}</span>
			</a>
		{/each}
	</nav>

	<button class="sb-signout" onclick={handleLogout} data-tip="Sign Out">
		<svg
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2"
			stroke-linecap="round"
			stroke-linejoin="round"
		>
			<path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
			<polyline points="16 17 21 12 16 7" />
			<line x1="21" y1="12" x2="9" y2="12" />
		</svg>
		<span class="lbl">Sign Out</span>
	</button>
</aside>

<style>
	.sidebar {
		display: none;
	}

	@media (min-width: 768px) {
		.sidebar {
			display: flex;
			flex-direction: column;
			width: var(--sw);
			min-height: 100vh;
			background: var(--surface);
			border-right: 1px solid var(--border);
			position: fixed;
			top: 0;
			left: 0;
			bottom: 0;
			z-index: 100;
			transition: width var(--ease);
			overflow: hidden;
		}

		.toggle {
			position: absolute;
			top: 22px;
			right: -13px;
			width: 26px;
			height: 26px;
			background: var(--surface);
			border: 1.5px solid var(--border);
			border-radius: 50%;
			display: grid;
			place-items: center;
			cursor: pointer;
			z-index: 101;
			box-shadow: 0 1px 6px rgba(0, 0, 0, 0.1);
			transition: background 0.2s;
			padding: 0;
		}
		.toggle:hover {
			background: var(--accent-bg);
		}
		.toggle svg {
			width: 13px;
			height: 13px;
			color: var(--muted);
		}

		.sb-logo {
			display: flex;
			align-items: center;
			gap: 10px;
			padding: 22px 16px 20px;
			border-bottom: 1px solid var(--border);
			min-height: 70px;
			white-space: nowrap;
			overflow: hidden;
		}
		.sb-logo-img {
			width: 32px;
			height: 32px;
			object-fit: contain;
			border-radius: 8px;
			flex-shrink: 0;
			box-shadow: 0 4px 12px rgba(0,0,0,0.08);
		}
		.sb-logo-text {
			font-weight: 800;
			font-size: 18px;
			letter-spacing: -0.5px;
			color: var(--text);
			transition:
				opacity var(--ease),
				width var(--ease);
			white-space: nowrap;
		}

		.sb-user-card {
			margin: 16px 12px;
			background: var(--surface2);
			border: 1px solid var(--border);
			border-radius: 12px;
			padding: 12px;
			display: flex;
			align-items: center;
			gap: 12px;
			overflow: hidden;
			transition: all var(--ease);
		}
		.sb-avatar {
			width: 40px;
			height: 40px;
			flex-shrink: 0;
			border-radius: 12px;
			background: var(--brand-gradient);
			display: grid;
			place-items: center;
			font-weight: 700;
			font-size: 14px;
			color: #fff;
			box-shadow: 0 4px 12px rgba(92, 96, 245, 0.2);
			overflow: hidden;
		}
		.sb-avatar-img {
			width: 100%;
			height: 100%;
			object-fit: cover;
		}
		.sb-uinfo {
			flex: 1;
			overflow: hidden;
			transition: opacity var(--ease);
		}
		.sb-uinfo .name {
			font-weight: 700;
			font-size: 13px;
			color: var(--text);
			white-space: nowrap;
			overflow: hidden;
			text-overflow: ellipsis;
		}
		.sb-uinfo .role {
			font-size: 9px;
			color: var(--accent);
			text-transform: uppercase;
			letter-spacing: 1px;
			margin-top: 2px;
			font-weight: 800;
		}

		.sb-nav {
			padding: 6px 8px;
			flex: 1;
		}
		.sb-nav-label {
			font-size: 10px;
			text-transform: uppercase;
			letter-spacing: 1.2px;
			color: var(--muted);
			padding: 8px 10px 4px;
			white-space: nowrap;
			overflow: hidden;
			transition: opacity var(--ease);
			font-weight: 700;
		}
		.nav-item {
			display: flex;
			align-items: center;
			gap: 11px;
			padding: 10px;
			border-radius: 10px;
			font-size: 14px;
			font-weight: 600;
			color: var(--muted);
			cursor: pointer;
			transition: all 0.18s;
			text-decoration: none;
			margin-bottom: 2px;
			white-space: nowrap;
			overflow: hidden;
			position: relative;
			border: none;
			background: transparent;
		}
		.nav-item:hover {
			background: var(--surface2);
			color: var(--text2);
		}
		.nav-item.active {
			background: var(--accent-bg);
			color: var(--accent);
		}
		.nav-item svg {
			width: 18px;
			height: 18px;
			flex-shrink: 0;
		}
		.lbl {
			transition: opacity var(--ease);
		}

		.sb-signout {
			margin: 0 8px 20px;
			padding: 10px;
			border-radius: 10px;
			display: flex;
			align-items: center;
			gap: 11px;
			font-size: 14px;
			font-weight: 600;
			color: var(--muted);
			cursor: pointer;
			transition: all 0.18s;
			white-space: nowrap;
			overflow: hidden;
			position: relative;
			border: none;
			background: transparent;
		}
		.sb-signout:hover {
			background: #fef2f2;
			color: var(--red);
		}
		.sb-signout svg {
			width: 18px;
			height: 18px;
			flex-shrink: 0;
		}
	}

	/* Col state */
	:global(body.col) .sidebar {
		width: var(--sc);
	}
	:global(body.col) .sb-logo {
		justify-content: center;
		padding-left: 0;
		padding-right: 0;
	}
	:global(body.col) .sb-logo-text {
		opacity: 0;
		width: 0;
		overflow: hidden;
	}
	:global(body.col) .sb-user-card {
		justify-content: center;
		padding: 8px;
	}
	:global(body.col) .sb-uinfo {
		display: none;
	}
	:global(body.col) .sb-nav-label {
		opacity: 0;
	}
	:global(body.col) .lbl {
		opacity: 0;
		width: 0;
		overflow: hidden;
	}

	/* Tooltip on collapse */
	:global(body.col) .nav-item:hover::after,
	:global(body.col) .sb-signout:hover::after {
		content: attr(data-tip);
		position: absolute;
		left: calc(100% + 10px);
		top: 50%;
		transform: translateY(-50%);
		background: var(--text);
		color: #fff;
		font-size: 12px;
		font-weight: 500;
		padding: 5px 11px;
		border-radius: 7px;
		white-space: nowrap;
		pointer-events: none;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		z-index: 300;
	}
</style>
