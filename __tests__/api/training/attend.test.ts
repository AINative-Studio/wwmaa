import { NextRequest } from "next/server";
import { POST, PUT, GET } from "@/app/api/training/[sessionId]/attend/route";

// Mock fetch
global.fetch = jest.fn();

describe("/api/training/[sessionId]/attend", () => {
  const sessionId = "session-123";
  const userId = "user-456";

  beforeEach(() => {
    jest.clearAllMocks();
    process.env.BACKEND_URL = "http://localhost:8000";
  });

  describe("POST - Record attendance", () => {
    it("records attendance successfully", async () => {
      const mockResponse = {
        id: "attendance-789",
        session_id: sessionId,
        user_id: userId,
        joined_at: "2024-01-01T10:00:00Z",
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const request = new NextRequest("http://localhost:3000/api/training/session-123/attend", {
        method: "POST",
        body: JSON.stringify({
          userId,
          joinedAt: "2024-01-01T10:00:00Z",
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(201);
      expect(data.success).toBe(true);
      expect(data.attendance).toEqual(mockResponse);
    });

    it("returns 400 if userId is missing", async () => {
      const request = new NextRequest("http://localhost:3000/api/training/session-123/attend", {
        method: "POST",
        body: JSON.stringify({
          joinedAt: "2024-01-01T10:00:00Z",
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toContain("Missing required fields");
    });

    it("returns 400 if joinedAt is missing", async () => {
      const request = new NextRequest("http://localhost:3000/api/training/session-123/attend", {
        method: "POST",
        body: JSON.stringify({
          userId,
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toContain("Missing required fields");
    });

    it("handles backend errors", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ detail: "Internal server error" }),
      });

      const request = new NextRequest("http://localhost:3000/api/training/session-123/attend", {
        method: "POST",
        body: JSON.stringify({
          userId,
          joinedAt: "2024-01-01T10:00:00Z",
        }),
      });

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(500);
      expect(data.error).toBeTruthy();
    });
  });

  describe("PUT - Update watch time", () => {
    it("updates watch time successfully", async () => {
      const mockResponse = {
        id: "attendance-789",
        session_id: sessionId,
        user_id: userId,
        watch_time: 120,
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const request = new NextRequest("http://localhost:3000/api/training/session-123/attend", {
        method: "PUT",
        body: JSON.stringify({
          userId,
          watchTime: 60,
        }),
      });

      const response = await PUT(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.attendance).toEqual(mockResponse);
    });

    it("returns 400 if userId is missing", async () => {
      const request = new NextRequest("http://localhost:3000/api/training/session-123/attend", {
        method: "PUT",
        body: JSON.stringify({
          watchTime: 60,
        }),
      });

      const response = await PUT(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toContain("Missing required fields");
    });

    it("returns 400 if watchTime is missing", async () => {
      const request = new NextRequest("http://localhost:3000/api/training/session-123/attend", {
        method: "PUT",
        body: JSON.stringify({
          userId,
        }),
      });

      const response = await PUT(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(400);
      expect(data.error).toContain("Missing required fields");
    });
  });

  describe("GET - Fetch attendance", () => {
    it("fetches attendance for specific user", async () => {
      const mockResponse = {
        id: "attendance-789",
        session_id: sessionId,
        user_id: userId,
        joined_at: "2024-01-01T10:00:00Z",
        watch_time: 120,
      };

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const request = new NextRequest(
        `http://localhost:3000/api/training/session-123/attend?userId=${userId}`,
        {
          method: "GET",
        }
      );

      const response = await GET(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data).toEqual(mockResponse);
    });

    it("fetches all attendance for session", async () => {
      const mockResponse = [
        {
          id: "attendance-1",
          session_id: sessionId,
          user_id: "user-1",
          joined_at: "2024-01-01T10:00:00Z",
        },
        {
          id: "attendance-2",
          session_id: sessionId,
          user_id: "user-2",
          joined_at: "2024-01-01T10:05:00Z",
        },
      ];

      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      });

      const request = new NextRequest(
        "http://localhost:3000/api/training/session-123/attend",
        {
          method: "GET",
        }
      );

      const response = await GET(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(Array.isArray(data)).toBe(true);
      expect(data.length).toBe(2);
    });

    it("handles backend errors", async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ detail: "Attendance not found" }),
      });

      const request = new NextRequest(
        `http://localhost:3000/api/training/session-123/attend?userId=${userId}`,
        {
          method: "GET",
        }
      );

      const response = await GET(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(404);
      expect(data.error).toBeTruthy();
    });
  });
});
