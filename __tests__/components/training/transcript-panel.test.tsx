import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { TranscriptPanel } from "@/components/training/transcript-panel";

// Mock useToast
jest.mock("@/components/ui/use-toast", () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

// Mock VTT content
const mockVTTContent = `WEBVTT

00:00:00.000 --> 00:00:05.000
Welcome to this training session.

00:00:05.000 --> 00:00:10.000
Today we will cover advanced techniques.

00:00:10.000 --> 00:00:15.000
Let's start with the fundamentals.

00:00:15.000 --> 00:00:20.000
This is an important concept to understand.`;

// Mock fetch
global.fetch = jest.fn();

describe("TranscriptPanel", () => {
  const defaultProps = {
    sessionId: "test-session-1",
    transcriptUrl: "https://example.com/transcript.vtt",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      text: async () => mockVTTContent,
    });
  });

  it("renders the transcript panel collapsed by default", () => {
    render(<TranscriptPanel {...defaultProps} />);
    expect(screen.getByText("Transcript")).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/search/i)).not.toBeInTheDocument();
  });

  it("expands when toggle button is clicked", async () => {
    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getByRole("button", { name: /chevron/i });
    await userEvent.click(toggleButton);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search transcript/i)).toBeInTheDocument();
    });
  });

  it("loads transcript when expanded", async () => {
    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (toggleButton) {
      await userEvent.click(toggleButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(defaultProps.transcriptUrl);
      });
    }
  });

  it("displays transcript cues", async () => {
    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (toggleButton) {
      await userEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText("Welcome to this training session.")).toBeInTheDocument();
        expect(screen.getByText("Today we will cover advanced techniques.")).toBeInTheDocument();
      });
    }
  });

  it("displays timestamps for each cue", async () => {
    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (toggleButton) {
      await userEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText("0:00")).toBeInTheDocument();
        expect(screen.getByText("0:05")).toBeInTheDocument();
      });
    }
  });

  it("filters transcript based on search query", async () => {
    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (toggleButton) {
      await userEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText("Welcome to this training session.")).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search transcript/i);
      await userEvent.type(searchInput, "advanced");

      await waitFor(() => {
        expect(screen.getByText("Today we will cover advanced techniques.")).toBeInTheDocument();
        expect(screen.queryByText("Welcome to this training session.")).not.toBeInTheDocument();
      });
    }
  });

  it("displays search results count", async () => {
    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (toggleButton) {
      await userEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText("Welcome to this training session.")).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search transcript/i);
      await userEvent.type(searchInput, "training");

      await waitFor(() => {
        expect(screen.getByText(/found 1 result/i)).toBeInTheDocument();
      });
    }
  });

  it("shows 'no results found' when search has no matches", async () => {
    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (toggleButton) {
      await userEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText("Welcome to this training session.")).toBeInTheDocument();
      });

      const searchInput = screen.getByPlaceholderText(/search transcript/i);
      await userEvent.type(searchInput, "nonexistent");

      await waitFor(() => {
        expect(screen.getByText("No results found")).toBeInTheDocument();
      });
    }
  });

  it("dispatches seek event when cue is clicked", async () => {
    const mockDispatchEvent = jest.spyOn(window, "dispatchEvent");

    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (toggleButton) {
      await userEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText("Welcome to this training session.")).toBeInTheDocument();
      });

      const firstCue = screen.getByText("Welcome to this training session.");
      await userEvent.click(firstCue);

      expect(mockDispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: "vod-seek-to",
        })
      );
    }

    mockDispatchEvent.mockRestore();
  });

  it("highlights current cue based on video time", async () => {
    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (toggleButton) {
      await userEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText("Welcome to this training session.")).toBeInTheDocument();
      });

      // Simulate time update event
      const timeUpdateEvent = new CustomEvent("vod-time-update", {
        detail: { currentTime: 7 },
      });
      window.dispatchEvent(timeUpdateEvent);

      await waitFor(() => {
        const activeCue = screen.getByText("Today we will cover advanced techniques.").parentElement;
        expect(activeCue).toHaveClass("bg-blue-50");
      });
    }
  });

  it("downloads transcript", async () => {
    const mockCreateElement = jest.spyOn(document, "createElement");
    const mockClick = jest.fn();
    const mockAppendChild = jest.spyOn(document.body, "appendChild");
    const mockRemoveChild = jest.spyOn(document.body, "removeChild");

    mockCreateElement.mockImplementation((tag) => {
      const element = document.createElement(tag);
      if (tag === "a") {
        element.click = mockClick;
      }
      return element;
    });

    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (toggleButton) {
      await userEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText("Download")).toBeInTheDocument();
      });

      const downloadButton = screen.getByText("Download");
      await userEvent.click(downloadButton);

      expect(mockClick).toHaveBeenCalled();
      expect(mockAppendChild).toHaveBeenCalled();
      expect(mockRemoveChild).toHaveBeenCalled();
    }

    mockCreateElement.mockRestore();
    mockAppendChild.mockRestore();
    mockRemoveChild.mockRestore();
  });

  it("handles transcript loading error", async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error("Failed to load"));

    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (toggleButton) {
      await userEvent.click(toggleButton);

      await waitFor(() => {
        expect(screen.getByText("No transcript available")).toBeInTheDocument();
      });
    }
  });

  it("parses VTT timestamps correctly", async () => {
    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (toggleButton) {
      await userEvent.click(toggleButton);

      await waitFor(() => {
        // Should format 0:00:00 as "0:00"
        expect(screen.getByText("0:00")).toBeInTheDocument();
        // Should format 0:00:05 as "0:05"
        expect(screen.getByText("0:05")).toBeInTheDocument();
        // Should format 0:00:10 as "0:10"
        expect(screen.getByText("0:10")).toBeInTheDocument();
      });
    }
  });

  it("only loads transcript once", async () => {
    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (toggleButton) {
      await userEvent.click(toggleButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(1);
      });

      // Close and reopen
      await userEvent.click(toggleButton);
      await userEvent.click(toggleButton);

      // Should still only be called once
      expect(global.fetch).toHaveBeenCalledTimes(1);
    }
  });

  it("clears search query", async () => {
    render(<TranscriptPanel {...defaultProps} />);

    const toggleButton = screen.getAllByRole("button").find(
      (btn) => btn.querySelector("svg")
    );

    if (toggleButton) {
      await userEvent.click(toggleButton);

      const searchInput = screen.getByPlaceholderText(/search transcript/i);
      await userEvent.type(searchInput, "test");
      await userEvent.clear(searchInput);

      await waitFor(() => {
        // All cues should be visible again
        expect(screen.getByText("Welcome to this training session.")).toBeInTheDocument();
        expect(screen.getByText("Today we will cover advanced techniques.")).toBeInTheDocument();
      });
    }
  });
});
