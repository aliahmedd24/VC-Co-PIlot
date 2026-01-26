import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
    // Simple check for now - in production we'd verify the token properly
    // or let the client-side API interceptor handle 401s

    // For this MVP, we'll let the client-side auth handling in lib/api.ts logic 
    // and the protected layout do the heavy lifting, but we can add basic 
    // route protection here if needed.

    // Currently just passing through.
    return NextResponse.next();
}

export const config = {
    matcher: '/((?!api|_next/static|_next/image|favicon.ico).*)',
};
