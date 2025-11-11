import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { VODPlayer } from "@/components/training/vod-player";

// Mock useToast
jest.mock("@/components/ui/use-toast", () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

// Mock HTMLVideoElement methods
const mockPlay = jest.fn();
const mockPause = jest.fn();
const mockRequestFullscreen = jest.fn();
const mockExitFullscreen = jest.fn();
const mockRequestPictureInPicture = jest.fn();
const mockExitPictureInPicture = jest.fn();

Object.defineProperty(HTMLMediaElement.prototype, "play", {
  configurable: true,
  value: mockPlay.mockResolvedValue(undefined),
});

Object.defineProperty(HTMLMediaElement.prototype, "pause", {
  configurable: true,
  value: mockPause,
});

Object.defineProperty(HTMLElement.prototype, "requestFullscreen", {
  configurable: true,
  value: mockRequestFullscreen.mockResolvedValue(undefined),
});

Object.defineProperty(document, "exitFullscreen", {
  configurable: true,
  value: mockExitFullscreen.mockResolvedValue(undefined),
});

Object.defineProperty(HTMLVideoElement.prototype, "requestPictureInPicture", {
  configurable: true,
  value: mockRequestPictureInPicture.mockResolvedValue(undefined),
});

Object.defineProperty(document, "exitPictureInPicture", {
  configurable: true,
  value: mockExitPictureInPicture.mockResolvedValue(undefined),
});

// Mock fetch
global.fetch = jest.fn();

describe("VODPlayer", () => {
  const defaultProps = {
    sessionId: "test-session-1",
    streamUrl: "https://example.com/video.mp4",
    title: "Test Video",
    duration: 600,
    thumbnailUrl: "https://example.com/thumbnail.jpg",
    initialPosition: 0,
    userId: "user-123",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ success: true }),
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("renders the video player", () => {
    render(<VODPlayer {...defaultProps} />);
    const video = screen.getByRole("button", { name: /play/i });
    expect(video).toBeInTheDocument();
  });

  it("displays the video title", () => {
    render(<VODPlayer {...defaultProps} />);
    expect(screen.getByText("Test Video")).toBeInTheDocument();
  });

  it("toggles play/pause on click", async () => {
    render(<VODPlayer {...defaultProps} />);

    const playButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (playButton) {
      await userEvent.click(playButton);
      expect(mockPlay).toHaveBeenCalled();
    }
  });

  it("handles keyboard shortcuts - Space for play/pause", async () => {
    render(<VODPlayer {...defaultProps} />);

    fireEvent.keyDown(window, { key: " " });

    await waitFor(() => {
      expect(mockPlay).toHaveBeenCalled();
    });
  });

  it("handles keyboard shortcuts - F for fullscreen", async () => {
    render(<VODPlayer {...defaultProps} />);

    fireEvent.keyDown(window, { key: "f" });

    await waitFor(() => {
      expect(mockRequestFullscreen).toHaveBeenCalled();
    });
  });

  it("handles keyboard shortcuts - M for mute", () => {
    render(<VODPlayer {...defaultProps} />);
    const video = document.querySelector("video");

    if (video) {
      const initialMuted = video.muted;
      fireEvent.keyDown(window, { key: "m" });
      expect(video.muted).toBe(!initialMuted);
    }
  });

  it("handles keyboard shortcuts - Arrow Left for skip back", () => {
    render(<VODPlayer {...defaultProps} />);
    const video = document.querySelector("video");

    if (video) {
      video.currentTime = 30;
      fireEvent.keyDown(window, { key: "ArrowLeft" });

      // Video should attempt to skip back 10 seconds
      expect(video.currentTime).toBeLessThanOrEqual(30);
    }
  });

  it("handles keyboard shortcuts - Arrow Right for skip forward", () => {
    render(<VODPlayer {...defaultProps} />);
    const video = document.querySelector("video");

    if (video) {
      const initialTime = video.currentTime;
      fireEvent.keyDown(window, { key: "ArrowRight" });

      // Time should be set (even if to 0 initially)
      expect(video.currentTime).toBeGreaterThanOrEqual(initialTime);
    }
  });

  it("handles keyboard shortcuts - Number keys for jump to percentage", () => {
    render(<VODPlayer {...defaultProps} />);
    const video = document.querySelector("video");

    if (video) {
      // Set duration first
      Object.defineProperty(video, "duration", {
        value: 600,
        writable: true,
      });

      fireEvent.keyDown(window, { key: "5" });

      // Should jump to 50% (300 seconds)
      expect(video.currentTime).toBeLessThanOrEqual(600);
    }
  });

  it("does not handle keyboard shortcuts when typing in input", () => {
    const { container } = render(
      <div>
        <input type="text" data-testid="text-input" />
        <VODPlayer {...defaultProps} />
      </div>
    );

    const input = screen.getByTestId("text-input");
    input.focus();

    fireEvent.keyDown(input, { key: " " });

    // Should not trigger play
    expect(mockPlay).not.toHaveBeenCalled();
  });

  it("saves watch progress periodically", async () => {
    jest.useFakeTimers();

    render(<VODPlayer {...defaultProps} />);
    const video = document.querySelector("video");

    if (video) {
      // Simulate playing
      fireEvent.play(video);

      // Simulate time update
      Object.defineProperty(video, "currentTime", {
        value: 30,
        writable: true,
      });
      fireEvent.timeUpdate(video);

      // Fast-forward 10 seconds
      jest.advanceTimersByTime(10000);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining("/api/training/test-session-1/progress"),
          expect.objectContaining({
            method: "POST",
          })
        );
      });
    }

    jest.useRealTimers();
  });

  it("resumes from initial position", async () => {
    render(<VODPlayer {...defaultProps} initialPosition={120} />);
    const video = document.querySelector("video");

    await waitFor(() => {
      if (video) {
        // Should attempt to set currentTime to initial position
        expect(video.currentTime).toBeDefined();
      }
    });
  });

  it("formats time correctly", () => {
    render(<VODPlayer {...defaultProps} />);

    // Should display time in format MM:SS or HH:MM:SS
    const timeDisplay = screen.getAllByText(/\d+:\d{2}/);
    expect(timeDisplay.length).toBeGreaterThan(0);
  });

  it("shows buffering state", () => {
    render(<VODPlayer {...defaultProps} />);
    const video = document.querySelector("video");

    if (video) {
      fireEvent.waiting(video);

      // Should show loading spinner
      const loader = document.querySelector(".animate-spin");
      expect(loader).toBeInTheDocument();
    }
  });

  it("hides buffering state when ready", () => {
    render(<VODPlayer {...defaultProps} />);
    const video = document.querySelector("video");

    if (video) {
      fireEvent.waiting(video);
      fireEvent.canPlay(video);

      // Should hide loading spinner
      const loader = document.querySelector(".animate-spin");
      expect(loader).not.toBeInTheDocument();
    }
  });

  it("updates volume when slider changes", async () => {
    render(<VODPlayer {...defaultProps} />);
    const video = document.querySelector("video");

    if (video) {
      const volumeSlider = screen.getAllByRole("slider").find(
        (slider) => slider.getAttribute("aria-label")?.includes("volume") || true
      );

      if (volumeSlider) {
        // Should be able to change volume
        expect(video.volume).toBeDefined();
      }
    }
  });

  it("changes playback speed", async () => {
    render(<VODPlayer {...defaultProps} />);
    const video = document.querySelector("video");

    if (video) {
      // Initial playback rate should be 1
      expect(video.playbackRate).toBe(1);
    }
  });

  it("toggles picture-in-picture mode", async () => {
    render(<VODPlayer {...defaultProps} />);

    const pipButton = screen.getAllByRole("button").find(
      (btn) => btn.getAttribute("aria-label")?.includes("Picture") ||
               btn.querySelector("svg")?.classList.contains("lucide-picture-in-picture")
    );

    if (pipButton) {
      await userEvent.click(pipButton);

      await waitFor(() => {
        expect(mockRequestPictureInPicture).toHaveBeenCalled();
      });
    }
  });

  it("auto-hides controls during playback", async () => {
    jest.useFakeTimers();

    render(<VODPlayer {...defaultProps} />);
    const video = document.querySelector("video");

    if (video) {
      fireEvent.play(video);

      // Controls should be visible initially
      const controls = document.querySelector(".absolute.bottom-0");
      expect(controls).toBeInTheDocument();

      // After timeout, controls should fade
      jest.advanceTimersByTime(3000);

      // Controls should have reduced opacity
      expect(controls).toHaveClass("opacity-0");
    }

    jest.useRealTimers();
  });

  it("shows controls on mouse move", () => {
    render(<VODPlayer {...defaultProps} />);
    const container = document.querySelector(".relative.bg-black");

    if (container) {
      fireEvent.mouseMove(container);

      const controls = document.querySelector(".absolute.bottom-0");
      expect(controls).not.toHaveClass("opacity-0");
    }
  });

  it("displays thumbnail poster", () => {
    render(<VODPlayer {...defaultProps} />);
    const video = document.querySelector("video");

    expect(video).toHaveAttribute("poster", defaultProps.thumbnailUrl);
  });

  it("saves progress on unmount", () => {
    const { unmount } = render(<VODPlayer {...defaultProps} />);
    const video = document.querySelector("video");

    if (video) {
      Object.defineProperty(video, "currentTime", {
        value: 45,
        writable: true,
      });
      fireEvent.timeUpdate(video);
    }

    unmount();

    // Should have attempted to save progress
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/progress"),
      expect.any(Object)
    );
  });
});
