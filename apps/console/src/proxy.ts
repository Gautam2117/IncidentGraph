import { NextRequest, NextResponse } from 'next/server';

export function proxy(request: NextRequest) {
  if (!request.cookies.has('incidentgraph_session')) {
    const login = new URL('/login', request.url);
    login.searchParams.set('returnTo', request.nextUrl.pathname);
    return NextResponse.redirect(login);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api|login|_next/static|_next/image|favicon.ico).*)'],
};
