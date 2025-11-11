import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { BookmarksPanel } from "@/components/training/bookmarks-panel";

// Mock useToast
jest.mock("@/components/ui/use-toast", () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

// Mock fetch
global.fetch = jest.fn();

const mockBookmarks = [
  {
    id: "bookmark-1",
    sessionId: "test-session-1",
    userId: "user-123",
    timestamp: 120,
    note: "Important concept here",
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-01T00:00:00Z",
  },
  {
    id: "bookmark-2",
    sessionId: "test-session-1",
    userId: "user-123",
    timestamp: 300,
    note: "Remember to review this part",
    createdAt: "2024-01-01T00:00:00Z",
    updatedAt: "2024-01-01T00:00:00Z",
  },
];

describe("BookmarksPanel", () => {
  const defaultProps = {
    sessionId: "test-session-1",
    userId: "user-123",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ bookmarks: mockBookmarks }),
    });
  });

  it("renders the bookmarks panel", () => {
    render(<BookmarksPanel {...defaultProps} />);
    expect(screen.getByText("Bookmarks")).toBeInTheDocument();
  });

  it("loads bookmarks on mount", async () => {
    render(<BookmarksPanel {...defaultProps} />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining(`/api/training/${defaultProps.sessionId}/bookmarks`)
      );
    });
  });

  it("displays bookmarks", async () => {
    render(<BookmarksPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Important concept here")).toBeInTheDocument();
      expect(screen.getByText("Remember to review this part")).toBeInTheDocument();
    });
  });

  it("displays bookmark timestamps", async () => {
    render(<BookmarksPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("2:00")).toBeInTheDocument(); // 120 seconds
      expect(screen.getByText("5:00")).toBeInTheDocument(); // 300 seconds
    });
  });

  it("shows empty state when no bookmarks", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ bookmarks: [] }),
    });

    render(<BookmarksPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("No bookmarks yet")).toBeInTheDocument();
    });
  });

  it("opens add bookmark dialog", async () => {
    render(<BookmarksPanel {...defaultProps} />);

    const addButton = screen.getByText("Add");
    await userEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText("Add Bookmark")).toBeInTheDocument();
    });
  });

  it("creates a new bookmark", async () => {
    const mockNewBookmark = {
      id: "bookmark-3",
      sessionId: "test-session-1",
      userId: "user-123",
      timestamp: 150,
      note: "New bookmark note",
      createdAt: "2024-01-01T00:00:00Z",
      updatedAt: "2024-01-01T00:00:00Z",
    };

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ bookmarks: mockBookmarks }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ bookmark: mockNewBookmark }),
      });

    // Simulate time update
    const timeUpdateEvent = new CustomEvent("vod-time-update", {
      detail: { currentTime: 150 },
    });
    window.dispatchEvent(timeUpdateEvent);

    render(<BookmarksPanel {...defaultProps} />);

    const addButton = screen.getByText("Add");
    await userEvent.click(addButton);

    const noteInput = screen.getByPlaceholderText(/add a note/i);
    await userEvent.type(noteInput, "New bookmark note");

    const submitButton = screen.getByText("Add Bookmark");
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining("/bookmarks"),
        expect.objectContaining({
          method: "POST",
          body: expect.stringContaining("New bookmark note"),
        })
      );
    });
  });

  it("opens edit bookmark dialog", async () => {
    render(<BookmarksPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Important concept here")).toBeInTheDocument();
    });

    const editButtons = screen.getAllByRole("button", { name: "" }).filter(
      (btn) => btn.querySelector("svg")?.classList.contains("lucide-edit-2")
    );

    if (editButtons.length > 0) {
      await userEvent.click(editButtons[0]);

      await waitFor(() => {
        expect(screen.getByText("Edit Bookmark")).toBeInTheDocument();
      });
    }
  });

  it("updates a bookmark", async () => {
    const updatedBookmark = {
      ...mockBookmarks[0],
      note: "Updated note",
    };

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ bookmarks: mockBookmarks }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ bookmark: updatedBookmark }),
      });

    render(<BookmarksPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Important concept here")).toBeInTheDocument();
    });

    const editButtons = screen.getAllByRole("button", { name: "" }).filter(
      (btn) => btn.querySelector("svg")?.classList.contains("lucide-edit-2")
    );

    if (editButtons.length > 0) {
      await userEvent.click(editButtons[0]);

      const noteInput = screen.getByPlaceholderText(/add a note/i);
      await userEvent.clear(noteInput);
      await userEvent.type(noteInput, "Updated note");

      const updateButton = screen.getByText("Update Bookmark");
      await userEvent.click(updateButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining(`/bookmarks/${mockBookmarks[0].id}`),
          expect.objectContaining({
            method: "PUT",
          })
        );
      });
    }
  });

  it("opens delete confirmation dialog", async () => {
    render(<BookmarksPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Important concept here")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole("button", { name: "" }).filter(
      (btn) => btn.querySelector("svg")?.classList.contains("lucide-trash-2")
    );

    if (deleteButtons.length > 0) {
      await userEvent.click(deleteButtons[0]);

      await waitFor(() => {
        expect(screen.getByText("Delete Bookmark?")).toBeInTheDocument();
      });
    }
  });

  it("deletes a bookmark", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ bookmarks: mockBookmarks }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true }),
      });

    render(<BookmarksPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("Important concept here")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole("button", { name: "" }).filter(
      (btn) => btn.querySelector("svg")?.classList.contains("lucide-trash-2")
    );

    if (deleteButtons.length > 0) {
      await userEvent.click(deleteButtons[0]);

      const confirmButton = screen.getByRole("button", { name: /delete/i });
      await userEvent.click(confirmButton);

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining(`/bookmarks/${mockBookmarks[0].id}`),
          expect.objectContaining({
            method: "DELETE",
          })
        );
      });
    }
  });

  it("seeks to bookmark timestamp when clicked", async () => {
    const mockDispatchEvent = jest.spyOn(window, "dispatchEvent");

    render(<BookmarksPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("2:00")).toBeInTheDocument();
    });

    const timestampButton = screen.getByText("2:00");
    await userEvent.click(timestampButton);

    expect(mockDispatchEvent).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "vod-seek-to",
      })
    );

    mockDispatchEvent.mockRestore();
  });

  it("updates current time from video events", () => {
    render(<BookmarksPanel {...defaultProps} />);

    const timeUpdateEvent = new CustomEvent("vod-time-update", {
      detail: { currentTime: 180 },
    });
    window.dispatchEvent(timeUpdateEvent);

    // Current time should be updated (verified when opening add dialog)
    const addButton = screen.getByText("Add");
    fireEvent.click(addButton);

    // Should show current time in dialog
    expect(screen.getByText("3:00")).toBeInTheDocument();
  });

  it("formats time correctly for hours", async () => {
    const longBookmark = {
      ...mockBookmarks[0],
      timestamp: 3661, // 1:01:01
    };

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ bookmarks: [longBookmark] }),
    });

    render(<BookmarksPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("1:01:01")).toBeInTheDocument();
    });
  });

  it("handles loading state", () => {
    (global.fetch as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<BookmarksPanel {...defaultProps} />);

    expect(screen.getByText("Loading bookmarks...")).toBeInTheDocument();
  });

  it("handles error when loading bookmarks", async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error("Failed to load"));

    render(<BookmarksPanel {...defaultProps} />);

    await waitFor(() => {
      expect(screen.getByText("No bookmarks yet")).toBeInTheDocument();
    });
  });

  it("closes dialog when cancel is clicked", async () => {
    render(<BookmarksPanel {...defaultProps} />);

    const addButton = screen.getByText("Add");
    await userEvent.click(addButton);

    const cancelButton = screen.getByText("Cancel");
    await userEvent.click(cancelButton);

    await waitFor(() => {
      expect(screen.queryByText("Add Bookmark")).not.toBeInTheDocument();
    });
  });

  it("sorts bookmarks by timestamp", async () => {
    const unsortedBookmarks = [
      { ...mockBookmarks[1] },
      { ...mockBookmarks[0] },
    ];

    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ bookmarks: unsortedBookmarks }),
    });

    render(<BookmarksPanel {...defaultProps} />);

    await waitFor(() => {
      const timestamps = screen.getAllByText(/\d+:\d{2}/);
      // First timestamp should be 2:00 (120s), second should be 5:00 (300s)
      expect(timestamps[0]).toHaveTextContent("2:00");
      expect(timestamps[1]).toHaveTextContent("5:00");
    });
  });
});
