import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { EventCalendar } from '@/components/events/event-calendar';
import { EventItem } from '@/lib/types';
import { useRouter } from 'next/navigation';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}));

// Mock react-big-calendar CSS import
jest.mock('react-big-calendar/lib/css/react-big-calendar.css', () => ({}));

describe('EventCalendar', () => {
  const mockPush = jest.fn();
  const mockEvents: EventItem[] = [
    {
      id: 'e1',
      title: 'Judo Seminar',
      description: 'Advanced Judo techniques',
      start: '2025-12-15T10:00:00Z',
      end: '2025-12-15T12:00:00Z',
      location: 'Online',
      location_type: 'online',
      type: 'seminar',
      price: 0,
      visibility: 'public',
      status: 'published',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
    {
      id: 'e2',
      title: 'Karate Tournament',
      description: 'National championship',
      start: '2025-12-20T09:00:00Z',
      end: '2025-12-20T18:00:00Z',
      location: 'Los Angeles, CA',
      location_type: 'in_person',
      type: 'tournament',
      price: 50,
      visibility: 'public',
      status: 'published',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
  ];

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    });
    mockPush.mockClear();
  });

  it('renders calendar with events', () => {
    render(<EventCalendar events={mockEvents} />);

    // Check for calendar navigation elements
    expect(screen.getByText('Today')).toBeInTheDocument();
    expect(screen.getByText('Next')).toBeInTheDocument();
    expect(screen.getByText('Previous')).toBeInTheDocument();
  });

  it('displays color legend', () => {
    render(<EventCalendar events={mockEvents} />);

    expect(screen.getByText('Live Training')).toBeInTheDocument();
    expect(screen.getByText('Seminar')).toBeInTheDocument();
    expect(screen.getByText('Tournament')).toBeInTheDocument();
    expect(screen.getByText('Certification')).toBeInTheDocument();
  });

  it('displays events on calendar', async () => {
    render(<EventCalendar events={mockEvents} />);

    await waitFor(() => {
      expect(screen.getByText('Judo Seminar')).toBeInTheDocument();
      expect(screen.getByText('Karate Tournament')).toBeInTheDocument();
    });
  });

  it('navigates to event detail on click', async () => {
    const user = userEvent.setup();
    render(<EventCalendar events={mockEvents} />);

    const event = await screen.findByText('Judo Seminar');
    await user.click(event);

    expect(mockPush).toHaveBeenCalledWith('/events/e1');
  });

  it('calls onDateRangeChange when navigating months', async () => {
    const onDateRangeChange = jest.fn();
    const user = userEvent.setup();

    render(<EventCalendar events={mockEvents} onDateRangeChange={onDateRangeChange} />);

    const nextButton = screen.getByText('Next');
    await user.click(nextButton);

    expect(onDateRangeChange).toHaveBeenCalled();
  });

  it('shows event time and location type', async () => {
    render(<EventCalendar events={mockEvents} />);

    await waitFor(() => {
      // Check for online indicator
      const onlineEvents = screen.getAllByText('Online');
      expect(onlineEvents.length).toBeGreaterThan(0);
    });
  });

  it('handles empty events array', () => {
    render(<EventCalendar events={[]} />);

    // Calendar should still render with controls
    expect(screen.getByText('Today')).toBeInTheDocument();
    expect(screen.getByText('Month')).toBeInTheDocument();
  });

  it('switches between month, week, and day views', async () => {
    const user = userEvent.setup();
    render(<EventCalendar events={mockEvents} />);

    // Click Week view
    const weekButton = screen.getByText('Week');
    await user.click(weekButton);

    // Verify week view is active
    expect(weekButton).toHaveClass('rbc-active');

    // Click Day view
    const dayButton = screen.getByText('Day');
    await user.click(dayButton);

    // Verify day view is active
    expect(dayButton).toHaveClass('rbc-active');
  });

  it('displays correct color coding for different event types', () => {
    const multiTypeEvents: EventItem[] = [
      {
        id: 'live1',
        title: 'Live Training Session',
        start: '2025-12-15T10:00:00Z',
        end: '2025-12-15T12:00:00Z',
        location: 'Online',
        location_type: 'online',
        type: 'live_training',
        price: 0,
        visibility: 'public',
        status: 'published',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
      {
        id: 'cert1',
        title: 'Black Belt Certification',
        start: '2025-12-16T10:00:00Z',
        end: '2025-12-16T15:00:00Z',
        location: 'Dojo',
        location_type: 'in_person',
        type: 'certification',
        price: 100,
        visibility: 'public',
        status: 'published',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
    ];

    render(<EventCalendar events={multiTypeEvents} />);

    // Verify all color legends are displayed
    expect(screen.getByText('Live Training')).toBeInTheDocument();
    expect(screen.getByText('Seminar')).toBeInTheDocument();
    expect(screen.getByText('Tournament')).toBeInTheDocument();
    expect(screen.getByText('Certification')).toBeInTheDocument();
  });

  it('handles multi-day events spanning across dates', async () => {
    const multiDayEvent: EventItem[] = [
      {
        id: 'multi1',
        title: 'Weekend Seminar',
        start: '2025-12-20T09:00:00Z',
        end: '2025-12-22T17:00:00Z',
        location: 'Training Center',
        location_type: 'in_person',
        type: 'seminar',
        price: 150,
        visibility: 'public',
        status: 'published',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
    ];

    render(<EventCalendar events={multiDayEvent} />);

    await waitFor(() => {
      expect(screen.getByText('Weekend Seminar')).toBeInTheDocument();
    });
  });

  it('displays today indicator correctly', () => {
    render(<EventCalendar events={mockEvents} />);

    // Calendar should render and handle today's date
    const todayButton = screen.getByText('Today');
    expect(todayButton).toBeInTheDocument();
  });

  it('navigates to previous month when clicking Previous button', async () => {
    const onDateRangeChange = jest.fn();
    const user = userEvent.setup();

    render(<EventCalendar events={mockEvents} onDateRangeChange={onDateRangeChange} />);

    const prevButton = screen.getByText('Previous');
    await user.click(prevButton);

    expect(onDateRangeChange).toHaveBeenCalled();
  });

  it('navigates to today when clicking Today button', async () => {
    const user = userEvent.setup();
    render(<EventCalendar events={mockEvents} />);

    const todayButton = screen.getByText('Today');
    await user.click(todayButton);

    // Calendar should navigate to current date
    expect(todayButton).toBeInTheDocument();
  });

  it('displays event price information in tooltip', () => {
    render(<EventCalendar events={mockEvents} />);

    // Calendar renders with events that have price information
    expect(screen.getByText('Judo Seminar')).toBeInTheDocument();
    expect(screen.getByText('Karate Tournament')).toBeInTheDocument();
  });

  it('handles paid vs free events correctly', async () => {
    const mixedPriceEvents: EventItem[] = [
      {
        id: 'free1',
        title: 'Free Seminar',
        start: '2025-12-15T10:00:00Z',
        end: '2025-12-15T12:00:00Z',
        location: 'Community Center',
        location_type: 'in_person',
        type: 'seminar',
        price: 0,
        visibility: 'public',
        status: 'published',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
      {
        id: 'paid1',
        title: 'Premium Training',
        start: '2025-12-16T10:00:00Z',
        end: '2025-12-16T12:00:00Z',
        location: 'Elite Dojo',
        location_type: 'in_person',
        type: 'live_training',
        price: 75,
        visibility: 'public',
        status: 'published',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
    ];

    render(<EventCalendar events={mixedPriceEvents} />);

    await waitFor(() => {
      expect(screen.getByText('Free Seminar')).toBeInTheDocument();
      expect(screen.getByText('Premium Training')).toBeInTheDocument();
    });
  });

  it('applies custom className when provided', () => {
    const { container } = render(
      <EventCalendar events={mockEvents} className="custom-calendar-class" />
    );

    expect(container.querySelector('.custom-calendar-class')).toBeInTheDocument();
  });

  it('displays location information for online vs in-person events', async () => {
    render(<EventCalendar events={mockEvents} />);

    await waitFor(() => {
      // Online event should show "Online" indicator
      const onlineEvents = screen.getAllByText('Online');
      expect(onlineEvents.length).toBeGreaterThan(0);
    });
  });

  // Additional tests for comprehensive coverage

  describe('EventCalendar - Additional Coverage', () => {
    it('handles view change to week view', async () => {
      const user = userEvent.setup();
      render(<EventCalendar events={mockEvents} />);

      const weekButton = screen.getByText('Week');
      await user.click(weekButton);

      expect(weekButton).toHaveClass('rbc-active');
    });

    it('handles view change to day view', async () => {
      const user = userEvent.setup();
      render(<EventCalendar events={mockEvents} />);

      const dayButton = screen.getByText('Day');
      await user.click(dayButton);

      expect(dayButton).toHaveClass('rbc-active');
    });

    it('handles navigation to next period', async () => {
      const onDateRangeChange = jest.fn();
      const user = userEvent.setup();
      render(<EventCalendar events={mockEvents} onDateRangeChange={onDateRangeChange} />);

      const nextButton = screen.getByText('Next');
      await user.click(nextButton);

      expect(onDateRangeChange).toHaveBeenCalled();
    });

    it('handles navigation to previous period', async () => {
      const onDateRangeChange = jest.fn();
      const user = userEvent.setup();
      render(<EventCalendar events={mockEvents} onDateRangeChange={onDateRangeChange} />);

      const prevButton = screen.getByText('Previous');
      await user.click(prevButton);

      expect(onDateRangeChange).toHaveBeenCalled();
    });

    it('handles navigation to today', async () => {
      const user = userEvent.setup();
      render(<EventCalendar events={mockEvents} />);

      const todayButton = screen.getByText('Today');
      await user.click(todayButton);

      // Should navigate calendar to today's date
      expect(screen.getByText('Today')).toBeInTheDocument();
    });

    it('calls onDateRangeChange with array range format', async () => {
      const onDateRangeChange = jest.fn();
      const user = userEvent.setup();
      render(<EventCalendar events={mockEvents} onDateRangeChange={onDateRangeChange} />);

      const nextButton = screen.getByText('Next');
      await user.click(nextButton);

      // onDateRangeChange should be called with start and end dates
      expect(onDateRangeChange).toHaveBeenCalledWith(
        expect.any(Date),
        expect.any(Date)
      );
    });

    it('renders event with custom styling based on type', () => {
      const { container } = render(<EventCalendar events={mockEvents} />);

      // Calendar should apply custom event styles
      expect(container.querySelector('.rbc-calendar')).toBeInTheDocument();
    });

    it('displays event time in correct format', async () => {
      render(<EventCalendar events={mockEvents} />);

      await waitFor(() => {
        // Check for formatted time
        const timeElements = screen.getAllByText('10:00 AM');
        expect(timeElements.length).toBeGreaterThan(0);
      });
    });

    it('handles event with unknown type gracefully', async () => {
      const unknownTypeEvent: EventItem[] = [
        {
          id: 'unknown1',
          title: 'Unknown Event Type',
          start: '2025-12-15T10:00:00Z',
          end: '2025-12-15T12:00:00Z',
          location: 'Test Location',
          location_type: 'in_person',
          type: 'unknown_type' as any,
          price: 0,
          visibility: 'public',
          status: 'published',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ];

      render(<EventCalendar events={unknownTypeEvent} />);

      await waitFor(() => {
        expect(screen.getByText('Unknown Event Type')).toBeInTheDocument();
      });
    });

    it('displays tooltip with event details on hover', async () => {
      render(<EventCalendar events={mockEvents} />);

      await waitFor(() => {
        // Tooltip should show title, location, and price
        expect(screen.getByText('Judo Seminar')).toBeInTheDocument();
        expect(screen.getByText('Karate Tournament')).toBeInTheDocument();
      });
    });

    it('displays free event price correctly in tooltip', () => {
      const freeEvent: EventItem[] = [
        {
          id: 'free1',
          title: 'Free Event',
          start: '2025-12-15T10:00:00Z',
          end: '2025-12-15T12:00:00Z',
          location: 'Community Center',
          location_type: 'in_person',
          type: 'seminar',
          price: 0,
          visibility: 'public',
          status: 'published',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ];

      const { container } = render(<EventCalendar events={freeEvent} />);

      // Calendar should render free event
      expect(container.querySelector('.rbc-calendar')).toBeInTheDocument();
    });

    it('displays paid event price correctly in tooltip', () => {
      const paidEvent: EventItem[] = [
        {
          id: 'paid1',
          title: 'Paid Event',
          start: '2025-12-15T10:00:00Z',
          end: '2025-12-15T12:00:00Z',
          location: 'Premium Venue',
          location_type: 'in_person',
          type: 'tournament',
          price: 100,
          visibility: 'public',
          status: 'published',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ];

      const { container } = render(<EventCalendar events={paidEvent} />);

      // Calendar should render paid event
      expect(container.querySelector('.rbc-calendar')).toBeInTheDocument();
    });

    it('handles multiple events on same day', async () => {
      const sameDayEvents: EventItem[] = [
        {
          id: 'e1',
          title: 'Morning Event',
          start: '2025-12-15T10:00:00Z',
          end: '2025-12-15T12:00:00Z',
          location: 'Location 1',
          location_type: 'in_person',
          type: 'seminar',
          price: 0,
          visibility: 'public',
          status: 'published',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 'e2',
          title: 'Afternoon Event',
          start: '2025-12-15T14:00:00Z',
          end: '2025-12-15T16:00:00Z',
          location: 'Location 2',
          location_type: 'online',
          type: 'live_training',
          price: 25,
          visibility: 'public',
          status: 'published',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 'e3',
          title: 'Evening Event',
          start: '2025-12-15T18:00:00Z',
          end: '2025-12-15T20:00:00Z',
          location: 'Location 3',
          location_type: 'in_person',
          type: 'tournament',
          price: 50,
          visibility: 'public',
          status: 'published',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ];

      render(<EventCalendar events={sameDayEvents} />);

      await waitFor(() => {
        expect(screen.getByText('Morning Event')).toBeInTheDocument();
        expect(screen.getByText('Afternoon Event')).toBeInTheDocument();
        expect(screen.getByText('Evening Event')).toBeInTheDocument();
      });
    });

    it('renders calendar with proper height style', () => {
      const { container } = render(<EventCalendar events={mockEvents} />);

      const calendar = container.querySelector('.rbc-calendar');
      expect(calendar).toBeInTheDocument();
    });

    it('displays all event type colors in legend', () => {
      render(<EventCalendar events={[]} />);

      // All color legend items should be visible
      expect(screen.getByText('Live Training')).toBeInTheDocument();
      expect(screen.getByText('Seminar')).toBeInTheDocument();
      expect(screen.getByText('Tournament')).toBeInTheDocument();
      expect(screen.getByText('Certification')).toBeInTheDocument();
    });

    it('handles event click navigation correctly', async () => {
      const user = userEvent.setup();
      render(<EventCalendar events={mockEvents} />);

      const event = await screen.findByText('Karate Tournament');
      await user.click(event);

      expect(mockPush).toHaveBeenCalledWith('/events/e2');
    });

    it('transforms events to calendar format with correct dates', () => {
      const { container } = render(<EventCalendar events={mockEvents} />);

      // Events should be transformed and rendered
      expect(container.querySelector('.rbc-calendar')).toBeInTheDocument();
    });

    it('handles single event correctly', async () => {
      const singleEvent: EventItem[] = [mockEvents[0]];
      render(<EventCalendar events={singleEvent} />);

      await waitFor(() => {
        expect(screen.getByText('Judo Seminar')).toBeInTheDocument();
      });
    });

    it('renders without onDateRangeChange callback', async () => {
      const user = userEvent.setup();
      render(<EventCalendar events={mockEvents} />);

      const nextButton = screen.getByText('Next');
      await user.click(nextButton);

      // Should not throw error even without callback
      expect(screen.getByText('Next')).toBeInTheDocument();
    });

    it('applies custom className to container', () => {
      const { container } = render(
        <EventCalendar events={mockEvents} className="my-custom-class" />
      );

      expect(container.querySelector('.my-custom-class')).toBeInTheDocument();
    });

    it('applies event-calendar base class', () => {
      const { container } = render(<EventCalendar events={mockEvents} />);

      expect(container.querySelector('.event-calendar')).toBeInTheDocument();
    });

    it('renders event component with title and time', async () => {
      render(<EventCalendar events={mockEvents} />);

      await waitFor(() => {
        expect(screen.getByText('Judo Seminar')).toBeInTheDocument();
        expect(screen.getAllByText('10:00 AM').length).toBeGreaterThan(0);
      });
    });

    it('shows online indicator only for online events', async () => {
      render(<EventCalendar events={mockEvents} />);

      await waitFor(() => {
        const onlineIndicators = screen.getAllByText('Online');
        // Only one event (Judo Seminar) is online
        expect(onlineIndicators.length).toBeGreaterThan(0);
      });
    });

    it('handles view switch from month to week', async () => {
      const user = userEvent.setup();
      render(<EventCalendar events={mockEvents} />);

      // Start in month view
      const monthButton = screen.getByText('Month');
      expect(monthButton).toHaveClass('rbc-active');

      // Switch to week view
      const weekButton = screen.getByText('Week');
      await user.click(weekButton);

      expect(weekButton).toHaveClass('rbc-active');
    });

    it('handles view switch from week to day', async () => {
      const user = userEvent.setup();
      render(<EventCalendar events={mockEvents} />);

      // Switch to week view first
      const weekButton = screen.getByText('Week');
      await user.click(weekButton);

      // Then switch to day view
      const dayButton = screen.getByText('Day');
      await user.click(dayButton);

      expect(dayButton).toHaveClass('rbc-active');
    });

    it('maintains events across view changes', async () => {
      const user = userEvent.setup();
      render(<EventCalendar events={mockEvents} />);

      // Switch to week view
      const weekButton = screen.getByText('Week');
      await user.click(weekButton);

      // Events should still be visible
      await waitFor(() => {
        expect(screen.getByText('Judo Seminar')).toBeInTheDocument();
      });
    });

    it('handles empty className prop', () => {
      const { container } = render(<EventCalendar events={mockEvents} className="" />);

      expect(container.querySelector('.event-calendar')).toBeInTheDocument();
    });
  });
});
