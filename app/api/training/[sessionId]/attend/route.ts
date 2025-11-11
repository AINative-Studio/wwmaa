import { NextRequest, NextResponse } from "next/server";

export async function POST(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  try {
    const { sessionId } = params;
    const body = await request.json();
    const { userId, joinedAt } = body;

    if (!userId || !joinedAt) {
      return NextResponse.json(
        { error: "Missing required fields: userId, joinedAt" },
        { status: 400 }
      );
    }

    // In production, call backend API to record attendance
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    const response = await fetch(
      `${backendUrl}/api/training/sessions/${sessionId}/attendance`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // Add authentication headers as needed
        },
        body: JSON.stringify({
          user_id: userId,
          joined_at: joinedAt,
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.detail || "Failed to record attendance" },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json(
      {
        success: true,
        attendance: data,
      },
      { status: 201 }
    );
  } catch (error) {
    console.error("Error recording attendance:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  try {
    const { sessionId } = params;
    const body = await request.json();
    const { userId, watchTime } = body;

    if (!userId || watchTime === undefined) {
      return NextResponse.json(
        { error: "Missing required fields: userId, watchTime" },
        { status: 400 }
      );
    }

    // In production, call backend API to update watch time
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    const response = await fetch(
      `${backendUrl}/api/training/sessions/${sessionId}/attendance/${userId}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          // Add authentication headers as needed
        },
        body: JSON.stringify({
          watch_time_increment: watchTime,
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.detail || "Failed to update watch time" },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json({
      success: true,
      attendance: data,
    });
  } catch (error) {
    console.error("Error updating watch time:", error);
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
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get("userId");

    // In production, call backend API to get attendance record
    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
    const url = userId
      ? `${backendUrl}/api/training/sessions/${sessionId}/attendance/${userId}`
      : `${backendUrl}/api/training/sessions/${sessionId}/attendance`;

    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        // Add authentication headers as needed
      },
    });

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: errorData.detail || "Failed to fetch attendance" },
        { status: response.status }
      );
    }

    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error fetching attendance:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
