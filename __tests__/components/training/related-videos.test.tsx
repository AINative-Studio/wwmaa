import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { RelatedVideos } from "@/components/training/related-videos";

const mockSessions = [
  {
    id: "session-1",
    title: "Advanced Techniques Part 1",
    description: "Learn advanced martial arts techniques",
    thumbnailUrl: "https://example.com/thumb1.jpg",
    duration: 1800,
    instructorName: "John Doe",
    category: "Advanced",
    requiredTier: "Premium",
    recordingId: "rec-1",
  },
  {
    id: "session-2",
    title: "Fundamentals Review",
    description: "Review of basic fundamentals",
    thumbnailUrl: "https://example.com/thumb2.jpg",
    duration: 1200,
    instructorName: "Jane Smith",
    category: "Beginner",
    requiredTier: "Basic",
    recordingId: "rec-2",
  },
  {
    id: "session-3",
    title: "Competition Preparation",
    description: "Preparing for competitions",
    thumbnailUrl: undefined,
    duration: 2400,
    instructorName: "Mike Johnson",
    category: "Competition",
    requiredTier: "Premium+",
    recordingId: "rec-3",
  },
  {
    id: "session-4",
    title: "Flexibility Training",
    thumbnailUrl: "https://example.com/thumb4.jpg",
    duration: 900,
    instructorName: "Sarah Williams",
    category: "Fitness",
    recordingId: "rec-4",
  },
  {
    id: "session-5",
    title: "Sparring Techniques",
    thumbnailUrl: "https://example.com/thumb5.jpg",
    duration: undefined,
    instructorName: "Tom Brown",
    category: "Advanced",
    recordingId: "rec-5",
  },
  {
    id: "session-6",
    title: "Forms and Kata",
    thumbnailUrl: "https://example.com/thumb6.jpg",
    duration: 1500,
    instructorName: "Lisa Davis",
    category: "Traditional",
    recordingId: "rec-6",
  },
];

describe("RelatedVideos", () => {
  it("renders the related videos section", () => {
    render(<RelatedVideos sessions={mockSessions.slice(0, 3)} />);
    expect(screen.getByText("Related Videos")).toBeInTheDocument();
  });

  it("displays related video titles", () => {
    render(<RelatedVideos sessions={mockSessions.slice(0, 3)} />);
    expect(screen.getByText("Advanced Techniques Part 1")).toBeInTheDocument();
    expect(screen.getByText("Fundamentals Review")).toBeInTheDocument();
    expect(screen.getByText("Competition Preparation")).toBeInTheDocument();
  });

  it("displays instructor names", () => {
    render(<RelatedVideos sessions={mockSessions.slice(0, 3)} />);
    expect(screen.getByText("John Doe")).toBeInTheDocument();
    expect(screen.getByText("Jane Smith")).toBeInTheDocument();
  });

  it("displays video duration", () => {
    render(<RelatedVideos sessions={mockSessions.slice(0, 3)} />);
    expect(screen.getByText("30:00")).toBeInTheDocument(); // 1800 seconds
    expect(screen.getByText("20:00")).toBeInTheDocument(); // 1200 seconds
    expect(screen.getByText("40:00")).toBeInTheDocument(); // 2400 seconds
  });

  it("formats duration with hours correctly", () => {
    const longSession = {
      id: "long-session",
      title: "Marathon Session",
      duration: 7200, // 2 hours
      instructorName: "Test Instructor",
      recordingId: "rec-long",
    };

    render(<RelatedVideos sessions={[longSession]} />);
    expect(screen.getByText("2:00:00")).toBeInTheDocument();
  });

  it("shows N/A for missing duration", () => {
    render(<RelatedVideos sessions={[mockSessions[4]]} />);
    expect(screen.getByText("N/A")).toBeInTheDocument();
  });

  it("displays category badges", () => {
    render(<RelatedVideos sessions={mockSessions.slice(0, 3)} />);
    expect(screen.getByText("Advanced")).toBeInTheDocument();
    expect(screen.getByText("Beginner")).toBeInTheDocument();
    expect(screen.getByText("Competition")).toBeInTheDocument();
  });

  it("displays tier badges for non-basic tiers", () => {
    render(<RelatedVideos sessions={mockSessions.slice(0, 3)} />);
    expect(screen.getByText("Premium")).toBeInTheDocument();
    expect(screen.getByText("Premium+")).toBeInTheDocument();
    expect(screen.queryByText("Basic")).not.toBeInTheDocument();
  });

  it("shows only 3 videos initially", () => {
    render(<RelatedVideos sessions={mockSessions} />);

    expect(screen.getByText("Advanced Techniques Part 1")).toBeInTheDocument();
    expect(screen.getByText("Fundamentals Review")).toBeInTheDocument();
    expect(screen.getByText("Competition Preparation")).toBeInTheDocument();
    expect(screen.queryByText("Flexibility Training")).not.toBeInTheDocument();
  });

  it("shows load more button when there are more videos", () => {
    render(<RelatedVideos sessions={mockSessions} />);
    expect(screen.getByText(/load more/i)).toBeInTheDocument();
    expect(screen.getByText(/3 remaining/i)).toBeInTheDocument();
  });

  it("loads more videos when load more is clicked", async () => {
    render(<RelatedVideos sessions={mockSessions} />);

    const loadMoreButton = screen.getByText(/load more/i);
    await userEvent.click(loadMoreButton);

    await waitFor(() => {
      expect(screen.getByText("Flexibility Training")).toBeInTheDocument();
      expect(screen.getByText("Sparring Techniques")).toBeInTheDocument();
      expect(screen.getByText("Forms and Kata")).toBeInTheDocument();
    });
  });

  it("hides load more button when all videos are shown", async () => {
    render(<RelatedVideos sessions={mockSessions} />);

    const loadMoreButton = screen.getByText(/load more/i);
    await userEvent.click(loadMoreButton);

    await waitFor(() => {
      expect(screen.queryByText(/load more/i)).not.toBeInTheDocument();
      expect(screen.getByText("No more videos")).toBeInTheDocument();
    });
  });

  it("renders links to VOD pages", () => {
    render(<RelatedVideos sessions={mockSessions.slice(0, 3)} />);

    const links = screen.getAllByRole("link");
    expect(links[0]).toHaveAttribute("href", "/training/session-1/vod");
    expect(links[1]).toHaveAttribute("href", "/training/session-2/vod");
    expect(links[2]).toHaveAttribute("href", "/training/session-3/vod");
  });

  it("displays thumbnail images when available", () => {
    const { container } = render(<RelatedVideos sessions={mockSessions.slice(0, 1)} />);

    const images = container.querySelectorAll("img");
    expect(images.length).toBeGreaterThan(0);
  });

  it("shows play icon when no thumbnail", () => {
    render(<RelatedVideos sessions={[mockSessions[2]]} />);

    const playIcon = document.querySelector(".lucide-play");
    expect(playIcon).toBeInTheDocument();
  });

  it("applies hover effects", () => {
    const { container } = render(<RelatedVideos sessions={mockSessions.slice(0, 1)} />);

    const videoCard = container.querySelector(".group");
    expect(videoCard).toHaveClass("group");
  });

  it("handles empty sessions array", () => {
    render(<RelatedVideos sessions={[]} />);

    expect(screen.getByText("Related Videos")).toBeInTheDocument();
    expect(screen.queryByText("Advanced Techniques Part 1")).not.toBeInTheDocument();
  });

  it("truncates long titles", () => {
    const longTitleSession = {
      id: "long-title",
      title: "This is a very long title that should be truncated to prevent overflow and maintain proper layout consistency across all video cards",
      instructorName: "Test Instructor",
      duration: 1200,
      recordingId: "rec-long",
    };

    const { container } = render(<RelatedVideos sessions={[longTitleSession]} />);

    const title = container.querySelector(".line-clamp-2");
    expect(title).toBeInTheDocument();
  });

  it("increments visible count by 3 on each load more", async () => {
    const manySessions = Array.from({ length: 12 }, (_, i) => ({
      id: `session-${i}`,
      title: `Session ${i}`,
      instructorName: "Instructor",
      duration: 1200,
      recordingId: `rec-${i}`,
    }));

    render(<RelatedVideos sessions={manySessions} />);

    // Initially 3 visible
    expect(screen.getByText(/9 remaining/i)).toBeInTheDocument();

    // Click load more
    await userEvent.click(screen.getByText(/load more/i));

    // Now 6 visible
    await waitFor(() => {
      expect(screen.getByText(/6 remaining/i)).toBeInTheDocument();
    });

    // Click load more again
    await userEvent.click(screen.getByText(/load more/i));

    // Now 9 visible
    await waitFor(() => {
      expect(screen.getByText(/3 remaining/i)).toBeInTheDocument();
    });
  });

  it("does not show 'no more videos' message if initially 3 or fewer", () => {
    render(<RelatedVideos sessions={mockSessions.slice(0, 2)} />);

    expect(screen.queryByText("No more videos")).not.toBeInTheDocument();
    expect(screen.queryByText(/load more/i)).not.toBeInTheDocument();
  });
});
