import { NextRequest, NextResponse } from "next/server";

interface Bookmark {
  id: string;
  sessionId: string;
  userId: string;
  timestamp: number;
  note: string;
  createdAt: string;
  updatedAt: string;
}

// Mock database - In production, this would use ZeroDB user_bookmarks collection
const bookmarksStore = new Map<string, Bookmark>();

function generateId(): string {
  return `bookmark-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// GET - List bookmarks for a session
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
    const userBookmarks = Array.from(bookmarksStore.values())
      .filter((b) => b.sessionId === sessionId && b.userId === userId)
      .sort((a, b) => a.timestamp - b.timestamp);

    return NextResponse.json({
      bookmarks: userBookmarks,
      count: userBookmarks.length,
    });
  } catch (error) {
    console.error("Error fetching bookmarks:", error);
    return NextResponse.json(
      { error: "Failed to fetch bookmarks" },
      { status: 500 }
    );
  }
}

// POST - Create a bookmark
export async function POST(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  try {
    const { sessionId } = params;
    const body = await request.json();

    const { userId, timestamp, note } = body;

    // Validation
    if (!userId) {
      return NextResponse.json(
        { error: "User ID is required" },
        { status: 400 }
      );
    }

    if (typeof timestamp !== "number" || timestamp < 0) {
      return NextResponse.json(
        { error: "Invalid timestamp" },
        { status: 400 }
      );
    }

    // In production, this would:
    // 1. Verify user authentication
    // 2. Check if user has access to the session
    // 3. Create record in ZeroDB user_bookmarks collection

    const bookmark: Bookmark = {
      id: generateId(),
      sessionId,
      userId,
      timestamp,
      note: note || "",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    bookmarksStore.set(bookmark.id, bookmark);

    return NextResponse.json(
      {
        success: true,
        bookmark,
      },
      { status: 201 }
    );
  } catch (error) {
    console.error("Error creating bookmark:", error);
    return NextResponse.json(
      { error: "Failed to create bookmark" },
      { status: 500 }
    );
  }
}
