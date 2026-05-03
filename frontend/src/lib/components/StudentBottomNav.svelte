<script>
	import { page } from '$app/state';
	import {
		GridOutline,
		CheckCircleOutline,
		ChartOutline,
		UserOutline
	} from 'flowbite-svelte-icons';

	const navItems = [
		{ name: 'Dashboard', path: '/student',         Icon: GridOutline },
		{ name: 'Cast Vote',  path: '/student/ballot',  Icon: CheckCircleOutline },
		{ name: 'Results',    path: '/student/results', Icon: ChartOutline },
		{ name: 'Profile',    path: '/student/profile', Icon: UserOutline }
	];
</script>

<nav class="univote-bottom-nav">
	{#each navItems as item}
		{@const isActive = page.url.pathname === item.path}
		<a 
			href={item.path}
			class="nav-item"
			class:active={isActive}
			data-sveltekit-preload-data="hover"
		>
			<item.Icon size="md" class="nav-icon" />
			<span class="nav-label">{item.name}</span>
		</a>
	{/each}
</nav>

<style>
	.univote-bottom-nav {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 0;
		background: var(--surface) !important;
		border-top: 1px solid var(--border) !important;
		position: fixed !important;
		bottom: 0 !important;
		left: 0 !important;
		right: 0 !important;
		z-index: 200 !important;
		padding-bottom: max(12px, env(safe-area-inset-bottom)) !important;
		width: 100%;
		height: calc(56px + env(safe-area-inset-bottom));
	}
	.nav-item {
		display: flex !important;
		flex-direction: column !important;
		align-items: center !important;
		justify-content: center !important;
		gap: 4px;
		padding: 8px 4px;
		text-decoration: none;
		color: var(--muted) !important;
		font-size: 10px !important;
		font-weight: 600 !important;
		transition: color 0.18s ease !important;
		min-height: 56px;
		text-align: center;
		flex: 1;
	}

	.nav-item:hover {
		background: var(--bg-card) !important;
	}

	.nav-item.active {
		color: var(--accent) !important;
	}

	:global(.nav-item .nav-icon) {
		color: inherit !important;
		flex-shrink: 0;
	}

	.nav-label {
		display: block;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		font-size: 8.5px;
		font-weight: 800;
		letter-spacing: 0.2px;
		text-transform: uppercase;
	}

	@media (min-width: 1025px) {
		.univote-bottom-nav {
			display: none !important;
		}
	}
</style>
