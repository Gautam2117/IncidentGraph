import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  const origin = request.headers.get('origin');
  const host = request.headers.get('host');
  const allowedOrigins = [
    request.nextUrl.origin,
    `http://${host}`,
    `https://${host}`,
    'http://localhost:3000',
    'http://127.0.0.1:3000',
  ];
  if (!origin || !allowedOrigins.includes(origin)) {
    return NextResponse.json({ message: 'Cross-origin request rejected' }, { status: 403 });
  }
  const payload = await request.json();
  const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  const body = await response.json();
  if (!response.ok) {
    return NextResponse.json(body, { status: response.status });
  }
  const result = NextResponse.json({
    username: body.username,
    role: body.role,
    token_type: body.token_type,
  });
  result.cookies.set('incidentgraph_session', body.access_token, {
    httpOnly: true,
    sameSite: 'strict',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 60 * 60,
  });
  return result;
}
