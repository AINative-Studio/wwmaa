/**
 * Tests for EventHero Component
 */

import { render, screen } from "@testing-library/react";
import { EventHero } from "@/components/events/event-hero";

describe("EventHero", () => {
  const defaultProps = {
    title: "Judo Seminar with Sensei Smith",
    featuredImageUrl: "https://example.com/image.jpg",
    eventType: "seminar",
    startDatetime: "2025-12-15T10:00:00Z",
    endDatetime: "2025-12-15T13:00:00Z",
    timezone: "America/Los_Angeles",
    locationName: "WWMAA Dojo",
    city: "San Francisco",
    state: "CA",
    isVirtual: false,
    maxAttendees: 30,
    spotsRemaining: 15,
    registrationFee: 50.0,
    visibility: "public",
  };

  it("renders event title correctly", () => {
    render(<EventHero {...defaultProps} />);
    expect(screen.getByText("Judo Seminar with Sensei Smith")).toBeInTheDocument();
  });

  it("displays event type badge", () => {
    render(<EventHero {...defaultProps} />);
    expect(screen.getByText("Seminar")).toBeInTheDocument();
  });

  it("shows location for in-person events", () => {
    render(<EventHero {...defaultProps} />);
    expect(screen.getByText("WWMAA Dojo")).toBeInTheDocument();
    expect(screen.getByText("San Francisco, CA")).toBeInTheDocument();
  });

  it("shows virtual event label when event is online", () => {
    render(<EventHero {...defaultProps} isVirtual={true} />);
    expect(screen.getByText("Virtual Event")).toBeInTheDocument();
    expect(screen.getByText("Join from anywhere")).toBeInTheDocument();
  });

  it("displays spots remaining when available", () => {
    render(<EventHero {...defaultProps} />);
    expect(screen.getByText("15 spots remaining")).toBeInTheDocument();
  });

  it("shows event full when no spots remaining", () => {
    render(<EventHero {...defaultProps} spotsRemaining={0} />);
    expect(screen.getByText("Event Full")).toBeInTheDocument();
  });

  it("displays registration fee correctly", () => {
    render(<EventHero {...defaultProps} />);
    expect(screen.getByText("$50.00")).toBeInTheDocument();
  });

  it("shows free when no registration fee", () => {
    render(<EventHero {...defaultProps} registrationFee={0} />);
    expect(screen.getByText("Free")).toBeInTheDocument();
  });

  it("displays members only badge for restricted events", () => {
    render(<EventHero {...defaultProps} visibility="members_only" />);
    expect(screen.getByText("Members Only")).toBeInTheDocument();
  });

  it("displays invite only badge for invite events", () => {
    render(<EventHero {...defaultProps} visibility="invite_only" />);
    expect(screen.getByText("Invite Only")).toBeInTheDocument();
  });

  it("shows location TBD when no location provided", () => {
    render(
      <EventHero
        {...defaultProps}
        locationName={undefined}
        city={undefined}
        state={undefined}
      />
    );
    expect(screen.getByText("Location TBD")).toBeInTheDocument();
  });

  it("displays capacity info when max attendees is set", () => {
    render(<EventHero {...defaultProps} />);
    expect(screen.getByText("Limited capacity")).toBeInTheDocument();
  });
});
