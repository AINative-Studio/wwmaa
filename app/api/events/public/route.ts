import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://athletic-curiosity-production.up.railway.app';

// Mark this route as dynamic to prevent static optimization errors
export const dynamic = 'force-dynamic';

/**
 * GET /api/events/public
 * Proxy for public events endpoint to avoid CORS issues
 */
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);

    // Forward all query parameters
    const backendUrl = `${API_BASE_URL}/api/events/public?${searchParams.toString()}`;

    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error('[Events Proxy] Backend error:', response.status, response.statusText);
      return NextResponse.json(
        { error: 'Failed to fetch events from backend' },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error('[Events Proxy] Error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
