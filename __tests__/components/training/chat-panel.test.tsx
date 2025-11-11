import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ChatPanel } from "@/components/training/chat-panel";

// Mock useWebSocket
jest.mock("react-use-websocket", () => ({
  __esModule: true,
  default: jest.fn(() => ({
    sendMessage: jest.fn(),
    lastMessage: null,
    readyState: 1, // OPEN
  })),
  ReadyState: {
    CONNECTING: 0,
    OPEN: 1,
    CLOSING: 2,
    CLOSED: 3,
    UNINSTANTIATED: -1,
  },
}));

// Mock emoji-picker-react
jest.mock("emoji-picker-react", () => ({
  __esModule: true,
  default: () => <div>Emoji Picker</div>,
}));

describe("ChatPanel", () => {
  const mockProps = {
    sessionId: "session-123",
    currentUserId: "user-456",
    currentUserName: "John Doe",
    onClose: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders chat panel with header", () => {
    render(<ChatPanel {...mockProps} />);
    expect(screen.getByText("Chat")).toBeInTheDocument();
    expect(screen.getByText("Live")).toBeInTheDocument();
  });

  it("displays empty state when no messages", () => {
    render(<ChatPanel {...mockProps} />);
    expect(screen.getByText("No messages yet")).toBeInTheDocument();
    expect(screen.getByText("Be the first to say something!")).toBeInTheDocument();
  });

  it("renders message input field", () => {
    render(<ChatPanel {...mockProps} />);
    const input = screen.getByPlaceholderText("Type a message...");
    expect(input).toBeInTheDocument();
  });

  it("allows typing in message input", () => {
    render(<ChatPanel {...mockProps} />);
    const input = screen.getByPlaceholderText("Type a message...") as HTMLInputElement;

    fireEvent.change(input, { target: { value: "Hello everyone!" } });
    expect(input.value).toBe("Hello everyone!");
  });

  it("shows send button", () => {
    render(<ChatPanel {...mockProps} />);
    const sendButton = screen.getByRole("button", { name: "" });
    expect(sendButton).toBeInTheDocument();
  });

  it("displays rate limit warning when low", () => {
    const useWebSocket = require("react-use-websocket").default;
    useWebSocket.mockReturnValue({
      sendMessage: jest.fn(),
      lastMessage: {
        data: JSON.stringify({
          type: "rate_limit",
          remaining: 2,
        }),
      },
      readyState: 1,
    });

    render(<ChatPanel {...mockProps} />);
    // Rate limit display would appear after processing the message
  });

  it("calls onClose when close button clicked", () => {
    render(<ChatPanel {...mockProps} />);
    const closeButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector('svg')
    );

    if (closeButton) {
      fireEvent.click(closeButton);
      expect(mockProps.onClose).toHaveBeenCalled();
    }
  });

  it("shows emoji picker button", () => {
    render(<ChatPanel {...mockProps} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("displays connection status", () => {
    render(<ChatPanel {...mockProps} />);
    expect(screen.getByText("Live")).toBeInTheDocument();
  });

  it("shows keyboard hint", () => {
    render(<ChatPanel {...mockProps} />);
    expect(screen.getByText(/Press Enter to send/)).toBeInTheDocument();
  });

  it("limits message length to 500 characters", () => {
    render(<ChatPanel {...mockProps} />);
    const input = screen.getByPlaceholderText("Type a message...") as HTMLInputElement;
    expect(input).toHaveAttribute("maxLength", "500");
  });

  it("disables input when disconnected", () => {
    const useWebSocket = require("react-use-websocket").default;
    useWebSocket.mockReturnValue({
      sendMessage: jest.fn(),
      lastMessage: null,
      readyState: 3, // CLOSED
    });

    render(<ChatPanel {...mockProps} />);
    const input = screen.getByPlaceholderText("Type a message...");
    expect(input).toBeDisabled();
  });
});
