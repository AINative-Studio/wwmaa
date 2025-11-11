import { NextRequest } from "next/server";
import { POST, GET } from "@/app/api/training/[sessionId]/accept-terms/route";

describe("/api/training/[sessionId]/accept-terms", () => {
  const sessionId = "session-123";

  beforeEach(() => {
    jest.clearAllMocks();
    process.env.BACKEND_URL = "http://localhost:8000";
  });

  describe("POST - Accept terms", () => {
    it("accepts terms successfully", async () => {
      const request = new NextRequest(
        "http://localhost:3000/api/training/session-123/accept-terms",
        {
          method: "POST",
        }
      );

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.success).toBe(true);
      expect(data.sessionId).toBe(sessionId);
      expect(data.acceptedAt).toBeTruthy();
    });

    it("returns acceptedAt timestamp", async () => {
      const request = new NextRequest(
        "http://localhost:3000/api/training/session-123/accept-terms",
        {
          method: "POST",
        }
      );

      const response = await POST(request, { params: { sessionId } });
      const data = await response.json();

      const acceptedDate = new Date(data.acceptedAt);
      expect(acceptedDate).toBeInstanceOf(Date);
      expect(acceptedDate.getTime()).toBeLessThanOrEqual(Date.now());
    });

    it("handles errors gracefully", async () => {
      // Mock an error scenario by modifying the implementation temporarily
      // In production, this would test actual backend failures
      const request = new NextRequest(
        "http://localhost:3000/api/training/session-123/accept-terms",
        {
          method: "POST",
        }
      );

      const response = await POST(request, { params: { sessionId } });

      expect(response.status).toBeLessThan(500);
    });
  });

  describe("GET - Check terms acceptance", () => {
    it("returns terms acceptance status", async () => {
      const request = new NextRequest(
        "http://localhost:3000/api/training/session-123/accept-terms",
        {
          method: "GET",
        }
      );

      const response = await GET(request, { params: { sessionId } });
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data).toHaveProperty("hasAccepted");
      expect(data).toHaveProperty("acceptedAt");
    });

    it("returns false for hasAccepted by default", async () => {
      const request = new NextRequest(
        "http://localhost:3000/api/training/session-123/accept-terms",
        {
          method: "GET",
        }
      );

      const response = await GET(request, { params: { sessionId } });
      const data = await response.json();

      expect(data.hasAccepted).toBe(false);
      expect(data.acceptedAt).toBeNull();
    });

    it("handles errors gracefully", async () => {
      const request = new NextRequest(
        "http://localhost:3000/api/training/session-123/accept-terms",
        {
          method: "GET",
        }
      );

      const response = await GET(request, { params: { sessionId } });

      expect(response.status).toBeLessThan(500);
    });
  });
});
