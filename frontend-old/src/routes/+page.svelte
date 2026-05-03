<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authSession } from '$lib/stores/auth.js';
	import { voterSession } from '$lib/stores/session.js';
	import { toggleTheme } from '$lib/stores/theme.js';
	import { branding } from '$lib/stores/branding.js';

	onMount(() => {
		if ($authSession) goto($authSession.role === 'admin' ? '/admin' : '/adviser');
		else if ($voterSession) goto('/student/ballot');
	});
</script>

<svelte:head>
	<title>{$branding.appName} — School Election System</title>
</svelte:head>

<div class="landing">
	<!-- Decorative floating voting icons -->
	<svg class="floating-icon floating-icon-xl" style="bottom: -100px; left: -80px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="0.5"><path d="M19 11V9a2 2 0 00-2-2H5a2 2 0 00-2 2v2m0 0a2 2 0 012 2h12a2 2 0 012-2M3 11v10h18V11M12 11v10m-3-6h6"/></svg>
	<svg class="floating-icon floating-icon-lg" style="top: 5%; right: 10%; animation-delay: -3s; opacity: 0.05;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
	<svg class="floating-icon floating-icon-md" style="top: 45%; left: 40%; animation-delay: -7s;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2"><path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/></svg>
	<svg class="floating-icon floating-icon-sm" style="top: 15%; left: 20%; animation-delay: -10s; opacity: 0.06;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2m12-9a4 4 0 11-8 0 4 4 0 018 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zm-2 4v-1a3 3 0 00-3-3h-1m1.5-9a2 2 0 11-4 0 2 2 0 014 0z"/></svg>
	<svg class="floating-icon floating-icon-xs" style="bottom: 20%; right: 15%; animation-delay: -4s;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 00-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
	<svg class="floating-icon floating-icon-lg" style="top: 80%; right: 35%; animation-delay: -15s; opacity: 0.04;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"/></svg>
	<svg class="floating-icon floating-icon-md" style="top: 30%; right: 45%; animation-delay: -8s; opacity: 0.05;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M19 11V9a2 2 0 00-2-2H5a2 2 0 00-2 2v2m0 0a2 2 0 012 2h12a2 2 0 012-2M3 11v10h18V11M12 11v10m-3-6h6"/></svg>
	<svg class="floating-icon floating-icon-sm" style="bottom: 5%; left: 40%; animation-delay: -5s;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>

	<!-- Topbar -->
	<nav class="topbar">
		<div class="topbar-inner">
			<div class="topbar-brand">
				<button
					onclick={toggleTheme}
					style="background:transparent;border:none;padding:0;cursor:pointer;display:flex;align-items:center;"
					title="Toggle theme"
				>
					<img
						src={$branding.logoUrl || '/Messenger_creation_1261776042047231.jpeg'}
						alt="{$branding.appName} Logo"
						style="width: 32px; height: 32px; object-fit: contain; border-radius: 6px;"
					/>
				</button>
				<span class="logo-text">{$branding.appName}</span>
				<span class="logo-divider">|</span>
				<span class="logo-sub">School Election System</span>
			</div>
			<div class="topbar-right">
				<span class="status-dot"></span>
				<span class="status-label">System Online</span>
			</div>
		</div>
	</nav>

	<!-- Hero -->
	<main class="hero">
		<div class="hero-inner">
			<h1 class="hero-title">
				School Elections,<br />
				<span class="hero-title-accent">Done Right.</span>
			</h1>
			<p class="hero-desc">
				Transparent · Secure · Verifiable. Cast and manage student council votes through a trusted,
				real-time digital system.
			</p>

			<!-- Entry cards -->
			<div class="entry-grid">
				<!-- Student -->
				<a href="/student/validate" class="entry-card" id="entry-student">
					<div class="entry-icon-wrap entry-icon-primary">
						<svg
							class="entry-icon"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"
							/>
						</svg>
					</div>
					<div class="entry-body">
						<p class="entry-tag">Student Access</p>
						<h2 class="entry-title">Cast Your Vote</h2>
						<p class="entry-desc-card">
							Authenticate with your student ID to vote in active school elections.
						</p>
					</div>
					<div class="entry-features">
						<div class="entry-feature">
							<svg class="h-3p5 w-3p5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
								><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
							One vote per election, guaranteed
						</div>
						<div class="entry-feature">
							<svg class="h-3p5 w-3p5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
								><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
							View your ballot receipt
						</div>
					</div>
					<div class="entry-action btn-primary" style="margin-top:auto;">
						Enter Student Portal
						<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
							><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" /></svg>
					</div>
				</a>

				<!-- Staff -->
				<a href="/login" class="entry-card" id="entry-staff">
					<div class="entry-icon-wrap entry-icon-neutral">
						<svg
							class="entry-icon"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0V12a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 12V5.25"
							/>
						</svg>
					</div>
					<div class="entry-body">
						<p class="entry-tag">Staff Access</p>
						<h2 class="entry-title">Administration</h2>
						<p class="entry-desc-card">
							Manage elections, candidates, voters, and view real-time results.
						</p>
					</div>
					<div class="entry-features">
						<div class="entry-feature">
							<svg class="h-3p5 w-3p5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
								><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
							Full audit log access
						</div>
						<div class="entry-feature">
							<svg class="h-3p5 w-3p5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
								><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
							Live turnout monitoring
						</div>
					</div>
					<div class="entry-action btn-primary" style="margin-top:auto;">
						Staff Login
						<svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"
							><path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" /></svg>
					</div>
				</a>
			</div>
		</div>
	</main>

	<!-- Footer -->
	<footer class="landing-footer">
		<span>© 2025 {$branding.appName}</span>
		<span class="footer-sep">·</span>
		<span>Secure · Transparent · Official</span>
	</footer>
</div>

<style>
	:global(body) {
		background: linear-gradient(135deg, var(--brand-primary, #0b75fe) 0%, var(--brand-primary-hover, #0052cc) 50%, var(--brand-secondary, #003d99) 100%);
	}

	.landing {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		position: relative;
		overflow: hidden;
		background: linear-gradient(135deg, var(--brand-primary, #0b75fe) 0%, var(--brand-primary-hover, #0052cc) 50%, var(--brand-secondary, #003d99) 100%);
	}

	@keyframes sphereBob1 { 0%, 100% { transform: translate(0, 0); } 50% { transform: translate(15px, -25px); } }
	@keyframes sphereBob2 { 0%, 100% { transform: translate(0, 0) scale(1); } 50% { transform: translate(-12px, 18px) scale(1.06); } }
	@keyframes sphereBob3 { 0%, 100% { transform: translate(0, 0); } 33% { transform: translate(12px, -12px); } 66% { transform: translate(-8px, 10px); } }

	/* ====== TOPBAR ====== */
	.topbar {
		position: sticky;
		top: 0;
		z-index: 50;
		background: var(--brand-primary-light, rgba(0, 60, 160, 0.35));
		backdrop-filter: blur(16px);
		-webkit-backdrop-filter: blur(16px);
		border-bottom: 1px solid rgba(255, 255, 255, 0.12);
	}
	.topbar-inner {
		max-width: 900px;
		margin: 0 auto;
		padding: 0 1.5rem;
		height: 52px;
		display: flex;
		align-items: center;
		justify-content: space-between;
	}
	.topbar-brand {
		display: flex;
		align-items: center;
		gap: 0.625rem;
	}
	.logo-text {
		font-size: 0.9375rem;
		font-weight: 700;
		color: white;
	}
	.logo-divider {
		color: rgba(255,255,255,0.3);
		margin: 0 0.25rem;
	}
	.logo-sub {
		font-size: 0.75rem;
		color: rgba(255,255,255,0.6);
		font-weight: 500;
	}
	.topbar-right {
		display: flex;
		align-items: center;
		gap: 0.4rem;
	}
	.status-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		background-color: #4ade80;
		box-shadow: 0 0 6px #4ade80;
	}
	.status-label {
		font-size: 0.75rem;
		color: rgba(255,255,255,0.7);
		font-weight: 500;
	}

	/* ====== HERO ====== */
	.hero {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 3rem 1.5rem;
		position: relative;
		z-index: 1;
	}
	.hero-inner {
		width: 100%;
		max-width: 720px;
		text-align: center;
	}

	.hero-title {
		font-size: clamp(2rem, 5vw, 3rem);
		font-weight: 900;
		color: white;
		line-height: 1.1;
		letter-spacing: -0.03em;
		margin-bottom: 1rem;
	}
	.hero-title-accent {
		color: rgba(255,255,255,0.5);
	}
	.hero-desc {
		font-size: 0.9375rem;
		color: rgba(255,255,255,0.7);
		line-height: 1.65;
		max-width: 480px;
		margin: 0 auto 2.5rem;
	}

	/* ====== ENTRY CARDS ====== */
	.entry-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		text-align: left;
	}
	@media (max-width: 600px) {
		.entry-grid { grid-template-columns: 1fr; }
	}

	.entry-card {
		background: rgba(255,255,255,0.97);
		border: 1px solid rgba(255,255,255,0.3);
		border-radius: 16px;
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
		text-decoration: none;
		color: inherit;
		transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.15s;
		box-shadow: 0 8px 32px rgba(0,0,0,0.15);
	}
	.entry-card:hover {
		transform: translateY(-3px);
		box-shadow: 0 16px 48px rgba(0,0,0,0.25);
		border-color: rgba(255,255,255,0.6);
	}

	.entry-icon-wrap {
		width: 40px;
		height: 40px;
		border-radius: 10px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.entry-icon-primary {
		background-color: var(--brand-primary-light, rgba(37, 99, 235, 0.12));
		color: var(--brand-primary, #2563eb);
	}
	.entry-icon-neutral {
		background-color: #f1f5f9;
		color: #64748b;
	}
	.entry-icon { width: 20px; height: 20px; }

	.entry-tag {
		font-size: 0.6875rem;
		font-weight: 600;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		margin-bottom: 0.25rem;
	}
	.entry-title {
		font-size: 1.0625rem;
		font-weight: 700;
		color: #0f172a;
	}
	.entry-desc-card {
		font-size: 0.8125rem;
		color: #475569;
		line-height: 1.55;
		margin-top: 0.25rem;
	}

	.entry-features {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}
	.entry-feature {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		font-size: 0.75rem;
		color: #475569;
		font-weight: 500;
	}
	.h-3p5 { height: 14px; }
	.w-3p5 { width: 14px; }
	.h-4 { height: 16px; }
	.w-4 { width: 16px; }

	.entry-action {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		font-size: 0.8125rem;
		font-weight: 700;
		border-radius: 8px;
		text-decoration: none;
		justify-content: center;
		cursor: pointer;
		border: none;
		letter-spacing: 0.02em;
	}

	/* ====== FOOTER ====== */
	.landing-footer {
		position: relative;
		z-index: 1;
		padding: 1rem 1.5rem;
		border-top: 1px solid rgba(255,255,255,0.12);
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		font-size: 0.75rem;
		color: rgba(255,255,255,0.4);
		font-weight: 500;
	}
	.footer-sep {
		color: rgba(255,255,255,0.2);
	}
</style>
