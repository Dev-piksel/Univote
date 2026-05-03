<script>
	import { page } from '$app/state';

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

<nav class="bottom-nav">
	{#each navItems as item}
		{@const isActive = page.url.pathname === item.path}
		<a href={item.path} class="bn-item" class:active={isActive}>
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
			{item.name}
		</a>
	{/each}
</nav>

<style>
	.bottom-nav {
		display: flex;
		position: fixed;
		bottom: 0;
		left: 0;
		right: 0;
		height: var(--bnh);
		background: var(--surface);
		border-top: 1px solid var(--border);
		z-index: 200;
		padding: 0 8px;
		padding-bottom: env(safe-area-inset-bottom);
	}

	.bn-item {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 4px;
		font-size: 10px;
		font-weight: 600;
		color: var(--muted);
		text-decoration: none;
		cursor: pointer;
		border-radius: 10px;
		transition: color 0.18s;
		padding: 6px 4px;
	}

	.bn-item svg {
		width: 22px;
		height: 22px;
		flex-shrink: 0;
	}

	.bn-item.active {
		color: var(--accent);
	}

	@media (min-width: 768px) {
		.bottom-nav {
			display: none;
		}
	}
</style>
