import { NextRequest } from "next/server";
import { GET, POST } from "@/app/api/training/[sessionId]/progress/route";

describe("/api/training/[sessionId]/progress", () => {
  const sessionId = "test-session-1";
  const userId = "user-123";

  describe("GET", () => {
    it("returns watch progress for a user", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/progress?userId=${userId}`
      );
      const request = new NextRequest(url);

      const response = await GET(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data).toHaveProperty("position");
      expect(data).toHaveProperty("completed");
      expect(data).toHaveProperty("totalWatchTime");
    });

    it("returns default values when no progress exists", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/progress?userId=new-user`
      );
      const request = new NextRequest(url);

      const response = await GET(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.position).toBe(0);
      expect(data.completed).toBe(false);
      expect(data.totalWatchTime).toBe(0);
    });

    it("returns 400 when userId is missing", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/progress`
      );
      const request = new NextRequest(url);

      const response = await GET(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe("User ID is required");
    });
  });

  describe("POST", () => {
    it("creates new watch progress", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/progress`
      );
      const request = new NextRequest(url, {
        method: "POST",
        body: JSON.stringify({
          userId,
          lastWatchedPosition: 120,
          totalWatchTime: 120,
          completed: false,
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.progress.position).toBe(120);
      expect(data.progress.totalWatchTime).toBe(120);
      expect(data.progress.completed).toBe(false);
    });

    it("updates existing watch progress", async () => {
      // First, create progress
      const createUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/progress`
      );
      const createRequest = new NextRequest(createUrl, {
        method: "POST",
        body: JSON.stringify({
          userId,
          lastWatchedPosition: 100,
          totalWatchTime: 100,
          completed: false,
        }),
      });

      await POST(createRequest, { params: { sessionId } });

      // Then, update it
      const updateUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/progress`
      );
      const updateRequest = new NextRequest(updateUrl, {
        method: "POST",
        body: JSON.stringify({
          userId,
          lastWatchedPosition: 200,
          totalWatchTime: 200,
          completed: false,
        }),
      });

      const response = await POST(updateRequest, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.progress.position).toBe(200);
      expect(data.progress.totalWatchTime).toBe(200);
    });

    it("keeps higher totalWatchTime", async () => {
      // Create with high watch time
      const createUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/progress`
      );
      const createRequest = new NextRequest(createUrl, {
        method: "POST",
        body: JSON.stringify({
          userId: "user-2",
          lastWatchedPosition: 300,
          totalWatchTime: 300,
          completed: false,
        }),
      });

      await POST(createRequest, { params: { sessionId } });

      // Try to update with lower watch time
      const updateUrl = new URL(
        `http://localhost:3000/api/training/${sessionId}/progress`
      );
      const updateRequest = new NextRequest(updateUrl, {
        method: "POST",
        body: JSON.stringify({
          userId: "user-2",
          lastWatchedPosition: 100,
          totalWatchTime: 100,
          completed: false,
        }),
      });

      const response = await POST(updateRequest, { params: { sessionId } });
      const data = await response.json();

      expect(data.progress.totalWatchTime).toBe(300); // Should keep higher value
    });

    it("marks video as completed", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/progress`
      );
      const request = new NextRequest(url, {
        method: "POST",
        body: JSON.stringify({
          userId: "user-3",
          lastWatchedPosition: 540,
          totalWatchTime: 540,
          completed: true,
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.progress.completed).toBe(true);
    });

    it("returns 400 when userId is missing", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/progress`
      );
      const request = new NextRequest(url, {
        method: "POST",
        body: JSON.stringify({
          lastWatchedPosition: 120,
          totalWatchTime: 120,
          completed: false,
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe("User ID is required");
    });

    it("returns 400 when lastWatchedPosition is invalid", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/progress`
      );
      const request = new NextRequest(url, {
        method: "POST",
        body: JSON.stringify({
          userId,
          lastWatchedPosition: -10,
          totalWatchTime: 120,
          completed: false,
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe("Invalid lastWatchedPosition");
    });

    it("returns 400 when totalWatchTime is invalid", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/progress`
      );
      const request = new NextRequest(url, {
        method: "POST",
        body: JSON.stringify({
          userId,
          lastWatchedPosition: 120,
          totalWatchTime: -50,
          completed: false,
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toBe("Invalid totalWatchTime");
    });

    it("handles zero values correctly", async () => {
      const url = new URL(
        `http://localhost:3000/api/training/${sessionId}/progress`
      );
      const request = new NextRequest(url, {
        method: "POST",
        body: JSON.stringify({
          userId: "user-4",
          lastWatchedPosition: 0,
          totalWatchTime: 0,
          completed: false,
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.progress.position).toBe(0);
      expect(data.progress.totalWatchTime).toBe(0);
    });
  });
});
