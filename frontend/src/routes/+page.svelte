<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { authSession } from '$lib/stores/auth.js';
	import { voterSession } from '$lib/stores/session.js';
	import { toggleTheme } from '$lib/stores/theme.js';
	import { branding } from '$lib/stores/branding.js';
	import { ArrowRightToBracketOutline, DesktopPcOutline, UserOutline, CheckCircleOutline, ChartPieOutline, ShieldCheckOutline, LockOutline, ChevronRightOutline } from 'flowbite-svelte-icons';
	import Ripples from '$lib/components/Ripples.svelte';

	onMount(() => {
		if ($authSession) {
			const role = $authSession.role;
			if (role === 'super_admin' || role === 'dept_admin') goto('/admin');
			else goto('/adviser');
		} else if ($voterSession) {
			goto('/student');
		}
	});
</script>

<svelte:head>
	<title>{$branding.appName} — School Election System</title>
</svelte:head>

<!-- Full-viewport shell — no scroll on desktop -->
<div class="shell" style="background: {$branding.showBgAnims ? '' : 'color-mix(in srgb, var(--landing-bg-start) 85%, white)'};">
	<!-- Background blobs -->
	<div class="bg {$branding.showBgAnims ? 'animate' : ''}" aria-hidden="true">
		{#if $branding.showBgAnims}
			<div class="blob b1"></div>
			<div class="blob b2"></div>
		{/if}
		<div class="grid-lines"></div>

		<!-- Water Ripple Effect (Global Component) -->
		<Ripples />
	</div>

	<!-- ── Navbar ── -->
	<nav class="nav">
		<button class="brand" onclick={toggleTheme} title="Toggle theme">
			<img
				src={$branding.logoUrl || '/Messenger_creation_1261776042047231.jpeg'}
				alt="Logo"
				class="brand-img"
			/>
			<div class="brand-text">
				<span class="brand-name">{$branding.appName.toUpperCase()}</span>
				<span class="brand-sub">School Election System</span>
			</div>
		</button>
		<div class="status animate">
			<span class="dot"></span>
			<span class="status-text">System Online</span>
		</div>
	</nav>

	<!-- ── Main: fills all remaining height ── -->
	<main class="main">
		<!-- Hero text -->
		<div class="hero">
			<h1 class="h1">
				Voting,<br />
				<em class="accent">Redefined.</em>
			</h1>
			<p class="tagline">
				The next generation of student elections — transparent,<br class="br-hide" />
				tamper-proof, and built for academic integrity.
			</p>
		</div>

		<!-- Entry cards -->
		<div class="cards">
			<!-- Student -->
			<a href="/student/validate" class="card card--primary">
				<div class="card-icon ci--blue"><UserOutline size="md" /></div>
				<p class="card-eyebrow">Student Access</p>
				<h2 class="card-title">Cast Your Ballot</h2>
				<p class="card-desc">Authenticate with your student ID and vote in active campus elections.</p>
				<div class="chips">
					<span class="chip"><CheckCircleOutline size="xs" class="chip-ic green" />One vote per election</span>
					<span class="chip"><ChartPieOutline size="xs" class="chip-ic blue" />Instant receipt</span>
				</div>
				<div class="cta cta--blue">Enter Portal <ChevronRightOutline size="sm" class="arrow" /></div>
			</a>

			<!-- Admin -->
			<a href="/login" class="card card--dark">
				<div class="card-icon ci--dim"><DesktopPcOutline size="md" /></div>
				<p class="card-eyebrow ey--dim">Official Use Only</p>
				<h2 class="card-title">Administration</h2>
				<p class="card-desc">Full-scale election management, live analytics, and complete audit trail.</p>
				<div class="chips">
					<span class="chip"><ShieldCheckOutline size="xs" class="chip-ic blue" />Encrypted session</span>
					<span class="chip"><LockOutline size="xs" class="chip-ic green" />Full audit access</span>
				</div>
				<div class="cta cta--ghost">Staff Authenticate <ChevronRightOutline size="sm" class="arrow" /></div>
			</a>
		</div>
	</main>

	<!-- ── Footer ── -->
	<footer class="foot">
		<span class="foot-copy">© {new Date().getFullYear()} {$branding.appName} · Secure · Transparent · Official</span>
		<div class="foot-right">
			<span class="foot-badge">End-to-End Encrypted</span>
			<span class="foot-sep">·</span>
			<span class="foot-badge">Tamper-Proof Ledger</span>
		</div>
	</footer>

</div>

<style>
/* ── Global Reset ──────────────────────────────────── */
:global(html, body) {
	margin: 0; padding: 0;
	height: 100%; overflow: hidden;
}

/* ── Shell: exactly one viewport ──────────────────── */
.shell {
	position: relative;
	width: 100vw; height: 100vh;
	display: flex; flex-direction: column;
	background: #02040a;
	color: #fff;
	font-family: system-ui, -apple-system, sans-serif;
	overflow: hidden;
}

/* ── Background ───────────────────────────────────── */
.bg { 
	position: absolute; inset: 0; pointer-events: none; z-index: 0; overflow: hidden; 
}
.bg.animate {
	animation: wave-glow 10s ease-in-out infinite;
}
.blob {
	position: absolute; border-radius: 50%;
	filter: blur(100px); opacity: 0.85;
}
.b1 { width: 55vw; height: 55vh; top: -15%; left: -10%; background: rgba(0,102,255,.12); }
.b2 { width: 45vw; height: 45vh; bottom: -15%; right: -10%; background: rgba(0,51,255,.08); }
.bg.animate .b1 { animation: breathe 14s ease-in-out infinite; }
.bg.animate .b2 { animation: breathe 18s ease-in-out infinite reverse; }
.grid-lines {
	position: absolute; inset: 0;
	background-image: linear-gradient(to right,rgba(255,255,255,.015) 1px,transparent 1px),
	                  linear-gradient(to bottom,rgba(255,255,255,.015) 1px,transparent 1px);
	background-size: 48px 48px;
	mask-image: radial-gradient(ellipse 80% 80% at 50% 20%,#000 55%,transparent 100%);
}
@keyframes breathe { 0%,100%{transform:scale(1)} 50%{transform:scale(1.07)} }

@keyframes wave-glow {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.05); opacity: 1; }
}

/* ── Navbar ───────────────────────────────────────── */
.nav {
	position: relative; z-index: 10;
	display: flex; align-items: center; justify-content: space-between;
	padding: 0 2.5rem;
	height: 64px; flex-shrink: 0;
	background: rgba(2,4,10,.8);
	backdrop-filter: blur(20px);
	border-bottom: 1px solid rgba(255,255,255,.06);
}
.brand {
	display: flex; align-items: center; gap: .75rem;
	background: none; border: none; cursor: pointer; padding: 0;
}
.brand-img {
	width: 36px; height: 36px; border-radius: 9px; object-fit: contain;
	background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.08);
}
.brand-text { display: flex; flex-direction: column; gap: 1px; text-align: left; }
.brand-name { font-size: .9rem; font-weight: 900; letter-spacing: -.02em; color: #fff; line-height: 1; }
.brand-sub  { font-size: .55rem; font-weight: 700; letter-spacing: .18em; text-transform: uppercase; color: rgba(255,255,255,.35); line-height: 1; }
.status { display: flex; align-items: center; gap: .45rem; padding: .35rem .9rem; border-radius: 999px; background: rgba(16,185,129,.08); border: 1px solid rgba(16,185,129,.22); }
.dot {
	position: relative; width: 7px; height: 7px; flex-shrink: 0;
}
.dot::before,.dot::after { content:''; position:absolute; inset:0; border-radius:50%; background:#10b981; }
.status.animate .dot::before { animation: ping 1.6s ease-in-out infinite; opacity: .5; }
@keyframes ping { 0%,100%{transform:scale(1);opacity:.5} 50%{transform:scale(2.2);opacity:0} }
.status-text { font-size: .65rem; font-weight: 800; letter-spacing: .1em; text-transform: uppercase; color: #10b981; }

/* ── Main ─────────────────────────────────────────── */
.main {
	position: relative; z-index: 1;
	flex: 1; min-height: 0;                  /* fills remaining height */
	display: flex; flex-direction: column;
	align-items: center; justify-content: center;
	padding: 2rem 2.5rem 1.5rem;
	gap: 2rem;
}

/* ── Hero ─────────────────────────────────────────── */
.hero { text-align: center; }
.h1 {
	font-size: clamp(2.2rem, 6.5vw, 6rem);
	font-weight: 900; line-height: .92;
	letter-spacing: -.04em;
	color: #fff; margin: 0 0 .85rem;
	font-style: italic;
}
.accent {
	font-style: normal;
	background: linear-gradient(135deg,#60a5fa,#818cf8,#a78bfa);
	-webkit-background-clip: text; background-clip: text;
	-webkit-text-fill-color: transparent;
}
.tagline {
	font-size: clamp(.8rem, 1.6vw, 1.05rem);
	color: rgba(255,255,255,.42); line-height: 1.65;
	margin: 0;
}
.br-hide { display: inline; }

/* ── Cards ────────────────────────────────────────── */
.cards {
	display: grid; grid-template-columns: 1fr 1fr;
	gap: 1.25rem; width: 100%; max-width: 960px;
}
.card {
	position: relative;
	display: flex; flex-direction: column; gap: .6rem;
	padding: 1.5rem 1.75rem;
	border-radius: 1.5rem;
	text-decoration: none; color: inherit;
	border: 1px solid rgba(255,255,255,.07);
	transition: transform .35s cubic-bezier(.16,1,.3,1), box-shadow .35s;
	overflow: hidden;
}
.card:hover { transform: translateY(-5px); }
.card--primary { background: rgba(37,99,235,.07); }
.card--primary:hover { box-shadow: 0 20px 50px rgba(37,99,235,.22); border-color: rgba(96,165,250,.2); }
.card--dark    { background: rgba(255,255,255,.025); }
.card--dark:hover { box-shadow: 0 20px 50px rgba(0,0,0,.35); border-color: rgba(255,255,255,.1); }

.card-icon { width: 40px; height: 40px; border-radius: 11px; display:flex; align-items:center; justify-content:center; }
.ci--blue { background: rgba(59,130,246,.12); color:#60a5fa; border:1px solid rgba(96,165,250,.2); }
.ci--dim  { background: rgba(255,255,255,.05); color:rgba(255,255,255,.45); border:1px solid rgba(255,255,255,.08); }

.card-eyebrow { font-size:.6rem; font-weight:800; letter-spacing:.22em; text-transform:uppercase; color:#60a5fa; margin:0; }
.ey--dim { color: rgba(255,255,255,.28); }
.card-title { font-size: clamp(1.1rem, 2.2vw, 1.6rem); font-weight:900; letter-spacing:-.025em; color:#fff; margin:0; line-height:1.1; }
.card-desc  { font-size:.78rem; line-height:1.6; color:rgba(255,255,255,.38); margin:0; }

.chips { display:flex; flex-wrap:wrap; gap:.5rem; }
.chip {
	display:flex; align-items:center; gap:.35rem;
	padding:.3rem .7rem; border-radius:999px;
	background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.07);
	font-size:.65rem; font-weight:700; color:rgba(255,255,255,.55); letter-spacing:.03em;
}
:global(.green) { color:#34d399 !important; }
:global(.blue)  { color:#60a5fa !important; }

.cta {
	display:flex; align-items:center; justify-content:center; gap:.45rem;
	margin-top:.25rem; padding:.75rem 1.25rem;
	border-radius: .875rem;
	font-size:.7rem; font-weight:800; letter-spacing:.18em; text-transform:uppercase;
	transition: all .25s;
}
.cta--blue  { background:#2563eb; color:#fff; box-shadow:0 6px 20px rgba(37,99,235,.3); }
.cta--blue:hover  { background:#1d4ed8; box-shadow:0 10px 28px rgba(37,99,235,.5); }
.cta--ghost { background:rgba(255,255,255,.06); color:rgba(255,255,255,.8); border:1px solid rgba(255,255,255,.1); }
.cta--ghost:hover { background:#fff; color:#070c19; }
:global(.arrow) { transition: transform .25s; }
.card:hover :global(.arrow) { transform: translateX(4px); }

/* ── Footer ───────────────────────────────────────── */
.foot {
	position: relative; z-index: 10; flex-shrink: 0;
	display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;
	padding: .75rem 2.5rem;
	background: rgba(0,0,0,.25);
	border-top: 1px solid rgba(255,255,255,.05);
	gap: .5rem;
}
.foot-copy { font-size:.62rem; color:rgba(255,255,255,.2); font-weight:500; }
.foot-right { display:flex; align-items:center; gap:.5rem; }
.foot-badge { font-size:.6rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:rgba(255,255,255,.18); }
.foot-sep   { color:rgba(255,255,255,.1); }

/* ── Responsive: allow scroll on small screens ─────── */
@media (max-width: 768px) {
	:global(html, body) { overflow: auto; height: auto; }
	.shell { height: auto; min-height: 100vh; overflow: visible; }
	.cards { grid-template-columns: 1fr; gap: 1rem; }
	.main  { padding: 2rem 1.25rem 1.5rem; gap: 1.75rem; justify-content: flex-start; }
	.h1    { font-size: clamp(2.4rem, 11vw, 4rem); }
	.br-hide { display: none; }
	.nav   { padding: 0 1.25rem; }
	.foot  { padding: .75rem 1.25rem; flex-direction: column; align-items: flex-start; }
	.foot-right { display: none; }
}
@media (max-width: 480px) {
	.card  { padding: 1.25rem; }
	.chips { gap: .4rem; }
}
</style>
