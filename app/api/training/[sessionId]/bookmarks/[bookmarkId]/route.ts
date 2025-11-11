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

// PUT - Update a bookmark
export async function PUT(
  request: NextRequest,
  { params }: { params: { sessionId: string; bookmarkId: string } }
) {
  try {
    const { sessionId, bookmarkId } = params;
    const body = await request.json();

    const { userId, note } = body;

    // Validation
    if (!userId) {
      return NextResponse.json(
        { error: "User ID is required" },
        { status: 400 }
      );
    }

    // Get existing bookmark
    const existingBookmark = bookmarksStore.get(bookmarkId);

    if (!existingBookmark) {
      return NextResponse.json(
        { error: "Bookmark not found" },
        { status: 404 }
      );
    }

    // Verify ownership
    if (existingBookmark.userId !== userId) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 403 }
      );
    }

    // Verify session match
    if (existingBookmark.sessionId !== sessionId) {
      return NextResponse.json(
        { error: "Bookmark does not belong to this session" },
        { status: 400 }
      );
    }

    // Update bookmark
    const updatedBookmark: Bookmark = {
      ...existingBookmark,
      note: note !== undefined ? note : existingBookmark.note,
      updatedAt: new Date().toISOString(),
    };

    bookmarksStore.set(bookmarkId, updatedBookmark);

    return NextResponse.json({
      success: true,
      bookmark: updatedBookmark,
    });
  } catch (error) {
    console.error("Error updating bookmark:", error);
    return NextResponse.json(
      { error: "Failed to update bookmark" },
      { status: 500 }
    );
  }
}

// DELETE - Delete a bookmark
export async function DELETE(
  request: NextRequest,
  { params }: { params: { sessionId: string; bookmarkId: string } }
) {
  try {
    const { sessionId, bookmarkId } = params;
    const body = await request.json();

    const { userId } = body;

    // Validation
    if (!userId) {
      return NextResponse.json(
        { error: "User ID is required" },
        { status: 400 }
      );
    }

    // Get existing bookmark
    const existingBookmark = bookmarksStore.get(bookmarkId);

    if (!existingBookmark) {
      return NextResponse.json(
        { error: "Bookmark not found" },
        { status: 404 }
      );
    }

    // Verify ownership
    if (existingBookmark.userId !== userId) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 403 }
      );
    }

    // Verify session match
    if (existingBookmark.sessionId !== sessionId) {
      return NextResponse.json(
        { error: "Bookmark does not belong to this session" },
        { status: 400 }
      );
    }

    // Delete bookmark
    bookmarksStore.delete(bookmarkId);

    return NextResponse.json({
      success: true,
      message: "Bookmark deleted successfully",
    });
  } catch (error) {
    console.error("Error deleting bookmark:", error);
    return NextResponse.json(
      { error: "Failed to delete bookmark" },
      { status: 500 }
    );
  }
}

// GET - Get a single bookmark (optional, for completeness)
export async function GET(
  request: NextRequest,
  { params }: { params: { sessionId: string; bookmarkId: string } }
) {
  try {
    const { sessionId, bookmarkId } = params;
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get("userId");

    if (!userId) {
      return NextResponse.json(
        { error: "User ID is required" },
        { status: 400 }
      );
    }

    const bookmark = bookmarksStore.get(bookmarkId);

    if (!bookmark) {
      return NextResponse.json(
        { error: "Bookmark not found" },
        { status: 404 }
      );
    }

    // Verify ownership
    if (bookmark.userId !== userId) {
      return NextResponse.json(
        { error: "Unauthorized" },
        { status: 403 }
      );
    }

    // Verify session match
    if (bookmark.sessionId !== sessionId) {
      return NextResponse.json(
        { error: "Bookmark does not belong to this session" },
        { status: 400 }
      );
    }

    return NextResponse.json({
      bookmark,
    });
  } catch (error) {
    console.error("Error fetching bookmark:", error);
    return NextResponse.json(
      { error: "Failed to fetch bookmark" },
      { status: 500 }
    );
  }
}
