// Disable SSR for the entire student portal.
// Student pages require sessionStorage (client-only) for authentication,
// so server-side rendering causes hydration mismatches and blank pages.
export const ssr = false;
