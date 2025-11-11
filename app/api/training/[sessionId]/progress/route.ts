import { NextRequest, NextResponse } from "next/server";

interface WatchProgress {
  id?: string;
  userId: string;
  sessionId: string;
  lastWatchedPosition: number;
  totalWatchTime: number;
  completed: boolean;
  updatedAt: string;
}

// Mock database - In production, this would use ZeroDB
const watchProgressStore = new Map<string, WatchProgress>();

function getProgressKey(sessionId: string, userId: string): string {
  return `${sessionId}:${userId}`;
}

// GET - Get watch progress for a session
export async function GET(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  try {
    const { sessionId } = params;
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get("userId");

    if (!userId) {
      return NextResponse.json(
        { error: "User ID is required" },
        { status: 400 }
      );
    }

    // In production, fetch from ZeroDB
    const progressKey = getProgressKey(sessionId, userId);
    const progress = watchProgressStore.get(progressKey);

    if (!progress) {
      return NextResponse.json({
        position: 0,
        completed: false,
        totalWatchTime: 0,
      });
    }

    return NextResponse.json({
      position: progress.lastWatchedPosition,
      completed: progress.completed,
      totalWatchTime: progress.totalWatchTime,
      updatedAt: progress.updatedAt,
    });
  } catch (error) {
    console.error("Error fetching watch progress:", error);
    return NextResponse.json(
      { error: "Failed to fetch watch progress" },
      { status: 500 }
    );
  }
}

// POST - Update watch progress
export async function POST(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  try {
    const { sessionId } = params;
    const body = await request.json();

    const { userId, lastWatchedPosition, totalWatchTime, completed } = body;

    // Validation
    if (!userId) {
      return NextResponse.json(
        { error: "User ID is required" },
        { status: 400 }
      );
    }

    if (
      typeof lastWatchedPosition !== "number" ||
      lastWatchedPosition < 0
    ) {
      return NextResponse.json(
        { error: "Invalid lastWatchedPosition" },
        { status: 400 }
      );
    }

    if (
      typeof totalWatchTime !== "number" ||
      totalWatchTime < 0
    ) {
      return NextResponse.json(
        { error: "Invalid totalWatchTime" },
        { status: 400 }
      );
    }

    // In production, this would:
    // 1. Verify user authentication
    // 2. Check if user has access to the session
    // 3. Update or create record in ZeroDB session_attendance collection

    const progressKey = getProgressKey(sessionId, userId);
    const existingProgress = watchProgressStore.get(progressKey);

    const updatedProgress: WatchProgress = {
      id: existingProgress?.id || `progress-${Date.now()}`,
      userId,
      sessionId,
      lastWatchedPosition,
      totalWatchTime: Math.max(
        totalWatchTime,
        existingProgress?.totalWatchTime || 0
      ),
      completed: completed || false,
      updatedAt: new Date().toISOString(),
    };

    watchProgressStore.set(progressKey, updatedProgress);

    // In production, emit analytics event
    console.log("Watch progress updated:", {
      sessionId,
      userId,
      position: lastWatchedPosition,
      completed: updatedProgress.completed,
    });

    return NextResponse.json({
      success: true,
      progress: {
        position: updatedProgress.lastWatchedPosition,
        totalWatchTime: updatedProgress.totalWatchTime,
        completed: updatedProgress.completed,
      },
    });
  } catch (error) {
    console.error("Error updating watch progress:", error);
    return NextResponse.json(
      { error: "Failed to update watch progress" },
      { status: 500 }
    );
  }
}

// PUT - Update watch progress (alias for POST)
export async function PUT(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  return POST(request, { params });
}
