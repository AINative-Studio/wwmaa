import { NextRequest, NextResponse } from 'next/server';

/**
 * Search API Route
 *
 * Proxies search requests to the backend FastAPI service which handles:
 * - Embedding generation (OpenAI)
 * - Vector search (ZeroDB)
 * - AI answer generation
 * - Media attachment (Cloudflare videos, images)
 * - Related queries
 * - Caching and rate limiting
 */

interface SearchSource {
  id: string;
  title: string;
  url: string;
  description?: string;
  snippet?: string;
}

interface SearchResult {
  id: string;
  query: string;
  answer: string;
  sources?: SearchSource[];
  videoUrl?: string;
  images?: any[];
  relatedQueries?: string[];
  timestamp: string;
}

/**
 * Get the backend API URL from environment or default
 */
function getBackendUrl(): string {
  // Use NEXT_PUBLIC_API_URL if available (client-side), otherwise use SERVER_API_URL (server-side)
  return process.env.NEXT_PUBLIC_API_URL || process.env.SERVER_API_URL || 'http://localhost:8000';
}

/**
 * GET /api/search
 *
 * Query parameters:
 * - q: search query (required)
 * - bypass_cache: bypass cache for testing (optional, default: false)
 */
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('q');
    const bypassCache = searchParams.get('bypass_cache') === 'true';

    // Validate query
    if (!query || query.trim().length === 0) {
      return NextResponse.json(
        { error: 'Search query is required' },
        { status: 400 }
      );
    }

    if (query.length > 500) {
      return NextResponse.json(
        { error: 'Search query is too long (max 500 characters)' },
        { status: 400 }
      );
    }

    // Call backend search API
    const backendUrl = getBackendUrl();
    const backendResponse = await fetch(`${backendUrl}/api/search/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: query.trim(),
        bypass_cache: bypassCache,
      }),
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({ error: 'Unknown error' }));

      if (backendResponse.status === 408) {
        return NextResponse.json(
          { error: 'Search timed out. Please try again with a simpler query.' },
          { status: 408 }
        );
      } else if (backendResponse.status === 429) {
        return NextResponse.json(
          { error: 'Too many requests. Please try again in a minute.' },
          { status: 429 }
        );
      } else {
        return NextResponse.json(
          { error: errorData.message || 'Search failed. Please try again.' },
          { status: backendResponse.status }
        );
      }
    }

    // Parse backend response
    const backendData = await backendResponse.json();

    // Transform backend response to frontend format
    const result: SearchResult = {
      id: `search-${Date.now()}`,
      query,
      answer: backendData.answer || 'No answer generated',
      sources: backendData.sources || [],
      videoUrl: backendData.media?.videos?.[0]?.url,
      images: backendData.media?.images || [],
      relatedQueries: backendData.related_queries || [],
      timestamp: new Date().toISOString(),
    };

    // Add cache header
    const response = NextResponse.json(result);
    if (backendData.cached) {
      response.headers.set('X-Cache-Status', 'HIT');
    } else {
      response.headers.set('X-Cache-Status', 'MISS');
    }

    return response;

  } catch (error) {
    console.error('Search error:', error);

    // Handle fetch errors (backend unreachable)
    if (error instanceof TypeError && error.message.includes('fetch')) {
      return NextResponse.json(
        {
          error: 'Search service unavailable',
          message: 'Unable to connect to search service. Please try again later.',
        },
        { status: 503 }
      );
    }

    return NextResponse.json(
      {
        error: 'Internal server error',
        message: error instanceof Error ? error.message : 'Unknown error occurred',
      },
      { status: 500 }
    );
  }
}

/**
 * OPTIONS /api/search
 * Handle CORS preflight
 */
export async function OPTIONS(request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    },
  });
}
