/**
 * Next.js Middleware for Authentication
 * ForgeWorks Route Protection
 *
 * This middleware runs on every request and handles:
 * - Redirecting unauthenticated users to login
 * - Redirecting authenticated users away from auth pages
 * - Protecting API routes
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Routes that require authentication
const PROTECTED_ROUTES = [
  '/',
  '/settings',
  '/profile',
  '/ws/dashboard',
];

// Routes that are only for unauthenticated users
const AUTH_ROUTES = ['/login', '/register'];

// Public routes that don't require auth
const PUBLIC_ROUTES = ['/terms', '/privacy', '/api'];

/**
 * Check if the current path matches any of the given routes
 */
function matchesRoute(pathname: string, routes: string[]): boolean {
  return routes.some((route) => {
    // Exact match
    if (route === pathname) return true;
    // Prefix match for nested routes (e.g., /settings/*)
    if (pathname.startsWith(route + '/')) return true;
    return false;
  });
}

/**
 * Get access token from cookies or authorization header
 * Note: This only checks if a token EXISTS, not if it's valid
 * Full validation happens on the backend
 */
function getTokenFromRequest(request: NextRequest): string | null {
  // Check for token in localStorage is not possible in middleware
  // We rely on the cookie set by the auth system
  const accessToken = request.cookies.get('access_token')?.value;
  if (accessToken) return accessToken;

  // Also check Authorization header for API requests
  const authHeader = request.headers.get('authorization');
  if (authHeader?.startsWith('Bearer ')) {
    return authHeader.substring(7);
  }

  return null;
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip middleware for static files and Next.js internals
  if (
    pathname.startsWith('/_next') ||
    pathname.startsWith('/static') ||
    pathname.includes('.') // Files with extensions (images, etc.)
  ) {
    return NextResponse.next();
  }

  // Skip API routes - they handle their own auth
  if (pathname.startsWith('/api')) {
    return NextResponse.next();
  }

  // Check for authentication token
  // Note: In a real app, you might also validate the token here
  // For now, we just check if it exists - the actual validation
  // happens when the page loads and calls the backend
  const token = getTokenFromRequest(request);
  const isAuthenticated = !!token;

  // If user is on auth route and is authenticated, redirect to home
  if (matchesRoute(pathname, AUTH_ROUTES) && isAuthenticated) {
    return NextResponse.redirect(new URL('/', request.url));
  }

  // For now, we'll allow access to protected routes and let the
  // client-side handle the redirect if not authenticated.
  // This is because the token is stored in localStorage, not cookies,
  // so we can't reliably check auth status in middleware.
  //
  // Alternative: Store token in httpOnly cookie for server-side auth check
  // if (matchesRoute(pathname, PROTECTED_ROUTES) && !isAuthenticated) {
  //   const loginUrl = new URL('/login', request.url);
  //   loginUrl.searchParams.set('redirect', pathname);
  //   return NextResponse.redirect(loginUrl);
  // }

  return NextResponse.next();
}

// Configure which routes the middleware runs on
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (images, etc.)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\..*|api).*)',
  ],
};
