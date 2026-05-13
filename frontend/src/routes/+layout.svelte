<script>
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { onMount } from 'svelte';
	import { goto, preloadCode } from '$app/navigation';
	import { theme } from '$lib/stores/theme.js';
	import { loadBranding } from '$lib/stores/branding.js';
	import { authSession } from '$lib/stores/auth.js';
	import { voterSession } from '$lib/stores/session.js';
	import { page } from '$app/state';
	import Toast from '$lib/components/Toast.svelte';
	import { superAdmin as superAdminApi } from '$lib/api.js';
	import { invalidateAll } from '$lib/cache.js';

	let { children } = $props();

	onMount(() => {
		// Apply custom branding (colors + logo) from API on every page load
		loadBranding();

		// --- Eagerly prefetch all route JS bundles after first paint ---
		// This makes every subsequent navigation feel instant.
		preloadCode(
			'/admin',
			'/admin/elections',
			'/admin/voters',
			'/admin/advisers',
			'/admin/audit',
			'/admin/departments',
			'/admin/dept-admins',
			'/admin/results',
			'/admin/settings',
			'/admin/profile',
			'/adviser',
			'/adviser/candidates',
			'/adviser/partylists',
			'/adviser/results',
			'/adviser/audit',
			'/adviser/change-password',
			'/adviser/profile',
			'/student',
			'/student/ballot',
			'/student/results',
			'/student/profile',
			'/student/validate',
			'/login',
			'/super-admin/setup'
		);

		// --- Setup guard: redirect to initialization if no super admin exists yet ---
		const SETUP_PATH = '/super-admin/setup';
		if (page.url.pathname !== SETUP_PATH) {
			superAdminApi.getSetupStatus().then((status) => {
				if (!status.configured) goto(SETUP_PATH);
			}).catch(() => {
				// If the endpoint is unreachable, don't block the app
			});
		}

		// Refresh admin/adviser session details if missing
		const syncProfile = async () => {
			const session = JSON.parse(sessionStorage.getItem('univote_admin_session') || 'null');
			if (session && session.access_token) {
				try {
					const { auth: authApi } = await import('$lib/api.js');
					const me = await authApi.getMe();
					if (me) {
						console.log('Syncing profile:', me);
						authSession.update(old => ({ ...old, ...me }));
						// Update sessionStorage too
						const updated = { ...session, ...me };
						sessionStorage.setItem('univote_admin_session', JSON.stringify(updated));
					}
				} catch (err) {
					console.error('Sync failed:', err);
				}
			}
		};
		syncProfile();

		const unsubTheme = theme.subscribe((val) => {
			if (val === 'dark') {
				document.documentElement.classList.add('dark');
			} else {
				document.documentElement.classList.remove('dark');
			}
		});

		// Global session check for protected routes
		const unsubAuth = authSession.subscribe(session => {
			const path = page.url.pathname;
			if (!session && (page.url.pathname.startsWith('/admin') || page.url.pathname.startsWith('/adviser'))) {
				invalidateAll(); // clear cache on logout
				goto('/login');
			}
		});

		const unsubVoter = voterSession.subscribe(session => {
			if (!session && page.url.pathname.startsWith('/student') && page.url.pathname !== '/student/validate') {
				goto('/student/validate');
			}
		});

		return () => {
			unsubTheme();
			unsubAuth();
			unsubVoter();
		};
	});
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>



<Toast />

{@render children()}
