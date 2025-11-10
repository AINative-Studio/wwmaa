/**
 * Tests for EventCard Component (US-030)
 */

import { render, screen } from "@testing-library/react";
import { EventCard } from "@/components/events/event-card";
import { EventItem } from "@/lib/types";

describe("EventCard", () => {
  const mockEvent: EventItem = {
    id: "e_test_1",
    title: "Karate Kata Workshop",
    description: "Learn traditional kata",
    start: "2025-12-12T18:00:00Z",
    end: "2025-12-12T20:00:00Z",
    location: "Tokyo, Japan",
    location_type: "in_person",
    type: "seminar",
    price: 80,
    visibility: "public",
    status: "published",
    teaser: "Traditional kata refinement with senior instructors.",
    image: "/images/karate.jpg",
    instructor: "Sensei Nakamura",
    max_participants: 30,
    current_participants: 15,
    created_at: "2025-11-01T10:00:00Z",
    updated_at: "2025-11-01T10:00:00Z",
  };

  it("renders event title correctly (AC2)", () => {
    render(<EventCard event={mockEvent} />);
    expect(screen.getByText("Karate Kata Workshop")).toBeInTheDocument();
  });

  it("displays event type badge (AC2)", () => {
    render(<EventCard event={mockEvent} />);
    expect(screen.getByText("Seminar")).toBeInTheDocument();
  });

  it("shows event date in readable format (AC2)", () => {
    render(<EventCard event={mockEvent} />);
    // Date should be formatted like "Fri, Dec 12 at 6:00 PM" (depends on timezone)
    expect(screen.getByText(/Dec 12 at/)).toBeInTheDocument();
  });

  it("displays event location (AC2)", () => {
    render(<EventCard event={mockEvent} />);
    expect(screen.getByText("Tokyo, Japan")).toBeInTheDocument();
  });

  it("shows event price (AC2)", () => {
    render(<EventCard event={mockEvent} />);
    expect(screen.getByText("80")).toBeInTheDocument();
  });

  it('displays "Free" badge for free events (AC2)', () => {
    const freeEvent = { ...mockEvent, price: 0 };
    render(<EventCard event={freeEvent} />);
    expect(screen.getByText("Free")).toBeInTheDocument();
  });

  it("shows instructor name when provided (AC2)", () => {
    render(<EventCard event={mockEvent} />);
    expect(screen.getByText(/Sensei Nakamura/)).toBeInTheDocument();
  });

  it('displays "Members Only" badge for restricted events (AC6)', () => {
    const membersEvent = { ...mockEvent, visibility: "members_only" } as EventItem;
    render(<EventCard event={membersEvent} />);
    expect(screen.getByText("Members Only")).toBeInTheDocument();
  });

  it("shows spots remaining when available", () => {
    render(<EventCard event={mockEvent} />);
    const spotsRemaining = (mockEvent.max_participants ?? 0) - (mockEvent.current_participants ?? 0);
    expect(screen.getByText(`${spotsRemaining} spots remaining`)).toBeInTheDocument();
  });

  it('displays "Full" badge when event is at capacity', () => {
    const fullEvent = {
      ...mockEvent,
      max_participants: 30,
      current_participants: 30,
    };
    render(<EventCard event={fullEvent} />);
    expect(screen.getByText("Full")).toBeInTheDocument();
  });

  it("displays teaser text when provided (AC2)", () => {
    render(<EventCard event={mockEvent} />);
    expect(screen.getByText("Traditional kata refinement with senior instructors.")).toBeInTheDocument();
  });

  it("has link to event detail page (AC7)", () => {
    const { container } = render(<EventCard event={mockEvent} />);
    const link = container.querySelector('a[href="/events/e_test_1"]');
    expect(link).toBeInTheDocument();
  });

  it("displays online event icon for online events", () => {
    const onlineEvent = { ...mockEvent, location_type: "online", location: "Online" } as EventItem;
    render(<EventCard event={onlineEvent} />);
    // Check for online location
    expect(screen.getByText("Online")).toBeInTheDocument();
  });

  it("shows event type with correct color coding (AC2)", () => {
    const { rerender } = render(<EventCard event={mockEvent} />);

    // Seminar should have green badge
    expect(screen.getByText("Seminar")).toBeInTheDocument();

    // Tournament
    const tournamentEvent = { ...mockEvent, type: "tournament" } as EventItem;
    rerender(<EventCard event={tournamentEvent} />);
    expect(screen.getByText("Tournament")).toBeInTheDocument();

    // Live Training
    const trainingEvent = { ...mockEvent, type: "live_training" } as EventItem;
    rerender(<EventCard event={trainingEvent} />);
    expect(screen.getByText("Live Training")).toBeInTheDocument();

    // Certification
    const certEvent = { ...mockEvent, type: "certification" } as EventItem;
    rerender(<EventCard event={certEvent} />);
    expect(screen.getByText("Certification")).toBeInTheDocument();
  });

  it("displays placeholder when no image is provided", () => {
    const noImageEvent = { ...mockEvent, image: undefined };
    const { container } = render(<EventCard event={noImageEvent} />);
    // Should render a calendar icon placeholder
    const calendarIcon = container.querySelector('svg');
    expect(calendarIcon).toBeInTheDocument();
  });

  it("renders in responsive card layout", () => {
    const { container } = render(<EventCard event={mockEvent} />);
    const card = container.firstChild;
    expect(card).toHaveClass("rounded-2xl");
    expect(card).toHaveClass("shadow-sm");
  });

  it("has proper accessibility attributes", () => {
    render(<EventCard event={mockEvent} />);
    const link = screen.getByRole("link", { name: /View details for Karate Kata Workshop/i });
    expect(link).toBeInTheDocument();
  });

  it("shows View Details CTA", () => {
    render(<EventCard event={mockEvent} />);
    expect(screen.getByText("View Details")).toBeInTheDocument();
  });
});
