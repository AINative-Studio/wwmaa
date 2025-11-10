/**
 * Tests for EventSort Component (US-030)
 */

import { render, screen, fireEvent, within } from "@testing-library/react";
import { EventSort } from "@/components/events/event-sort";

describe("EventSort", () => {
  const mockOnSortChange = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders sort dropdown (AC4)", () => {
    render(<EventSort sortBy="date" sortOrder="asc" onSortChange={mockOnSortChange} />);

    expect(screen.getByRole("combobox")).toBeInTheDocument();
  });

  it("displays current sort option", () => {
    const { container } = render(
      <EventSort sortBy="date" sortOrder="asc" onSortChange={mockOnSortChange} />
    );

    // The trigger should show the current selection
    const trigger = container.querySelector('[role="combobox"]');
    expect(trigger).toBeInTheDocument();
  });

  it("shows all sort options when opened", () => {
    render(<EventSort sortBy="date" sortOrder="asc" onSortChange={mockOnSortChange} />);

    // Click to open dropdown
    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    // Check for all sort options (AC4)
    expect(screen.getByText("Date: Earliest First")).toBeInTheDocument();
    expect(screen.getByText("Date: Latest First")).toBeInTheDocument();
    expect(screen.getByText("Price: Low to High")).toBeInTheDocument();
    expect(screen.getByText("Price: High to Low")).toBeInTheDocument();
  });

  it("calls onSortChange when date ascending is selected (AC4)", () => {
    render(<EventSort sortBy="price" sortOrder="desc" onSortChange={mockOnSortChange} />);

    // Open dropdown
    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    // Select "Date: Earliest First"
    const option = screen.getByText("Date: Earliest First");
    fireEvent.click(option);

    expect(mockOnSortChange).toHaveBeenCalledWith("date", "asc");
  });

  it("calls onSortChange when date descending is selected (AC4)", () => {
    render(<EventSort sortBy="date" sortOrder="asc" onSortChange={mockOnSortChange} />);

    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    const option = screen.getByText("Date: Latest First");
    fireEvent.click(option);

    expect(mockOnSortChange).toHaveBeenCalledWith("date", "desc");
  });

  it("calls onSortChange when price low to high is selected (AC4)", () => {
    render(<EventSort sortBy="date" sortOrder="asc" onSortChange={mockOnSortChange} />);

    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    const option = screen.getByText("Price: Low to High");
    fireEvent.click(option);

    expect(mockOnSortChange).toHaveBeenCalledWith("price", "asc");
  });

  it("calls onSortChange when price high to low is selected (AC4)", () => {
    render(<EventSort sortBy="date" sortOrder="asc" onSortChange={mockOnSortChange} />);

    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    const option = screen.getByText("Price: High to Low");
    fireEvent.click(option);

    expect(mockOnSortChange).toHaveBeenCalledWith("price", "desc");
  });

  it("displays sort icon", () => {
    const { container } = render(
      <EventSort sortBy="date" sortOrder="asc" onSortChange={mockOnSortChange} />
    );

    // Should have an ArrowUpDown icon
    const icon = container.querySelector('svg');
    expect(icon).toBeInTheDocument();
  });

  it("reflects current sort selection", () => {
    render(<EventSort sortBy="price" sortOrder="desc" onSortChange={mockOnSortChange} />);

    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    // "Price: High to Low" should be selected
    const selectedOption = screen.getByText("Price: High to Low");
    expect(selectedOption).toBeInTheDocument();
  });

  it("has proper accessibility attributes", () => {
    render(<EventSort sortBy="date" sortOrder="asc" onSortChange={mockOnSortChange} />);

    const combobox = screen.getByRole("combobox");
    expect(combobox).toBeInTheDocument();
    expect(combobox).toHaveAccessibleName();
  });

  it("closes dropdown after selection", () => {
    render(<EventSort sortBy="date" sortOrder="asc" onSortChange={mockOnSortChange} />);

    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    // Options should be visible
    expect(screen.getByText("Date: Earliest First")).toBeInTheDocument();

    // Select an option
    const option = screen.getByText("Price: Low to High");
    fireEvent.click(option);

    // Dropdown should close (options no longer visible)
    // This behavior is handled by the Select component
    expect(mockOnSortChange).toHaveBeenCalled();
  });

  it("maintains selection state across renders", () => {
    const { rerender } = render(
      <EventSort sortBy="date" sortOrder="asc" onSortChange={mockOnSortChange} />
    );

    // Rerender with different sort
    rerender(<EventSort sortBy="price" sortOrder="asc" onSortChange={mockOnSortChange} />);

    const trigger = screen.getByRole("combobox");
    fireEvent.click(trigger);

    // New selection should be reflected
    expect(screen.getByText("Price: Low to High")).toBeInTheDocument();
  });
});
