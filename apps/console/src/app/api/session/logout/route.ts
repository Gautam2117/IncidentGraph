import { NextResponse } from 'next/server';

export async function POST() {
  const response = NextResponse.json({ logged_out: true });
  response.cookies.set('incidentgraph_session', '', {
    httpOnly: true,
    sameSite: 'strict',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    expires: new Date(0),
  });
  return response;
}
