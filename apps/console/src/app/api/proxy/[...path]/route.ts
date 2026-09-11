import { cookies } from 'next/headers';
import { NextRequest } from 'next/server';
import { demoResponse, isDemoMode } from '@/lib/demo-data';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function forward(request: NextRequest, path: string[]) {
  if (!['GET', 'HEAD'].includes(request.method)) {
    const origin = request.headers.get('origin');
    const host = request.headers.get('host');
    const allowedOrigins = new Set([request.nextUrl.origin, `http://${host}`, `https://${host}`]);
    if (!origin || !allowedOrigins.has(origin)) {
      return Response.json({ message: 'Cross-origin request rejected' }, { status: 403 });
    }
  }
  if (isDemoMode()) {
    return demoResponse(request.method, path, request.nextUrl.searchParams);
  }
  const token = (await cookies()).get('incidentgraph_session')?.value;
  if (!token) {
    return Response.json({ message: 'Authentication required' }, { status: 401 });
  }
  const target = new URL(`/api/v1/${path.map(encodeURIComponent).join('/')}`, API_BASE);
  target.search = request.nextUrl.search;
  const headers = new Headers({ Authorization: `Bearer ${token}` });
  const contentType = request.headers.get('content-type');
  if (contentType) headers.set('content-type', contentType);
  const hasBody = !['GET', 'HEAD'].includes(request.method);
  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers,
      body: hasBody ? await request.text() : undefined,
      cache: 'no-store',
    });
  } catch {
    return Response.json({ message: 'The control plane is temporarily unreachable' }, { status: 502 });
  }
  const responseHeaders = new Headers();
  const upstreamContentType = upstream.headers.get('content-type');
  if (upstreamContentType) responseHeaders.set('content-type', upstreamContentType);
  return new Response(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

type Context = { params: Promise<{ path: string[] }> };

export async function GET(request: NextRequest, context: Context) {
  return forward(request, (await context.params).path);
}

export async function POST(request: NextRequest, context: Context) {
  return forward(request, (await context.params).path);
}

export async function DELETE(request: NextRequest, context: Context) {
  return forward(request, (await context.params).path);
}

export async function PATCH(request: NextRequest, context: Context) {
  return forward(request, (await context.params).path);
}
