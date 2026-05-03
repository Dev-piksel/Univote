<script>
	import { onMount } from 'svelte';
	import { admin as adminApi } from '$lib/api.js';
	import { branding } from '$lib/stores/branding.js';
	import { theme, toggleTheme } from '$lib/stores/theme.js';

	// Form state — initialised from the store, then freshened from the API
	let appName = $state($branding.appName);
	let primaryColor = $state($branding.primaryColor);
	let accentColor = $state($branding.accentColor);
	let logoPreview = $state($branding.logoUrl || null);

	/** @type {File | null} */
	let logoFile = $state(null);
	let isDragging = $state(false);
	let isSaving = $state(false);
	let successMsg = $state('');
	let errorMsg = $state('');

	onMount(async () => {
		try {
			const res = await adminApi.getSettings();
			const d = res.data || {};
			appName = d.app_name || 'UniVote';
			primaryColor = d.primary_color || '#0b75fe';
			accentColor = d.accent_color || '#5c60f5';
			logoPreview = d.logo_url || null;
		} catch {
			// fall back to store defaults
		}
	});

	function handleLogoFile(/** @type {File} */ file) {
		if (!file.type.startsWith('image/')) {
			errorMsg = 'Only image files are supported.';
			return;
		}
		logoFile = file;
		const reader = new FileReader();
		reader.onload = (e) => { logoPreview = /** @type {string} */ (e.target?.result || null); };
		reader.readAsDataURL(file);
	}

	/** @param {DragEvent} e */
	function onDrop(e) {
		e.preventDefault();
		isDragging = false;
		const file = e.dataTransfer?.files?.[0];
		if (file) handleLogoFile(file);
	}

	/** @param {Event} e */
	function onFileInput(e) {
		const file = /** @type {HTMLInputElement} */ (e.target).files?.[0];
		if (file) handleLogoFile(file);
	}

	async function handleSave() {
		isSaving = true;
		successMsg = '';
		errorMsg = '';
		try {
			await adminApi.saveSettings({
				app_name: appName,
				primary_color: primaryColor,
				accent_color: accentColor,
				logo_url: logoPreview || undefined
			});

			// INSTANT broadcast — no API round-trip needed; store drives CSS directly
			branding.set({
				appName,
				primaryColor,
				accentColor,
				logoUrl: logoPreview || null
			});

			successMsg = 'Settings saved! Theme applied across the whole app.';
			logoFile = null;
		} catch (/** @type {any} */ err) {
			errorMsg = err?.message || 'Failed to save settings.';
		} finally {
			isSaving = false;
		}
	}

	async function handleReset() {
		appName = 'UniVote';
		primaryColor = '#0b75fe';
		accentColor = '#5c60f5';
		logoPreview = null;
		logoFile = null;
		successMsg = '';
		errorMsg = '';
		// Broadcast reset immediately
		branding.set({ appName: 'UniVote', primaryColor: '#0b75fe', accentColor: '#5c60f5', logoUrl: null });
	}

	// Live preview gradient
	const previewGrad = $derived(`linear-gradient(135deg, ${primaryColor}, ${accentColor})`);
</script>

<svelte:head><title>System Settings | {$branding.appName}</title></svelte:head>

<div class="settings-shell">
	<!-- Header -->
	<div class="settings-header">
		<div>
			<p class="settings-eyebrow"><span class="prefix">Pages /</span> App Settings</p>
			<h1 class="settings-title">App Settings</h1>
			<p class="settings-subtitle">Customize branding shown on landing pages and the sidebar.</p>
		</div>
		<div class="header-actions">
			<button class="btn-reset" onclick={handleReset} disabled={isSaving}>Reset to Default</button>
			<button class="btn-save" onclick={handleSave} disabled={isSaving}>
				{#if isSaving}
					<span class="spinner"></span> Saving…
				{:else}
					<svg width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
					</svg>
					Save Changes
				{/if}
			</button>
		</div>
	</div>

	<!-- Alerts -->
	{#if successMsg}
		<div class="alert alert-success">
			<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
			</svg>
			{successMsg}
		</div>
	{/if}
	{#if errorMsg}
		<div class="alert alert-error">
			<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
				<path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
			</svg>
			{errorMsg}
		</div>
	{/if}

	<div class="settings-grid">
		<!-- Left: Config panels -->
		<div class="config-col">
			<!-- Logo Upload -->
			<div class="settings-card">
				<div class="card-label-row">
					<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
					</svg>
					<span class="card-label-text">App Logo</span>
				</div>
				<p class="card-hint">Displayed in the top-left of the sidebar and on landing pages. PNG, JPG, SVG, or WebP recommended.</p>

				<!-- Drop zone -->
				<div
					class="drop-zone {isDragging ? 'dragging' : ''}"
					ondragover={(e) => { e.preventDefault(); isDragging = true; }}
					ondragleave={() => (isDragging = false)}
					ondrop={onDrop}
					role="button"
					tabindex="0"
					onkeydown={(e) => e.key === 'Enter' && document.getElementById('logo-file-input')?.click()}
				>
					{#if logoPreview}
						<img src={logoPreview} alt="Logo preview" class="logo-preview-img" />
						<p class="drop-hint">Drop a new image to replace, or <label for="logo-file-input" class="file-link">browse</label></p>
					{:else}
						<div class="drop-icon">
							<svg width="32" height="32" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
							</svg>
						</div>
						<p class="drop-text">Drag & drop your logo here</p>
						<p class="drop-hint">or <label for="logo-file-input" class="file-link">browse files</label></p>
					{/if}
					<input
						id="logo-file-input"
						type="file"
						accept="image/*"
						style="display:none;"
						onchange={onFileInput}
					/>
				</div>

				{#if logoPreview}
					<button
						class="btn-remove-logo"
						onclick={() => { logoPreview = null; logoFile = null; }}
					>Remove logo</button>
				{/if}
			</div>

			<!-- App Name -->
			<div class="settings-card">
				<div class="card-label-row">
					<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"/>
					</svg>
					<span class="card-label-text">App Name</span>
				</div>
				<p class="card-hint">Displayed in the navbar, sidebar, and page titles.</p>
				<input
					class="settings-input"
					type="text"
					bind:value={appName}
					placeholder="e.g. UniVote, StudentElect…"
					maxlength="48"
				/>
			</div>

			<!-- Color Theme -->
			<div class="settings-card">
				<div class="card-label-row">
					<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"/>
					</svg>
					<span class="card-label-text">Color Theme</span>
				</div>
				<p class="card-hint">These colors drive buttons, gradients, and accent elements across the app.</p>

				<div class="color-fields">
					<div class="color-field">
						<label class="color-label" for="primary-color">Primary Color</label>
						<div class="color-input-row">
							<input type="color" id="primary-color" bind:value={primaryColor} class="color-swatch" />
							<input
								type="text"
								bind:value={primaryColor}
								class="settings-input hex-input"
								placeholder="#0b75fe"
								pattern="^#[0-9a-fA-F]{6}$"
								maxlength="7"
							/>
						</div>
					</div>
					<div class="color-field">
						<label class="color-label" for="accent-color">Accent Color</label>
						<div class="color-input-row">
							<input type="color" id="accent-color" bind:value={accentColor} class="color-swatch" />
							<input
								type="text"
								bind:value={accentColor}
								class="settings-input hex-input"
								placeholder="#5c60f5"
								pattern="^#[0-9a-fA-F]{6}$"
								maxlength="7"
							/>
						</div>
					</div>
				</div>

				<!-- Preset palette -->
				<div class="preset-section">
					<span class="preset-label">Blues &amp; Cyans</span>
					<div class="preset-row">
						{#each [
							{ name: 'Ocean Blue', p: '#0b75fe', a: '#00d2ff' },
							{ name: 'Royal Blue', p: '#2563eb', a: '#3b82f6' },
							{ name: 'Sky', p: '#0ea5e9', a: '#38bdf8' },
							{ name: 'Teal', p: '#0d9488', a: '#14b8a6' },
							{ name: 'Navy', p: '#1e3a8a', a: '#1d4ed8' },
						] as preset}
							<button
								class="preset-chip"
								title={preset.name}
								style="background: linear-gradient(135deg, {preset.p}, {preset.a});"
								onclick={() => { primaryColor = preset.p; accentColor = preset.a; }}
							></button>
						{/each}
					</div>
					<span class="preset-label">Purples &amp; Pinks</span>
					<div class="preset-row">
						{#each [
							{ name: 'Indigo', p: '#4f46e5', a: '#7c3aed' },
							{ name: 'Violet', p: '#7c3aed', a: '#a855f7' },
							{ name: 'Purple', p: '#9333ea', a: '#c026d3' },
							{ name: 'Fuchsia', p: '#c026d3', a: '#e879f9' },
							{ name: 'Rose', p: '#f43f5e', a: '#fb7185' },
						] as preset}
							<button
								class="preset-chip"
								title={preset.name}
								style="background: linear-gradient(135deg, {preset.p}, {preset.a});"
								onclick={() => { primaryColor = preset.p; accentColor = preset.a; }}
							></button>
						{/each}
					</div>
					<span class="preset-label">Greens &amp; Earth</span>
					<div class="preset-row">
						{#each [
							{ name: 'Forest', p: '#16a34a', a: '#059669' },
							{ name: 'Lime', p: '#65a30d', a: '#84cc16' },
							{ name: 'Amber', p: '#d97706', a: '#f59e0b' },
							{ name: 'Orange', p: '#ea580c', a: '#f97316' },
							{ name: 'Brown', p: '#78350f', a: '#92400e' },
						] as preset}
							<button
								class="preset-chip"
								title={preset.name}
								style="background: linear-gradient(135deg, {preset.p}, {preset.a});"
								onclick={() => { primaryColor = preset.p; accentColor = preset.a; }}
							></button>
						{/each}
					</div>
					<span class="preset-label">Darks &amp; Monolith</span>
					<div class="preset-row">
						{#each [
							{ name: 'Carbon', p: '#2d3436', a: '#636e72' },
							{ name: 'Midnight', p: '#0f172a', a: '#334155' },
							{ name: 'Onyx', p: '#18181b', a: '#3f3f46' },
							{ name: 'Steel', p: '#475569', a: '#94a3b8' },
							{ name: 'Deep Space', p: '#020617', a: '#1e293b' },
						] as preset}
							<button
								class="preset-chip"
								title={preset.name}
								style="background: linear-gradient(135deg, {preset.p}, {preset.a});"
								onclick={() => { primaryColor = preset.p; accentColor = preset.a; }}
							></button>
						{/each}
					</div>
					<span class="preset-label">Neons &amp; Cyber</span>
					<div class="preset-row">
						{#each [
							{ name: 'Electric', p: '#f0abfc', a: '#818cf8' },
							{ name: 'Cyber', p: '#22d3ee', a: '#f472b6' },
							{ name: 'Magma', p: '#fb923c', a: '#db2777' },
							{ name: 'Aurora', p: '#4ade80', a: '#22d3ee' },
							{ name: 'Ultraviolet', p: '#8b5cf6', a: '#ec4899' },
						] as preset}
							<button
								class="preset-chip"
								title={preset.name}
								style="background: linear-gradient(135deg, {preset.p}, {preset.a});"
								onclick={() => { primaryColor = preset.p; accentColor = preset.a; }}
							></button>
						{/each}
					</div>
					<span class="preset-label">Pastels &amp; Soft</span>
					<div class="preset-row">
						{#each [
							{ name: 'Mint', p: '#6ee7b7', a: '#a7f3d0' },
							{ name: 'Lavender', p: '#c4b5fd', a: '#ddd6fe' },
							{ name: 'Peach', p: '#fdba74', a: '#fed7aa' },
							{ name: 'Sky Soft', p: '#7dd3fc', a: '#bae6fd' },
							{ name: 'Cotton Candy', p: '#f9a8d4', a: '#fbcfe8' },
						] as preset}
							<button
								class="preset-chip"
								title={preset.name}
								style="background: linear-gradient(135deg, {preset.p}, {preset.a});"
								onclick={() => { primaryColor = preset.p; accentColor = preset.a; }}
							></button>
						{/each}
					</div>
					<span class="preset-label">Reds &amp; Neutral</span>
					<div class="preset-row">
						{#each [
							{ name: 'Crimson', p: '#e63946', a: '#c1121f' },
							{ name: 'Sunset', p: '#ef4444', a: '#f97316' },
							{ name: 'Slate', p: '#475569', a: '#334155' },
							{ name: 'Dark', p: '#1e293b', a: '#0f172a' },
							{ name: 'Midnight', p: '#312e81', a: '#1e1b4b' },
						] as preset}
							<button
								class="preset-chip"
								title={preset.name}
								style="background: linear-gradient(135deg, {preset.p}, {preset.a});"
								onclick={() => { primaryColor = preset.p; accentColor = preset.a; }}
							></button>
						{/each}
					</div>
				</div>
			</div>
		</div>

		<!-- Right: Live preview -->
		<div class="preview-col">
			<div class="settings-card preview-sticky">
				<div class="card-label-row">
					<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
						<path stroke-linecap="round" stroke-linejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
					</svg>
					<span class="card-label-text">Live Preview</span>
				</div>
				<p class="card-hint">How your branding will look on landing pages.</p>

				<!-- Mini landing preview -->
				<div class="mini-landing" style="background: {previewGrad}; transition: background 0.3s ease;">
					<div class="mini-topbar">
						{#if logoPreview}
							<img src={logoPreview} alt="Logo" class="mini-logo" />
						{:else}
							<div class="mini-logo-placeholder"></div>
						{/if}
						<span class="mini-appname">{appName || 'App Name'}</span>
					</div>

					<div class="mini-hero">
						<div class="mini-title-bar"></div>
						<div class="mini-subtitle-bar"></div>
						<div class="mini-cards">
							<div class="mini-card">
								<div class="mini-card-icon" style="background: rgba(255,255,255,0.15);"></div>
								<div class="mini-card-lines">
									<div class="mini-line long"></div>
									<div class="mini-line short"></div>
								</div>
								<div class="mini-btn" style="background:{previewGrad};"></div>
							</div>
							<div class="mini-card">
								<div class="mini-card-icon" style="background: rgba(255,255,255,0.1);"></div>
								<div class="mini-card-lines">
									<div class="mini-line long"></div>
									<div class="mini-line short"></div>
								</div>
								<div class="mini-btn" style="background: rgba(255,255,255,0.2);"></div>
							</div>
						</div>
					</div>
				</div>

				<!-- Sidebar preview -->
				<p class="card-hint" style="margin-top:1.25rem;">Sidebar appearance:</p>
				<div class="mini-sidebar">
					<div class="mini-sb-brand">
						{#if logoPreview}
							<img src={logoPreview} alt="Logo" style="width:20px;height:20px;border-radius:4px;object-fit:contain;" />
						{:else}
							<div style="width:20px;height:20px;border-radius:4px;background:var(--border-main);"></div>
						{/if}
						<span class="mini-sb-name">{appName || 'App Name'}</span>
					</div>
					{#each ['Dashboard', 'Elections', 'Voters'] as item, i}
						<div class="mini-sb-item {i === 0 ? 'active' : ''}" style={i === 0 ? `background: color-mix(in srgb, ${primaryColor} 15%, transparent); color: ${primaryColor}; transition: all 0.3s ease;` : 'transition: all 0.3s ease;'}>
							<div class="mini-sb-dot" style={i === 0 ? `background: ${primaryColor};` : ''}></div>
							<span>{item}</span>
						</div>
					{/each}
				</div>

				<!-- Color swatches -->
				<div class="swatch-row" style="margin-top:1rem;">
					<div class="swatch-item">
						<div class="swatch" style="background:{primaryColor}; transition: background 0.3s ease;"></div>
						<span class="swatch-label">Primary</span>
					</div>
					<div class="swatch-item">
						<div class="swatch" style="background:{accentColor}; transition: background 0.3s ease;"></div>
						<span class="swatch-label">Accent</span>
					</div>
					<div class="swatch-item">
						<div class="swatch" style="background:{previewGrad}; transition: background 0.3s ease;"></div>
						<span class="swatch-label">Gradient</span>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.settings-shell {
		padding: 1.5rem;
		max-width: 1200px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	/* Header */
	.settings-header {
		display: flex;
		align-items: flex-end;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: 1rem;
	}
	.settings-eyebrow {
		font-size: 0.6875rem;
		font-weight: 700;
		color: var(--text-main);
		text-transform: uppercase;
		letter-spacing: 0.08em;
		margin: 0 0 0.25rem;
	}
	.settings-eyebrow .prefix { color: var(--text-subtle); font-weight: 400; }
	.settings-title {
		font-size: 1.75rem;
		font-weight: 800;
		color: var(--text-main);
		margin: 0;
		letter-spacing: -0.02em;
		line-height: 1.1;
	}
	.settings-subtitle {
		font-size: 0.8125rem;
		color: var(--text-subtle);
		margin: 0.25rem 0 0;
	}
	.header-actions {
		display: flex;
		align-items: center;
		gap: 0.75rem;
	}
	.btn-reset {
		padding: 0.5rem 1rem;
		font-size: 0.8125rem;
		font-weight: 600;
		color: var(--text-muted);
		background: var(--bg-card);
		border: 1.5px solid var(--border-main);
		border-radius: 8px;
		cursor: pointer;
		transition: all 0.18s ease;
	}
	.btn-reset:hover { background: var(--bg-elevated); color: var(--text-main); }
	.btn-save {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		padding: 0.5rem 1.25rem;
		font-size: 0.8125rem;
		font-weight: 700;
		color: #0f172a;
		background: var(--brand-gradient, linear-gradient(135deg,#0b75fe,#5c60f5));
		border: none;
		border-radius: 8px;
		cursor: pointer;
		box-shadow: 0 2px 8px var(--brand-glow, rgba(11,117,254,0.28));
		transition: all 0.18s ease;
	}
	.btn-save:hover:not(:disabled) { filter: brightness(1.08); transform: translateY(-1px); }
	.btn-save:disabled { opacity: 0.55; cursor: not-allowed; }
	.spinner {
		width: 12px; height: 12px;
		border: 2px solid rgba(15,23,42,0.3);
		border-top-color: #0f172a;
		border-radius: 50%;
		animation: spin 0.7s linear infinite;
		display: inline-block;
	}
	@keyframes spin { to { transform: rotate(360deg); } }

	/* Alerts */
	.alert {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		padding: 0.75rem 1rem;
		border-radius: 10px;
		font-size: 0.8125rem;
		font-weight: 600;
	}
	.alert-success {
		background: var(--status-success-bg, #ecfdf5);
		color: var(--status-success-fg, #16a34a);
		border: 1px solid rgba(22,163,74,0.2);
	}
	.alert-error {
		background: var(--status-danger-bg, #fff1f2);
		color: var(--status-danger-fg, #dc2626);
		border: 1px solid rgba(220,38,38,0.2);
	}

	/* Grid layout */
	.settings-grid {
		display: grid;
		grid-template-columns: 1fr 380px;
		gap: 1.25rem;
		align-items: start;
	}
	@media (max-width: 900px) {
		.settings-grid { grid-template-columns: 1fr; }
	}

	.config-col, .preview-col {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	/* Settings card */
	.settings-card {
		background: var(--bg-card);
		border: 1px solid var(--border-main);
		border-radius: 16px;
		padding: 1.25rem;
		box-shadow: 0 2px 8px rgba(80,70,229,0.05);
	}
	.preview-sticky { position: sticky; top: 1.5rem; }

	.card-label-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.25rem;
		color: var(--text-subtle);
	}
	.card-label-text {
		font-size: 0.9375rem;
		font-weight: 700;
		color: var(--text-main);
	}
	.card-hint {
		font-size: 0.75rem;
		color: var(--text-subtle);
		margin: 0 0 1rem;
	}

	/* Drop zone */
	.drop-zone {
		border: 2px dashed var(--border-main);
		border-radius: 12px;
		padding: 2rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		cursor: pointer;
		transition: border-color 0.2s, background 0.2s;
		position: relative;
		text-align: center;
	}
	.drop-zone:hover, .drop-zone.dragging {
		border-color: var(--brand-primary, #0b75fe);
		background: var(--brand-primary-light, rgba(11,117,254,0.04));
	}
	.drop-icon { color: var(--text-subtle); }
	.drop-text { font-size: 0.875rem; font-weight: 600; color: var(--text-muted); margin: 0; }
	.drop-hint { font-size: 0.75rem; color: var(--text-subtle); margin: 0; }
	.file-link { color: var(--brand-primary, #0b75fe); font-weight: 600; cursor: pointer; text-decoration: underline; }
	.logo-preview-img { width: 72px; height: 72px; object-fit: contain; border-radius: 12px; }
	.btn-remove-logo {
		align-self: flex-start;
		margin-top: 0.5rem;
		font-size: 0.75rem;
		font-weight: 600;
		color: var(--status-danger-fg, #ef4444);
		background: none;
		border: none;
		cursor: pointer;
		padding: 0;
	}

	/* Inputs */
	.settings-input {
		width: 100%;
		padding: 0.625rem 0.875rem;
		font-size: 0.875rem;
		font-family: inherit;
		color: var(--text-main);
		background: var(--bg-elevated);
		border: 1.5px solid var(--border-main);
		border-radius: 10px;
		outline: none;
		transition: border-color 0.2s, box-shadow 0.2s;
	}
	.settings-input:focus {
		border-color: var(--brand-primary, #0b75fe);
		box-shadow: var(--focus-ring, 0 0 0 3px rgba(11, 117, 254, 0.12));
	}
	.hex-input { flex: 1; font-family: monospace; }

	/* Color fields */
	.color-fields { display: flex; flex-direction: column; gap: 1rem; }
	.color-field { display: flex; flex-direction: column; gap: 0.5rem; }
	.color-label { font-size: 0.6875rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }
	.color-input-row { display: flex; align-items: center; gap: 0.75rem; }
	.color-swatch {
		width: 44px; height: 44px; border-radius: 10px;
		border: 2px solid var(--border-main);
		padding: 2px; cursor: pointer; background: none;
		flex-shrink: 0;
	}
	.color-swatch::-webkit-color-swatch-wrapper { padding: 0; border-radius: 8px; }
	.color-swatch::-webkit-color-swatch { border-radius: 8px; border: none; }

	/* Presets */
	.preset-section { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 1.25rem; }
	.preset-row { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
	.preset-label { font-size: 0.6875rem; font-weight: 700; color: var(--text-subtle); text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.5rem; }
	.preset-chip {
		width: 28px; height: 28px; border-radius: 50%;
		border: 2px solid transparent;
		cursor: pointer;
		transition: transform 0.15s, border-color 0.15s;
		box-shadow: 0 2px 6px rgba(0,0,0,0.15);
	}
	.preset-chip:hover { transform: scale(1.2); border-color: white; }

	/* ── MINI LANDING PREVIEW ── */
	.mini-landing {
		border-radius: 12px;
		overflow: hidden;
		min-height: 180px;
		display: flex;
		flex-direction: column;
	}
	.mini-topbar {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.75rem;
		background: rgba(0,0,0,0.15);
	}
	.mini-logo {
		width: 18px; height: 18px; border-radius: 3px; object-fit: contain;
	}
	.mini-logo-placeholder {
		width: 18px; height: 18px; border-radius: 3px; background: rgba(255,255,255,0.3);
	}
	.mini-appname { font-size: 0.625rem; font-weight: 800; color: white; }
	.mini-hero { flex: 1; padding: 0.875rem 0.75rem; }
	.mini-title-bar { height: 10px; background: rgba(255,255,255,0.8); border-radius: 4px; width: 60%; margin-bottom: 6px; }
	.mini-subtitle-bar { height: 6px; background: rgba(255,255,255,0.4); border-radius: 3px; width: 80%; margin-bottom: 12px; }
	.mini-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
	.mini-card {
		background: rgba(255,255,255,0.95); border-radius: 8px;
		padding: 8px; display: flex; flex-direction: column; gap: 5px;
	}
	.mini-card-icon { width: 18px; height: 18px; border-radius: 5px; }
	.mini-card-lines { display: flex; flex-direction: column; gap: 3px; }
	.mini-line { height: 4px; background: #e2e8f0; border-radius: 2px; }
	.mini-line.long { width: 80%; }
	.mini-line.short { width: 55%; }
	.mini-btn { height: 14px; border-radius: 4px; }

	/* ── MINI SIDEBAR PREVIEW ── */
	.mini-sidebar {
		background: var(--bg-elevated);
		border: 1px solid var(--border-main);
		border-radius: 10px;
		padding: 0.75rem;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
	}
	.mini-sb-brand {
		display: flex; align-items: center; gap: 0.4rem;
		padding: 0.25rem 0.375rem;
		margin-bottom: 0.375rem;
	}
	.mini-sb-name { font-size: 0.6875rem; font-weight: 800; color: var(--text-main); }
	.mini-sb-item {
		display: flex; align-items: center; gap: 0.5rem;
		padding: 0.3rem 0.5rem;
		border-radius: 6px;
		font-size: 0.6875rem;
		color: var(--text-subtle);
	}
	.mini-sb-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; flex-shrink: 0; }

	/* Swatches */
	.swatch-row { display: flex; gap: 0.75rem; }
	.swatch-item { display: flex; flex-direction: column; align-items: center; gap: 0.25rem; }
	.swatch { width: 36px; height: 36px; border-radius: 8px; border: 1.5px solid var(--border-main); }
	.swatch-label { font-size: 0.5625rem; font-weight: 600; color: var(--text-subtle); text-transform: uppercase; letter-spacing: 0.05em; }
</style>
