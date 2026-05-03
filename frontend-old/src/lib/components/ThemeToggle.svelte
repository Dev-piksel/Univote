<script>
	import { theme, toggleTheme } from '$lib/stores/theme.js';
</script>

<button
	onclick={toggleTheme}
	class="group relative flex h-7 w-14 items-center justify-between overflow-hidden rounded-full border border-line-subtle bg-surface-elevated p-1 transition-all duration-300"
	aria-label="Toggle dark mode"
>
	<!-- Background transition -->
	<div
		class="absolute inset-0 translate-y-full bg-brand-primary/10 transition-transform duration-300 group-hover:translate-y-0"
	></div>

	<!-- Icons -->
	<div class="z-10 flex w-full items-center justify-around">
		<svg
			class="h-3.5 w-3.5 {$theme === 'light'
				? 'text-[var(--status-warning-fg)]'
				: 'text-content-muted'}"
			fill="currentColor"
			viewBox="0 0 20 20"
		>
			<path
				d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"
			/>
		</svg>
		<svg
			class="h-3.5 w-3.5 {$theme === 'dark' ? 'text-brand-primary' : 'text-content-muted'}"
			fill="currentColor"
			viewBox="0 0 20 20"
		>
			<path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
		</svg>
	</div>

	<!-- Knob -->
	<div
		class="absolute z-20 h-5 w-5 rounded-full border border-line-main bg-surface-main shadow-sm transition-all duration-300"
		style="transform: translateX({$theme === 'light' ? '0' : '1.75rem'})"
	></div>
</button>
