import { NextRequest } from "next/server";
import { GET, POST } from "@/app/api/training/[sessionId]/bookmarks/route";
import {
  GET as GET_SINGLE,
  PUT,
  DELETE,
} from "@/app/api/training/[sessionId]/bookmarks/[bookmarkId]/route";

describe("/api/training/[sessionId]/bookmarks", () => {
  const sessionId = "test-session-1";
  const userId = "user-123";

  describe("GET - List bookmarks", () => {
    it("returns empty list when no bookmarks exist", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks?userId=${userId}`
      );
      const request = new NextRequest(url);

      const response = await GET(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.bookmarks).toEqual([]);
      expect(data.count).toBe(0);
    });

    it("returns 400 when userId is missing", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks`
      );
      const request = new NextRequest(url);

      const response = await GET(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe("User ID is required");
    });
  });

  describe("POST - Create bookmark", () => {
    it("creates a new bookmark", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks`
      );
      const request = new NextRequest(url, {
        method: "POST",
        body: JSON.stringify({
          userId,
          timestamp: 120,
          note: "Important moment",
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(201);
      expect(data.success).toBe(true);
      expect(data.bookmark).toMatchObject({
        sessionId,
        userId,
        timestamp: 120,
        note: "Important moment",
      });
      expect(data.bookmark.id).toBeDefined();
      expect(data.bookmark.createdAt).toBeDefined();
      expect(data.bookmark.updatedAt).toBeDefined();
    });

    it("creates bookmark without note", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks`
      );
      const request = new NextRequest(url, {
        method: "POST",
        body: JSON.stringify({
          userId,
          timestamp: 200,
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(201);
      expect(data.bookmark.note).toBe("");
    });

    it("returns 400 when userId is missing", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks`
      );
      const request = new NextRequest(url, {
        method: "POST",
        body: JSON.stringify({
          timestamp: 120,
          note: "Test",
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe("User ID is required");
    });

    it("returns 400 when timestamp is invalid", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks`
      );
      const request = new NextRequest(url, {
        method: "POST",
        body: JSON.stringify({
          userId,
          timestamp: -10,
          note: "Test",
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe("Invalid timestamp");
    });

    it("accepts timestamp of 0", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks`
      );
      const request = new NextRequest(url, {
        method: "POST",
        body: JSON.stringify({
          userId,
          timestamp: 0,
          note: "Start of video",
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(201);
      expect(data.bookmark.timestamp).toBe(0);
    });
  });

  describe("GET - Get single bookmark", () => {
    it("returns a bookmark by ID", async () => {
      // First create a bookmark
      const createUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks`
      );
      const createRequest = new NextRequest(createUrl, {
        method: "POST",
        body: JSON.stringify({
          userId,
          timestamp: 150,
          note: "Test bookmark",
        }),
      });

      const createResponse = await POST(createRequest, { params: { sessionId } });
      const createData = await createResponse.json();
      const bookmarkId = createData.bookmark.id;

      // Then retrieve it
      const getUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks/${bookmarkId}?userId=${userId}`
      );
      const getRequest = new NextRequest(getUrl);

      const response = await GET_SINGLE(getRequest, {
        params: { sessionId, bookmarkId },
      });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.bookmark.id).toBe(bookmarkId);
      expect(data.bookmark.timestamp).toBe(150);
      expect(data.bookmark.note).toBe("Test bookmark");
    });

    it("returns 404 when bookmark not found", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks/nonexistent?userId=${userId}`
      );
      const request = new NextRequest(url);

      const response = await GET_SINGLE(request, {
        params: { sessionId, bookmarkId: "nonexistent" },
      });
      const data = await response.json();

      expect(response.status).toBe(404);
      expect(data.error).toBe("Bookmark not found");
    });

    it("returns 403 when accessing another user's bookmark", async () => {
      // Create bookmark for user-123
      const createUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks`
      );
      const createRequest = new NextRequest(createUrl, {
        method: "POST",
        body: JSON.stringify({
          userId: "user-123",
          timestamp: 160,
          note: "User 123's bookmark",
        }),
      });

      const createResponse = await POST(createRequest, { params: { sessionId } });
      const createData = await createResponse.json();
      const bookmarkId = createData.bookmark.id;

      // Try to access with different user
      const getUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks/${bookmarkId}?userId=user-456`
      );
      const getRequest = new NextRequest(getUrl);

      const response = await GET_SINGLE(getRequest, {
        params: { sessionId, bookmarkId },
      });
      const data = await response.json();

      expect(response.status).toBe(403);
      expect(data.error).toBe("Unauthorized");
    });
  });

  describe("PUT - Update bookmark", () => {
    it("updates bookmark note", async () => {
      // Create bookmark
      const createUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks`
      );
      const createRequest = new NextRequest(createUrl, {
        method: "POST",
        body: JSON.stringify({
          userId,
          timestamp: 170,
          note: "Original note",
        }),
      });

      const createResponse = await POST(createRequest, { params: { sessionId } });
      const createData = await createResponse.json();
      const bookmarkId = createData.bookmark.id;

      // Update it
      const updateUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks/${bookmarkId}`
      );
      const updateRequest = new NextRequest(updateUrl, {
        method: "PUT",
        body: JSON.stringify({
          userId,
          note: "Updated note",
        }),
      });

      const response = await PUT(updateRequest, {
        params: { sessionId, bookmarkId },
      });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.bookmark.note).toBe("Updated note");
      expect(data.bookmark.timestamp).toBe(170); // Should not change
    });

    it("returns 404 when bookmark not found", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks/nonexistent`
      );
      const request = new NextRequest(url, {
        method: "PUT",
        body: JSON.stringify({
          userId,
          note: "Updated",
        }),
      });

      const response = await PUT(request, {
        params: { sessionId, bookmarkId: "nonexistent" },
      });
      const data = await response.json();

      expect(response.status).toBe(404);
      expect(data.error).toBe("Bookmark not found");
    });

    it("returns 403 when updating another user's bookmark", async () => {
      // Create bookmark for user-123
      const createUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks`
      );
      const createRequest = new NextRequest(createUrl, {
        method: "POST",
        body: JSON.stringify({
          userId: "user-123",
          timestamp: 180,
          note: "User 123's bookmark",
        }),
      });

      const createResponse = await POST(createRequest, { params: { sessionId } });
      const createData = await createResponse.json();
      const bookmarkId = createData.bookmark.id;

      // Try to update with different user
      const updateUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks/${bookmarkId}`
      );
      const updateRequest = new NextRequest(updateUrl, {
        method: "PUT",
        body: JSON.stringify({
          userId: "user-456",
          note: "Hacked!",
        }),
      });

      const response = await PUT(updateRequest, {
        params: { sessionId, bookmarkId },
      });
      const data = await response.json();

      expect(response.status).toBe(403);
      expect(data.error).toBe("Unauthorized");
    });
  });

  describe("DELETE - Delete bookmark", () => {
    it("deletes a bookmark", async () => {
      // Create bookmark
      const createUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks`
      );
      const createRequest = new NextRequest(createUrl, {
        method: "POST",
        body: JSON.stringify({
          userId,
          timestamp: 190,
          note: "To be deleted",
        }),
      });

      const createResponse = await POST(createRequest, { params: { sessionId } });
      const createData = await createResponse.json();
      const bookmarkId = createData.bookmark.id;

      // Delete it
      const deleteUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks/${bookmarkId}`
      );
      const deleteRequest = new NextRequest(deleteUrl, {
        method: "DELETE",
        body: JSON.stringify({ userId }),
      });

      const response = await DELETE(deleteRequest, {
        params: { sessionId, bookmarkId },
      });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.message).toBe("Bookmark deleted successfully");
    });

    it("returns 404 when bookmark not found", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks/nonexistent`
      );
      const request = new NextRequest(url, {
        method: "DELETE",
        body: JSON.stringify({ userId }),
      });

      const response = await DELETE(request, {
        params: { sessionId, bookmarkId: "nonexistent" },
      });
      const data = await response.json();

      expect(response.status).toBe(404);
      expect(data.error).toBe("Bookmark not found");
    });

    it("returns 403 when deleting another user's bookmark", async () => {
      // Create bookmark for user-123
      const createUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks`
      );
      const createRequest = new NextRequest(createUrl, {
        method: "POST",
        body: JSON.stringify({
          userId: "user-123",
          timestamp: 200,
          note: "User 123's bookmark",
        }),
      });

      const createResponse = await POST(createRequest, { params: { sessionId } });
      const createData = await createResponse.json();
      const bookmarkId = createData.bookmark.id;

      // Try to delete with different user
      const deleteUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks/${bookmarkId}`
      );
      const deleteRequest = new NextRequest(deleteUrl, {
        method: "DELETE",
        body: JSON.stringify({ userId: "user-456" }),
      });

      const response = await DELETE(deleteRequest, {
        params: { sessionId, bookmarkId },
      });
      const data = await response.json();

      expect(response.status).toBe(403);
      expect(data.error).toBe("Unauthorized");
    });
  });

  describe("Integration - Full CRUD lifecycle", () => {
    it("completes full CRUD lifecycle", async () => {
      const testUserId = "integration-user";

      // CREATE
      const createUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks`
      );
      const createRequest = new NextRequest(createUrl, {
        method: "POST",
        body: JSON.stringify({
          userId: testUserId,
          timestamp: 250,
          note: "Integration test",
        }),
      });

      const createResponse = await POST(createRequest, { params: { sessionId } });
      const createData = await createResponse.json();
      const bookmarkId = createData.bookmark.id;

      expect(createResponse.status).toBe(201);

      // READ (single)
      const getUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks/${bookmarkId}?userId=${testUserId}`
      );
      const getRequest = new NextRequest(getUrl);

      const getResponse = await GET_SINGLE(getRequest, {
        params: { sessionId, bookmarkId },
      });
      const getData = await getResponse.json();

      expect(getResponse.status).toBe(200);
      expect(getData.bookmark.note).toBe("Integration test");

      // UPDATE
      const updateUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks/${bookmarkId}`
      );
      const updateRequest = new NextRequest(updateUrl, {
        method: "PUT",
        body: JSON.stringify({
          userId: testUserId,
          note: "Updated integration test",
        }),
      });

      const updateResponse = await PUT(updateRequest, {
        params: { sessionId, bookmarkId },
      });
      const updateData = await updateResponse.json();

      expect(updateResponse.status).toBe(200);
      expect(updateData.bookmark.note).toBe("Updated integration test");

      // LIST
      const listUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks?userId=${testUserId}`
      );
      const listRequest = new NextRequest(listUrl);

      const listResponse = await GET(listRequest, { params: { sessionId } });
      const listData = await listResponse.json();

      expect(listResponse.status).toBe(200);
      expect(listData.bookmarks.length).toBeGreaterThan(0);

      // DELETE
      const deleteUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/bookmarks/${bookmarkId}`
      );
      const deleteRequest = new NextRequest(deleteUrl, {
        method: "DELETE",
        body: JSON.stringify({ userId: testUserId }),
      });

      const deleteResponse = await DELETE(deleteRequest, {
        params: { sessionId, bookmarkId },
      });

      expect(deleteResponse.status).toBe(200);
    });
  });
});
