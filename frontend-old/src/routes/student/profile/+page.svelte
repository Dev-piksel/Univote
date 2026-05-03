<script>
	import { onMount } from 'svelte';
	import { student as studentApi } from '$lib/api.js';
	import { voterSession } from '$lib/stores/session.js';
	import { branding } from '$lib/stores/branding.js';
	import { fade, scale } from 'svelte/transition';

	/** @type {boolean} */
	let isUploading = $state(false);
	/** @type {string} */
	let uploadToast = $state('');
	/** @type {'success'|'error'|''} */
	let uploadToastType = $state('');

	let voterName = $derived($voterSession?.full_name || 'Student');
	let initials = $derived(
		voterName.split(' ').slice(0, 2).map(w => w[0]).join('')
	);

	/**
	 * Convert a File to base64 data URL
	 * @param {File} file
	 * @returns {Promise<string>}
	 */
	function fileToBase64(file) {
		return new Promise((resolve, reject) => {
			const reader = new FileReader();
			reader.onload = () => resolve(/** @type {string} */ (reader.result));
			reader.onerror = reject;
			reader.readAsDataURL(file);
		});
	}

	/** @param {Event} e */
	async function handlePhotoUpload(e) {
		const input = /** @type {HTMLInputElement} */ (e.target);
		const file = input.files?.[0];
		if (!file) return;

		isUploading = true;
		try {
			const base64 = await fileToBase64(file);
			const resp = await studentApi.uploadProfilePhoto(base64);
			// Update the session store with the new photo_url
			voterSession.update(s => s ? { ...s, photo_url: resp.photo_url } : s);
			uploadToast = 'Profile photo updated!';
			uploadToastType = 'success';
		} catch (err) {
			console.error('Failed to upload photo:', err);
			uploadToast = 'Failed to upload photo. Try a smaller image.';
			uploadToastType = 'error';
		} finally {
			isUploading = false;
			input.value = '';
			setTimeout(() => { uploadToast = ''; uploadToastType = ''; }, 3000);
		}
	}
</script>

<svelte:head><title>Profile | {$branding.appName}</title></svelte:head>

<div class="profile-container" in:fade>
	<div class="profile-header">
		<div class="breadcrumb">PAGES / STUDENT PROFILE</div>
		<h1 class="title">Your Profile</h1>
	</div>

	<div class="profile-card">
		<div class="photo-section">
			<div class="avatar-large">
				{#if $voterSession?.photo_url}
					<img src={$voterSession.photo_url} alt={voterName} />
				{:else}
					<div class="fallback">{initials}</div>
				{/if}
				
				<label class="upload-btn" title="Change profile picture" class:is-uploading={isUploading}>
					{#if isUploading}
						<div class="spinner-tiny"></div>
					{:else}
						<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
							<path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
							<circle cx="12" cy="13" r="4"/>
						</svg>
					{/if}
					<input type="file" accept="image/*" onchange={handlePhotoUpload} disabled={isUploading} aria-label="Upload profile photo" />
				</label>
			</div>
			
			{#if uploadToast}
				<p class="toast {uploadToastType}" in:scale>{uploadToast}</p>
			{/if}
			<p class="photo-hint">Upload a professional photo for identification.</p>
		</div>

		<div class="details-section">
			<div class="detail-group">
				<span class="label">Full Name</span>
				<p>{$voterSession?.full_name || '—'}</p>
			</div>
			<div class="detail-group">
				<span class="label">Student ID</span>
				<p class="mono">{$voterSession?.student_id || '—'}</p>
			</div>
			<div class="grid-2">
				<div class="detail-group">
					<span class="label">Program</span>
					<p>{$voterSession?.program || '—'}</p>
				</div>
				<div class="detail-group">
					<span class="label">Year Level</span>
					<p>{$voterSession?.year_level || '—'} Year</p>
				</div>
			</div>
			<div class="detail-group">
				<span class="label">Email Address</span>
				<p class="email">{$voterSession?.student_id?.toLowerCase() || ''}@uni.edu.ph</p>
			</div>

			<div class="secure-badge">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
				This profile is verified and secured by UniVote.
			</div>
		</div>
	</div>
</div>

<style>
	.profile-header { margin-bottom: 30px; }
	.breadcrumb { font-size: 10px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--accent); font-weight: 800; margin-bottom: 8px; }
	.title { font-size: 32px; font-weight: 800; color: var(--text); letter-spacing: -1px; margin: 0; }

	.profile-card {
		background: var(--surface);
		border: 1px solid var(--border);
		border-radius: 24px;
		display: grid;
		grid-template-columns: 280px 1fr;
		overflow: hidden;
		box-shadow: 0 10px 40px rgba(0,0,0,0.05);
	}

	@media (max-width: 768px) {
		.profile-card { grid-template-columns: 1fr; }
	}

	.photo-section {
		background: var(--surface2);
		padding: 40px;
		display: flex;
		flex-direction: column;
		align-items: center;
		border-right: 1px solid var(--border);
		text-align: center;
	}
	@media (max-width: 768px) { .photo-section { border-right: none; border-bottom: 1px solid var(--border); } }

	.avatar-large {
		width: 140px;
		height: 140px;
		position: relative;
		margin-bottom: 24px;
	}
	.avatar-large img {
		width: 100%;
		height: 100%;
		border-radius: 50%;
		object-fit: cover;
		border: 4px solid #fff;
		box-shadow: 0 8px 24px rgba(0,0,0,0.12);
	}
	.avatar-large .fallback {
		width: 100%;
		height: 100%;
		border-radius: 50%;
		background: var(--brand-gradient);
		display: grid;
		place-items: center;
		color: #fff;
		font-size: 44px;
		font-weight: 800;
		border: 4px solid #fff;
		box-shadow: 0 8px 24px rgba(0,0,0,0.1);
	}

	.upload-btn {
		position: absolute;
		bottom: 4px;
		right: 4px;
		width: 40px;
		height: 40px;
		background: var(--surface);
		border-radius: 50%;
		display: grid;
		place-items: center;
		cursor: pointer;
		box-shadow: 0 4px 12px rgba(0,0,0,0.15);
		border: 2px solid #fff;
		color: var(--text);
		transition: all 0.2s;
	}
	.upload-btn:hover { transform: scale(1.1); color: var(--accent); }
	.upload-btn svg { width: 18px; height: 18px; }
	.upload-btn input { display: none; }

	.toast { font-size: 13px; font-weight: 700; margin: 0 0 12px; }
	.toast.success { color: var(--green); }
	.toast.error { color: var(--red); }
	.photo-hint { font-size: 12px; color: var(--muted); line-height: 1.5; font-weight: 500; }

	.details-section { padding: 40px; }
	.detail-group { margin-bottom: 24px; }
	.detail-group .label {
		display: block;
		font-size: 10px;
		text-transform: uppercase;
		letter-spacing: 1.2px;
		color: var(--muted);
		font-weight: 800;
		margin-bottom: 6px;
	}
	.detail-group p {
		font-size: 18px;
		font-weight: 700;
		color: var(--text);
		margin: 0;
	}
	.detail-group p.mono { font-family: 'Geist Mono', monospace; letter-spacing: 1px; }
	.detail-group p.email { color: var(--accent); font-size: 16px; }

	.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

	.secure-badge {
		margin-top: 20px;
		padding: 12px 16px;
		background: var(--accent-bg);
		border-radius: 12px;
		color: var(--accent);
		font-size: 12px;
		font-weight: 600;
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.secure-badge svg { width: 16px; height: 16px; flex-shrink: 0; }

	.spinner-tiny { width: 16px; height: 16px; border: 2px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
	@keyframes spin { to { transform: rotate(360deg); } }
</style>
