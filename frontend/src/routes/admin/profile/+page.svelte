<script>
	import { onMount } from 'svelte';
	import { authSession } from '$lib/stores/auth.js';
	import { branding } from '$lib/stores/branding.js';
	import { auth } from '$lib/api.js';
	import Notification from '$lib/components/Notification.svelte';

	let session = $authSession;
	let initials = $derived(
		(session?.full_name || '?')
			.split(' ')
			.slice(0, 2)
			.map((w) => w[0]?.toUpperCase())
			.join('')
	);

	let notification = $state({ text: '', type: 'info' });
	let isUploading = $state(false);

	/** @param {string} msg, @param {'success'|'error'} type */
	function notify(msg, type = 'success') {
		notification = { text: msg, type };
		setTimeout(() => (notification = { text: '', type: 'info' }), 4000);
	}

	onMount(async () => {
		try {
			const data = await auth.getMe();
			// Sync store with latest server data (includes department_name)
			authSession.update(s => ({ ...s, ...data }));
			session = $authSession;
		} catch (err) {
			console.error('Failed to sync profile:', err);
		}
	});

	async function handlePhotoUpload(e) {
		const file = e.target.files[0];
		if (!file) return;

		if (file.size > 2 * 1024 * 1024) {
			notify('Image must be under 2MB', 'error');
			return;
		}

		isUploading = true;
		try {
			const reader = new FileReader();
			reader.onload = async (event) => {
				const base64 = event.target.result;
				const res = await auth.updateProfile({ photo_url: base64 });
				// Update local session store
				authSession.update(s => ({ ...s, photo_url: base64 }));
				notify('Profile photo updated!');
			};
			reader.readAsDataURL(file);
		} catch (err) {
			notify(err.message, 'error');
		} finally {
			isUploading = false;
		}
	}
</script>

<svelte:head><title>Account Profile | {$branding.appName}</title></svelte:head>

<Notification {...notification} />

<div class="dash">
	<div class="dash-header">
		<div>
		<div style="display: flex; align-items: flex-end; justify-content: space-between;">
			<div>
				<p class="dash-eyebrow"><span class="prefix">Pages /</span> Account</p>
				<h1 class="dash-title">Personal Profile</h1>
			</div>
			<p style="font-size: 0.8125rem; color: var(--text-subtle); font-weight: 500;">
				{new Date().toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
			</p>
		</div>
		</div>
	</div>

	<div class="bento-grid" style="grid-template-columns: 1fr 2fr; align-items: start;">
		<!-- LEFT: Avatar & Primary Info -->
		<div class="admin-card profile-main-card">
			<div class="profile-avatar-wrapper">
				<div class="profile-avatar-large">
					{#if session?.photo_url}
						<img src={session.photo_url} alt={session.full_name} />
					{:else}
						{initials}
					{/if}
				</div>
				<label class="avatar-overlay" class:uploading={isUploading}>
					<input type="file" accept="image/*" onchange={handlePhotoUpload} hidden disabled={isUploading} />
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15a2.25 2.25 0 002.25-2.25V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" />
					</svg>
				</label>
			</div>
			
			<div style="text-align:center; margin-top:1.5rem;">
				<h2 style="font-size:1.5rem; font-weight:800; color:var(--text-main); margin-bottom:0.25rem;">{session?.full_name}</h2>
				<div class="pill pill-primary" style="font-size:0.65rem; text-transform:uppercase; letter-spacing:0.05em; padding:0.25rem 0.75rem;">
					{session?.role.replace('_', ' ')}
				</div>
			</div>

			<div class="profile-purpose-box">
				<h3 style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.1em; color:var(--brand-primary); margin-bottom:0.5rem;">Role Purpose</h3>
				<p style="font-size:0.8125rem; line-height:1.6;">
					{#if session?.role === 'super_admin'}
						As a <strong>Super Admin</strong>, you have full authority over the UniVote ecosystem. Your responsibilities include managing departments, overseeing all administrative accounts, and ensuring global system security and stability.
					{:else}
						As a <strong>Department Admin</strong>, your primary mission is to facilitate transparent and efficient elections within your assigned department. You manage voter registries, oversee advisers, and ensure that departmental election results are accurately recorded and publicized.
					{/if}
				</p>
			</div>
		</div>

		<!-- RIGHT: Identity & Security -->
		<div style="display:flex; flex-direction:column; gap:1.25rem;">
			<!-- Identity Bento -->
			<div class="admin-card" style="padding:1.5rem;">
				<h3 class="section-label" style="margin-bottom:1.25rem;">Account Identity</h3>
				<div style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem;">
					<div class="info-group">
						<span class="field-label">Employee / ID Number</span>
						<p class="info-val" style="font-family:monospace; font-size:0.9rem;">#{session?.id_number || 'N/A'}</p>
					</div>
					<div class="info-group">
						<span class="field-label">Jurisdiction</span>
						<p class="info-val">{session?.department_name || 'System Level (Global)'}</p>
					</div>
					<div class="info-group">
						<span class="field-label">Account Status</span>
						<div style="display:flex; align-items:center; gap:0.5rem;">
							<div class="status-dot success"></div>
							<p class="info-val" style="color:var(--status-success-fg);">Active</p>
						</div>
					</div>
					<div class="info-group">
						<span class="field-label">Email Address</span>
						<p class="info-val" style="font-size:0.9rem;">{session?.email || 'Not configured'}</p>
					</div>
					<div class="info-group">
						<span class="field-label">Program</span>
						<p class="info-val">{session?.program || '—'}</p>
					</div>
				</div>
			</div>

			<!-- Account Management -->
			<div class="admin-card" style="padding:1.5rem; background:linear-gradient(to bottom right, var(--bg-card), var(--bg-elevated));">
				<div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:1rem;">
					<svg class="h-5 w-5" style="color:var(--brand-primary)" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
					<h3 style="font-size:0.875rem; font-weight:700; color:var(--text-main);">Session</h3>
				</div>
				<p style="font-size:0.8125rem; color:var(--text-subtle); line-height:1.6; margin-bottom:1.5rem;">
					Manage your session and logout securely.
				</p>
				<div style="display:flex; gap:0.75rem;">
					<button class="btn btn-ghost btn-sm" style="color:var(--status-danger-fg); border:1px solid var(--status-danger-fg);" onclick={() => authSession.logout()}>Sign Out</button>
				</div>
			</div>
		</div>
	</div>
</div>

<style>
	.profile-main-card {
		padding: 2rem;
		display: flex;
		flex-direction: column;
		align-items: center;
	}
	.profile-avatar-wrapper {
		position: relative;
		width: 140px;
		height: 140px;
		padding: 6px;
		background: var(--brand-gradient);
		border-radius: 50%;
		box-shadow: var(--shadow-float);
	}
	.profile-avatar-large {
		width: 100%;
		height: 100%;
		background: var(--bg-card);
		color: var(--brand-primary);
		display: grid;
		place-items: center;
		font-size: 2.5rem;
		font-weight: 800;
		border-radius: 50%;
		overflow: hidden;
		border: 4px solid var(--bg-card);
	}
	.profile-avatar-large img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	.avatar-overlay {
		position: absolute;
		inset: 6px;
		background: rgba(0,0,0,0.6);
		color: white;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		opacity: 0;
		cursor: pointer;
		transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
		backdrop-filter: blur(4px);
	}
	.avatar-overlay:hover, .avatar-overlay.uploading {
		opacity: 1;
	}
	.avatar-overlay svg { width: 32px; height: 32px; transform: translateY(0); transition: transform 0.3s ease; }
	.avatar-overlay:hover svg { transform: translateY(-4px); }

	.profile-purpose-box {
		margin-top: 2rem;
		padding-top: 1.5rem;
		border-top: 1px solid var(--border-subtle);
		width: 100%;
	}

	.status-dot {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.status-dot.success {
		background-color: var(--status-success-fg);
		box-shadow: 0 0 10px var(--status-success-fg);
	}

	.info-group {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}
	.info-val {
		font-size: 0.9375rem;
		font-weight: 600;
		color: var(--text-main);
	}
	.h-5 { height: 1.25rem; }
	.w-5 { width: 1.25rem; }
</style>
