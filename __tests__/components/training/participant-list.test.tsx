import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ParticipantList } from "@/components/training/participant-list";

describe("ParticipantList", () => {
  const mockParticipants = [
    {
      id: "1",
      name: "Instructor Sensei",
      isInstructor: true,
      isMuted: false,
      hasVideo: true,
      isActive: true,
    },
    {
      id: "2",
      name: "Student One",
      isInstructor: false,
      isMuted: true,
      hasVideo: false,
      isActive: true,
    },
    {
      id: "3",
      name: "Student Two",
      isInstructor: false,
      isMuted: false,
      hasVideo: true,
      isActive: false,
    },
  ];

  const mockProps = {
    participants: mockParticipants,
    onClose: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders participant list header", () => {
    render(<ParticipantList {...mockProps} />);
    expect(screen.getByText("Participants")).toBeInTheDocument();
  });

  it("displays total participant count", () => {
    render(<ParticipantList {...mockProps} />);
    expect(screen.getByText("3 Total")).toBeInTheDocument();
  });

  it("displays active participant count", () => {
    render(<ParticipantList {...mockProps} />);
    expect(screen.getByText("2 Active")).toBeInTheDocument();
  });

  it("separates instructors from regular participants", () => {
    render(<ParticipantList {...mockProps} />);
    expect(screen.getByText(/Instructors \(1\)/)).toBeInTheDocument();
    expect(screen.getByText(/Participants \(2\)/)).toBeInTheDocument();
  });

  it("displays instructor with crown icon", () => {
    render(<ParticipantList {...mockProps} />);
    expect(screen.getByText("Instructor Sensei")).toBeInTheDocument();
  });

  it("shows all participant names", () => {
    render(<ParticipantList {...mockProps} />);
    expect(screen.getByText("Instructor Sensei")).toBeInTheDocument();
    expect(screen.getByText("Student One")).toBeInTheDocument();
    expect(screen.getByText("Student Two")).toBeInTheDocument();
  });

  it("displays active status for participants", () => {
    render(<ParticipantList {...mockProps} />);
    const activeLabels = screen.getAllByText("Active");
    expect(activeLabels.length).toBe(2);
  });

  it("displays idle status for inactive participants", () => {
    render(<ParticipantList {...mockProps} />);
    expect(screen.getByText("Idle")).toBeInTheDocument();
  });

  it("calls onClose when close button clicked", () => {
    render(<ParticipantList {...mockProps} />);
    const closeButtons = screen.getAllByRole("button");
    const closeButton = closeButtons[0]; // First button should be close

    fireEvent.click(closeButton);
    expect(mockProps.onClose).toHaveBeenCalled();
  });

  it("displays legend with status explanations", () => {
    render(<ParticipantList {...mockProps} />);
    expect(screen.getByText("Legend:")).toBeInTheDocument();
    expect(screen.getByText("Active in session")).toBeInTheDocument();
    expect(screen.getByText("Microphone on")).toBeInTheDocument();
    expect(screen.getByText("Camera on")).toBeInTheDocument();
  });

  it("shows empty state when no participants", () => {
    const emptyProps = {
      participants: [],
      onClose: jest.fn(),
    };

    render(<ParticipantList {...emptyProps} />);
    expect(screen.getByText("No participants yet")).toBeInTheDocument();
  });

  it("displays participant initials in avatar", () => {
    render(<ParticipantList {...mockProps} />);
    // Avatars should display initials
    expect(screen.getByText("IS")).toBeInTheDocument(); // Instructor Sensei
    expect(screen.getByText("SO")).toBeInTheDocument(); // Student One
    expect(screen.getByText("ST")).toBeInTheDocument(); // Student Two
  });

  it("shows only regular participants when no instructors", () => {
    const regularOnlyProps = {
      participants: [
        {
          id: "2",
          name: "Student One",
          isInstructor: false,
          isMuted: true,
          hasVideo: false,
          isActive: true,
        },
      ],
      onClose: jest.fn(),
    };

    render(<ParticipantList {...regularOnlyProps} />);
    expect(screen.getByText(/Participants \(1\)/)).toBeInTheDocument();
    expect(screen.queryByText(/Instructors/)).not.toBeInTheDocument();
  });
});
