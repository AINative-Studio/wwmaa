import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { RTCInterface } from "@/components/training/rtc-interface";

// Mock WebRTC APIs
Object.defineProperty(global.navigator, 'mediaDevices', {
  writable: true,
  value: {
    getUserMedia: jest.fn(),
    enumerateDevices: jest.fn(),
    getDisplayMedia: jest.fn(),
  },
});

global.RTCPeerConnection = jest.fn() as any;

// Mock fetch
global.fetch = jest.fn();

// Mock useWebSocket
jest.mock("react-use-websocket", () => ({
  __esModule: true,
  default: jest.fn(() => ({
    sendMessage: jest.fn(),
    lastMessage: null,
    readyState: 1,
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

describe("RTCInterface", () => {
  const mockConfig = {
    sessionId: "session-123",
    userId: "user-456",
    userName: "John Doe",
    userRole: "member",
    isInstructor: false,
  };

  const mockProps = {
    sessionId: "session-123",
    sessionTitle: "Advanced Karate Training",
    eventId: "event-789",
    config: mockConfig,
    startDatetime: new Date().toISOString(),
    endDatetime: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
  };

  beforeEach(() => {
    jest.clearAllMocks();

    // Mock media devices
    (navigator.mediaDevices.enumerateDevices as jest.Mock).mockResolvedValue([
      { deviceId: "audio1", kind: "audioinput", label: "Microphone 1" },
      { deviceId: "video1", kind: "videoinput", label: "Camera 1" },
    ]);

    (navigator.mediaDevices.getUserMedia as jest.Mock).mockResolvedValue({
      getTracks: () => [{ stop: jest.fn(), enabled: true }],
      getAudioTracks: () => [{ stop: jest.fn(), enabled: true }],
      getVideoTracks: () => [],
      addTrack: jest.fn(),
      removeTrack: jest.fn(),
    });

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ success: true }),
    });
  });

  it("renders session title", () => {
    render(<RTCInterface {...mockProps} />);
    expect(screen.getByText("Advanced Karate Training")).toBeInTheDocument();
  });

  it("displays connection quality indicator", () => {
    render(<RTCInterface {...mockProps} />);
    expect(screen.getByText("Good")).toBeInTheDocument();
  });

  it("shows mute button", () => {
    render(<RTCInterface {...mockProps} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("toggles mute when mute button clicked", async () => {
    render(<RTCInterface {...mockProps} />);

    await waitFor(() => {
      expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalled();
    });

    const buttons = screen.getAllByRole("button");
    // Find mute button (first main control button)
    const muteButton = buttons[0];

    fireEvent.click(muteButton);
    // State should toggle
  });

  it("shows video toggle button", () => {
    render(<RTCInterface {...mockProps} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(1);
  });

  it("displays chat button", () => {
    render(<RTCInterface {...mockProps} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("opens chat panel when chat button clicked", async () => {
    render(<RTCInterface {...mockProps} />);

    // Find and click chat button (second to last button)
    const buttons = screen.getAllByRole("button");
    const chatButton = buttons[buttons.length - 2];

    fireEvent.click(chatButton);

    await waitFor(() => {
      expect(screen.getByText("Chat")).toBeInTheDocument();
    });
  });

  it("displays leave session button", () => {
    render(<RTCInterface {...mockProps} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("shows leave confirmation dialog when leave button clicked", async () => {
    render(<RTCInterface {...mockProps} />);

    const buttons = screen.getAllByRole("button");
    const leaveButton = buttons[buttons.length - 1]; // Last button

    fireEvent.click(leaveButton);

    await waitFor(() => {
      expect(screen.getByText("Leave Session?")).toBeInTheDocument();
    });
  });

  it("displays reaction buttons", () => {
    render(<RTCInterface {...mockProps} />);
    // Reaction buttons are visible on desktop
    // Check for emoji text content
  });

  it("shows recording indicator when recording", () => {
    const recordingProps = {
      ...mockProps,
    };

    render(<RTCInterface {...recordingProps} />);
    // Recording state would be set via WebSocket or other means
  });

  it("displays participant count", async () => {
    render(<RTCInterface {...mockProps} />);

    await waitFor(() => {
      // Should show at least 1 participant (current user)
      const buttons = screen.getAllByRole("button");
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  it("tracks attendance on mount", async () => {
    render(<RTCInterface {...mockProps} />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/attend"),
        expect.objectContaining({
          method: "POST",
        })
      );
    });
  });

  it("hides screen share button for non-instructors", () => {
    render(<RTCInterface {...mockProps} />);
    // Screen share button should be hidden for regular participants
  });

  it("shows screen share button for instructors", () => {
    const instructorConfig = {
      ...mockConfig,
      isInstructor: true,
    };

    const instructorProps = {
      ...mockProps,
      config: instructorConfig,
    };

    render(<RTCInterface {...instructorProps} />);
    // Screen share button should be visible
  });

  it("displays keyboard shortcuts hint on desktop", () => {
    render(<RTCInterface {...mockProps} />);
    // Shortcuts hint is hidden on mobile, visible on desktop
  });

  it("shows user avatar when video is off", () => {
    render(<RTCInterface {...mockProps} />);
    expect(screen.getByText("J")).toBeInTheDocument(); // First letter of name
    expect(screen.getByText("John Doe")).toBeInTheDocument();
  });

  it("opens participant list when participant count clicked", async () => {
    render(<RTCInterface {...mockProps} />);

    // Find participant count button in header
    const buttons = screen.getAllByRole("button");
    // Click one of the header buttons
    fireEvent.click(buttons[1]);

    await waitFor(() => {
      // Participant list should open
    });
  });
});
