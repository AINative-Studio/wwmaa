/**
 * Tests for EventFilters Component (US-030)
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { EventFilters } from "@/components/events/event-filters";
import { EventType, EventLocationType } from "@/lib/types";

describe("EventFilters", () => {
  const mockOnFilterChange = jest.fn();
  const mockOnClearAll = jest.fn();

  const defaultFilters = {
    type: undefined,
    location: undefined,
    price: undefined,
    date_range: "upcoming" as const,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders all filter sections (AC3)", () => {
    render(
      <EventFilters
        filters={defaultFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    expect(screen.getByText("Event Type")).toBeInTheDocument();
    expect(screen.getByText("Date Range")).toBeInTheDocument();
    expect(screen.getByText("Location")).toBeInTheDocument();
    expect(screen.getByText("Price")).toBeInTheDocument();
  });

  it("displays all event type options (AC3)", () => {
    render(
      <EventFilters
        filters={defaultFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    expect(screen.getByText("All Types")).toBeInTheDocument();
    expect(screen.getByText("Live Training")).toBeInTheDocument();
    expect(screen.getByText("Seminar")).toBeInTheDocument();
    expect(screen.getByText("Tournament")).toBeInTheDocument();
    expect(screen.getByText("Certification")).toBeInTheDocument();
  });

  it("displays date range options (AC3)", () => {
    render(
      <EventFilters
        filters={defaultFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    expect(screen.getByText("All Upcoming")).toBeInTheDocument();
    expect(screen.getByText("This Week")).toBeInTheDocument();
    expect(screen.getByText("This Month")).toBeInTheDocument();
  });

  it("displays location filter options (AC3)", () => {
    render(
      <EventFilters
        filters={defaultFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    expect(screen.getByText("All Locations")).toBeInTheDocument();
    expect(screen.getByText("In-Person")).toBeInTheDocument();
    expect(screen.getByText("Online")).toBeInTheDocument();
  });

  it("displays price filter options (AC3)", () => {
    render(
      <EventFilters
        filters={defaultFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    expect(screen.getByText("All Prices")).toBeInTheDocument();
    expect(screen.getByText("Free Events")).toBeInTheDocument();
    expect(screen.getByText("Paid Events")).toBeInTheDocument();
  });

  it("calls onFilterChange when event type is selected (AC3)", () => {
    render(
      <EventFilters
        filters={defaultFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    const seminarOption = screen.getByLabelText("Seminar");
    fireEvent.click(seminarOption);

    expect(mockOnFilterChange).toHaveBeenCalledWith("type", "seminar");
  });

  it("calls onFilterChange when location filter is selected (AC3)", () => {
    render(
      <EventFilters
        filters={defaultFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    const onlineOption = screen.getByLabelText("Online");
    fireEvent.click(onlineOption);

    expect(mockOnFilterChange).toHaveBeenCalledWith("location", "online");
  });

  it("calls onFilterChange when price filter is selected (AC3)", () => {
    render(
      <EventFilters
        filters={defaultFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    const freeOption = screen.getByLabelText("Free Events");
    fireEvent.click(freeOption);

    expect(mockOnFilterChange).toHaveBeenCalledWith("price", "free");
  });

  it("shows Clear All button when filters are active", () => {
    const activeFilters = {
      ...defaultFilters,
      type: "seminar" as EventType,
      price: "free" as const,
    };

    render(
      <EventFilters
        filters={activeFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    expect(screen.getByText("Clear All")).toBeInTheDocument();
  });

  it("hides Clear All button when no filters are active", () => {
    render(
      <EventFilters
        filters={defaultFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    expect(screen.queryByText("Clear All")).not.toBeInTheDocument();
  });

  it("calls onClearAll when Clear All button is clicked", () => {
    const activeFilters = {
      ...defaultFilters,
      type: "seminar" as EventType,
    };

    render(
      <EventFilters
        filters={activeFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    const clearButton = screen.getByText("Clear All");
    fireEvent.click(clearButton);

    expect(mockOnClearAll).toHaveBeenCalled();
  });

  it("displays active filters section when filters are applied", () => {
    const activeFilters = {
      ...defaultFilters,
      type: "tournament" as EventType,
      location: "online" as EventLocationType,
      price: "free" as const,
    };

    render(
      <EventFilters
        filters={activeFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    expect(screen.getByText("Active Filters")).toBeInTheDocument();
  });

  it("shows active filter badges with remove buttons", () => {
    const activeFilters = {
      ...defaultFilters,
      type: "seminar" as EventType,
      price: "paid" as const,
    };

    render(
      <EventFilters
        filters={activeFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    // Active filter badges should be displayed
    const activeFilterSection = screen.getByText("Active Filters");
    expect(activeFilterSection).toBeInTheDocument();

    // Should have clickable filter badges
    const filterButtons = screen.getAllByRole("button");
    expect(filterButtons.length).toBeGreaterThan(1); // Clear All + filter badges
  });

  it("removes individual filter when badge X is clicked", () => {
    const activeFilters = {
      ...defaultFilters,
      type: "tournament" as EventType,
    };

    const { container } = render(
      <EventFilters
        filters={activeFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    // Find the filter badge button (not the Clear All button)
    const filterBadges = container.querySelectorAll('button[class*="inline-flex items-center"]');
    const tournamentBadge = Array.from(filterBadges).find(
      (button) => button.textContent?.includes("tournament")
    );

    if (tournamentBadge) {
      fireEvent.click(tournamentBadge);
      expect(mockOnFilterChange).toHaveBeenCalledWith("type", undefined);
    }
  });

  it("reflects selected filters in UI", () => {
    const activeFilters = {
      ...defaultFilters,
      type: "live_training" as EventType,
      location: "in_person" as EventLocationType,
    };

    render(
      <EventFilters
        filters={activeFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    // Radio buttons should reflect current selection
    const liveTrainingRadio = screen.getByDisplayValue("live_training");
    const inPersonRadio = screen.getByDisplayValue("in_person");

    expect(liveTrainingRadio).toBeChecked();
    expect(inPersonRadio).toBeChecked();
  });

  it("has proper accessibility labels", () => {
    render(
      <EventFilters
        filters={defaultFilters}
        onFilterChange={mockOnFilterChange}
        onClearAll={mockOnClearAll}
      />
    );

    // All radio options should have labels
    expect(screen.getByLabelText("All Types")).toBeInTheDocument();
    expect(screen.getByLabelText("Live Training")).toBeInTheDocument();
    expect(screen.getByLabelText("Seminar")).toBeInTheDocument();
    expect(screen.getByLabelText("All Locations")).toBeInTheDocument();
    expect(screen.getByLabelText("In-Person")).toBeInTheDocument();
    expect(screen.getByLabelText("Online")).toBeInTheDocument();
  });
});
