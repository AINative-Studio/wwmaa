import { NextRequest, NextResponse } from "next/server";

export async function POST(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  try {
    const { sessionId } = params;

    // In production, you would:
    // 1. Get the user ID from the session/auth
    // 2. Call backend API to save terms acceptance
    // 3. Store timestamp and IP address for compliance

    // For now, we'll mock the response
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

    // Example backend call (uncomment in production):
    /*
    const response = await fetch(
      `${backendUrl}/api/training/sessions/${sessionId}/accept-terms`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          accepted_at: new Date().toISOString(),
          ip_address: request.headers.get("x-forwarded-for") || request.ip,
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.detail || "Failed to accept terms" },
        { status: response.status }
      );
    }

    const data = await response.json();
    */

    // Mock response for development
    const data = {
      success: true,
      acceptedAt: new Date().toISOString(),
      sessionId,
    };

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error("Error accepting terms:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function GET(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  try {
    const { sessionId } = params;

    // Check if current user has accepted terms for this session
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

    // Mock response for development
    const data = {
      hasAccepted: false,
      acceptedAt: null,
    };

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error checking terms acceptance:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
