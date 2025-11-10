/**
 * Tests for AddToCalendar Component
 */

import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { AddToCalendar } from "@/components/events/add-to-calendar";

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(),
  },
});

describe("AddToCalendar", () => {
  const defaultProps = {
    title: "Judo Seminar",
    description: "Advanced Judo techniques seminar",
    startDatetime: "2025-12-15T10:00:00Z",
    endDatetime: "2025-12-15T13:00:00Z",
    location: "123 Main St, San Francisco, CA",
    locationName: "WWMAA Dojo",
    city: "San Francisco",
    state: "CA",
    isVirtual: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders add to calendar button", () => {
    render(<AddToCalendar {...defaultProps} />);
    expect(screen.getByText("Add to Calendar")).toBeInTheDocument();
  });

  it("opens dropdown menu when clicked", async () => {
    render(<AddToCalendar {...defaultProps} />);

    const button = screen.getByText("Add to Calendar");
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText("Google Calendar")).toBeInTheDocument();
      expect(screen.getByText("Outlook Calendar")).toBeInTheDocument();
      expect(screen.getByText("Download ICS File")).toBeInTheDocument();
    });
  });

  it("generates correct Google Calendar URL", async () => {
    const windowOpenSpy = jest.spyOn(window, "open").mockImplementation();

    render(<AddToCalendar {...defaultProps} />);

    const button = screen.getByText("Add to Calendar");
    fireEvent.click(button);

    await waitFor(() => {
      const googleOption = screen.getByText("Google Calendar");
      fireEvent.click(googleOption);
    });

    expect(windowOpenSpy).toHaveBeenCalled();
    const calledUrl = windowOpenSpy.mock.calls[0][0] as string;
    expect(calledUrl).toContain("calendar.google.com");
    expect(calledUrl).toContain(encodeURIComponent("Judo Seminar"));

    windowOpenSpy.mockRestore();
  });

  it("generates correct Outlook Calendar URL", async () => {
    const windowOpenSpy = jest.spyOn(window, "open").mockImplementation();

    render(<AddToCalendar {...defaultProps} />);

    const button = screen.getByText("Add to Calendar");
    fireEvent.click(button);

    await waitFor(() => {
      const outlookOption = screen.getByText("Outlook Calendar");
      fireEvent.click(outlookOption);
    });

    expect(windowOpenSpy).toHaveBeenCalled();
    const calledUrl = windowOpenSpy.mock.calls[0][0] as string;
    expect(calledUrl).toContain("outlook.live.com");

    windowOpenSpy.mockRestore();
  });

  it("downloads ICS file when download option clicked", async () => {
    // Mock DOM operations for download
    const createElementSpy = jest.spyOn(document, "createElement");
    const appendChildSpy = jest.spyOn(document.body, "appendChild").mockImplementation();
    const removeChildSpy = jest.spyOn(document.body, "removeChild").mockImplementation();

    render(<AddToCalendar {...defaultProps} />);

    const button = screen.getByText("Add to Calendar");
    fireEvent.click(button);

    await waitFor(() => {
      const downloadOption = screen.getByText("Download ICS File");
      fireEvent.click(downloadOption);
    });

    expect(createElementSpy).toHaveBeenCalledWith("a");

    createElementSpy.mockRestore();
    appendChildSpy.mockRestore();
    removeChildSpy.mockRestore();
  });

  it("uses virtual URL for virtual events", async () => {
    const virtualProps = {
      ...defaultProps,
      isVirtual: true,
      virtualUrl: "https://zoom.us/j/123456",
    };

    const windowOpenSpy = jest.spyOn(window, "open").mockImplementation();

    render(<AddToCalendar {...virtualProps} />);

    const button = screen.getByText("Add to Calendar");
    fireEvent.click(button);

    await waitFor(() => {
      const googleOption = screen.getByText("Google Calendar");
      fireEvent.click(googleOption);
    });

    const calledUrl = windowOpenSpy.mock.calls[0][0] as string;
    expect(calledUrl).toContain(encodeURIComponent("https://zoom.us/j/123456"));

    windowOpenSpy.mockRestore();
  });

  it("handles events without description", async () => {
    const propsWithoutDesc = {
      ...defaultProps,
      description: undefined,
    };

    render(<AddToCalendar {...propsWithoutDesc} />);

    const button = screen.getByText("Add to Calendar");
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText("Google Calendar")).toBeInTheDocument();
    });
  });
});
