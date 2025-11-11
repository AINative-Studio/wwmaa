import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { EventSession } from "@/components/events/event-session";

// Mock fetch
global.fetch = jest.fn();

describe("EventSession", () => {
  const mockProps = {
    eventId: "event-123",
    sessionId: "session-456",
    sessionTitle: "Advanced Karate Training",
    startDatetime: new Date(Date.now() + 5 * 60 * 1000).toISOString(), // 5 minutes from now
    endDatetime: new Date(Date.now() + 65 * 60 * 1000).toISOString(),
    isVirtual: true,
    requiresPayment: true,
    registrationFee: 25.0,
    currentUserStatus: {
      isAuthenticated: true,
      hasPaid: true,
      hasAcceptedTerms: false,
    },
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ success: true }),
    });
  });

  it("renders session information correctly", () => {
    render(<EventSession {...mockProps} />);
    expect(screen.getByText("Advanced Karate Training")).toBeInTheDocument();
    expect(screen.getByText("Live Training Session")).toBeInTheDocument();
  });

  it("shows countdown timer", () => {
    render(<EventSession {...mockProps} />);
    expect(screen.getByText(/Joining Available|Starts in/)).toBeInTheDocument();
  });

  it("displays authentication status", () => {
    render(<EventSession {...mockProps} />);
    expect(screen.getByText("Authenticated")).toBeInTheDocument();
  });

  it("displays payment status when required", () => {
    render(<EventSession {...mockProps} />);
    expect(screen.getByText(/Payment Confirmed/)).toBeInTheDocument();
  });

  it("shows terms acceptance required", () => {
    render(<EventSession {...mockProps} />);
    expect(screen.getByText("Terms Acceptance Required")).toBeInTheDocument();
  });

  it("enables join button 10 minutes before start", () => {
    const startTime = new Date(Date.now() + 5 * 60 * 1000).toISOString();
    const props = {
      ...mockProps,
      startDatetime: startTime,
    };
    render(<EventSession {...props} />);

    const joinButton = screen.getByRole("button", { name: /Join Session/i });
    expect(joinButton).toBeInTheDocument();
  });

  it("redirects to login if not authenticated", () => {
    const props = {
      ...mockProps,
      currentUserStatus: {
        isAuthenticated: false,
        hasPaid: false,
        hasAcceptedTerms: false,
      },
    };

    const mockLocation = { href: "" };
    Object.defineProperty(window, "location", {
      writable: true,
      value: mockLocation,
    });

    render(<EventSession {...props} />);
    const joinButton = screen.getByRole("button", { name: /Login to Join/i });
    fireEvent.click(joinButton);

    expect(mockLocation.href).toContain("/login");
  });

  it("redirects to checkout if payment required and not paid", () => {
    const props = {
      ...mockProps,
      currentUserStatus: {
        isAuthenticated: true,
        hasPaid: false,
        hasAcceptedTerms: false,
      },
    };

    const mockLocation = { href: "" };
    Object.defineProperty(window, "location", {
      writable: true,
      value: mockLocation,
    });

    render(<EventSession {...props} />);
    const joinButton = screen.getByRole("button", { name: /Complete Payment/i });
    fireEvent.click(joinButton);

    expect(mockLocation.href).toContain("/checkout");
  });

  it("shows terms dialog when terms not accepted", () => {
    const startTime = new Date(Date.now() + 5 * 60 * 1000).toISOString();
    const props = {
      ...mockProps,
      startDatetime: startTime,
    };

    render(<EventSession {...props} />);
    const joinButton = screen.getByRole("button", { name: /Join Session/i });
    fireEvent.click(joinButton);

    expect(screen.getByText("Terms and Conditions")).toBeInTheDocument();
  });

  it("accepts terms and joins session", async () => {
    const startTime = new Date(Date.now() + 5 * 60 * 1000).toISOString();
    const props = {
      ...mockProps,
      startDatetime: startTime,
    };

    const mockLocation = { href: "" };
    Object.defineProperty(window, "location", {
      writable: true,
      value: mockLocation,
    });

    render(<EventSession {...props} />);

    // Click join button to open terms dialog
    const joinButton = screen.getByRole("button", { name: /Join Session/i });
    fireEvent.click(joinButton);

    // Accept terms checkbox
    const checkbox = screen.getByRole("checkbox");
    fireEvent.click(checkbox);

    // Click accept button
    const acceptButton = screen.getByRole("button", { name: /Accept & Join Session/i });
    fireEvent.click(acceptButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/accept-terms"),
        expect.any(Object)
      );
    });
  });

  it("displays session already started message", () => {
    const startTime = new Date(Date.now() - 1000).toISOString(); // Started 1 second ago
    const props = {
      ...mockProps,
      startDatetime: startTime,
    };

    render(<EventSession {...props} />);
    expect(screen.getByText("Session Started")).toBeInTheDocument();
  });

  it("formats countdown correctly for hours and minutes", () => {
    const startTime = new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString(); // 2 hours
    const props = {
      ...mockProps,
      startDatetime: startTime,
    };

    render(<EventSession {...props} />);
    expect(screen.getByText(/\d+h \d+m \d+s/)).toBeInTheDocument();
  });

  it("shows payment fee correctly", () => {
    render(<EventSession {...mockProps} />);
    expect(screen.getByText(/\$25.00/)).toBeInTheDocument();
  });
});
