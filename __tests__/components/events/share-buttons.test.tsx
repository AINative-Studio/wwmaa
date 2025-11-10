/**
 * Tests for ShareButtons Component
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ShareButtons } from "@/components/events/share-buttons";

// Mock useToast hook
jest.mock("@/components/ui/use-toast", () => ({
  useToast: () => ({
    toast: jest.fn(),
  }),
}));

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn().mockResolvedValue(undefined),
  },
});

describe("ShareButtons", () => {
  const defaultProps = {
    title: "Judo Seminar",
    description: "Advanced Judo techniques seminar",
    url: "https://wwmaa.ainative.studio/events/123",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    delete (navigator as any).share; // Remove native share API for desktop tests
  });

  it("renders share button", () => {
    render(<ShareButtons {...defaultProps} />);
    expect(screen.getByText("Share")).toBeInTheDocument();
  });

  it("opens dropdown menu when clicked", async () => {
    render(<ShareButtons {...defaultProps} />);

    const button = screen.getByText("Share");
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText("Twitter")).toBeInTheDocument();
      expect(screen.getByText("Facebook")).toBeInTheDocument();
      expect(screen.getByText("LinkedIn")).toBeInTheDocument();
      expect(screen.getByText("Copy Link")).toBeInTheDocument();
    });
  });

  it("opens Twitter share window with correct URL", async () => {
    const windowOpenSpy = jest.spyOn(window, "open").mockImplementation();

    render(<ShareButtons {...defaultProps} />);

    const button = screen.getByText("Share");
    fireEvent.click(button);

    await waitFor(() => {
      const twitterOption = screen.getByText("Twitter");
      fireEvent.click(twitterOption);
    });

    expect(windowOpenSpy).toHaveBeenCalled();
    const calledUrl = windowOpenSpy.mock.calls[0][0] as string;
    expect(calledUrl).toContain("twitter.com/intent/tweet");
    expect(calledUrl).toContain(encodeURIComponent(defaultProps.title));

    windowOpenSpy.mockRestore();
  });

  it("opens Facebook share window with correct URL", async () => {
    const windowOpenSpy = jest.spyOn(window, "open").mockImplementation();

    render(<ShareButtons {...defaultProps} />);

    const button = screen.getByText("Share");
    fireEvent.click(button);

    await waitFor(() => {
      const facebookOption = screen.getByText("Facebook");
      fireEvent.click(facebookOption);
    });

    expect(windowOpenSpy).toHaveBeenCalled();
    const calledUrl = windowOpenSpy.mock.calls[0][0] as string;
    expect(calledUrl).toContain("facebook.com/sharer");

    windowOpenSpy.mockRestore();
  });

  it("opens LinkedIn share window with correct URL", async () => {
    const windowOpenSpy = jest.spyOn(window, "open").mockImplementation();

    render(<ShareButtons {...defaultProps} />);

    const button = screen.getByText("Share");
    fireEvent.click(button);

    await waitFor(() => {
      const linkedInOption = screen.getByText("LinkedIn");
      fireEvent.click(linkedInOption);
    });

    expect(windowOpenSpy).toHaveBeenCalled();
    const calledUrl = windowOpenSpy.mock.calls[0][0] as string;
    expect(calledUrl).toContain("linkedin.com/sharing");

    windowOpenSpy.mockRestore();
  });

  it("copies link to clipboard when copy option clicked", async () => {
    render(<ShareButtons {...defaultProps} />);

    const button = screen.getByText("Share");
    fireEvent.click(button);

    await waitFor(() => {
      const copyOption = screen.getByText("Copy Link");
      fireEvent.click(copyOption);
    });

    expect(navigator.clipboard.writeText).toHaveBeenCalled();
  });

  it("shows copied confirmation after copying link", async () => {
    render(<ShareButtons {...defaultProps} />);

    const button = screen.getByText("Share");
    fireEvent.click(button);

    await waitFor(() => {
      const copyOption = screen.getByText("Copy Link");
      fireEvent.click(copyOption);
    });

    await waitFor(() => {
      expect(screen.getByText("Copied!")).toBeInTheDocument();
    });
  });

  it("uses native share API when available on mobile", async () => {
    // Mock native share API
    const shareMock = jest.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      share: shareMock,
    });

    render(<ShareButtons {...defaultProps} />);

    const button = screen.getByText("Share");
    fireEvent.click(button);

    expect(shareMock).toHaveBeenCalledWith({
      title: defaultProps.title,
      text: defaultProps.description,
      url: expect.any(String),
    });
  });

  it("handles share cancellation gracefully", async () => {
    // Mock native share API with rejection
    const shareMock = jest.fn().mockRejectedValue(new Error("Share cancelled"));
    Object.assign(navigator, {
      share: shareMock,
    });

    const consoleSpy = jest.spyOn(console, "log").mockImplementation();

    render(<ShareButtons {...defaultProps} />);

    const button = screen.getByText("Share");
    fireEvent.click(button);

    await waitFor(() => {
      expect(shareMock).toHaveBeenCalled();
    });

    consoleSpy.mockRestore();
  });
});
