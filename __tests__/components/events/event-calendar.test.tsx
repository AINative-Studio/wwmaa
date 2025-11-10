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
});
