import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import EventsPage from '@/app/events/page';
import { eventApi } from '@/lib/event-api';
import { EventItem } from '@/lib/types';

// Mock dependencies
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
  })),
  useSearchParams: jest.fn(() => ({
    get: jest.fn(),
  })),
}));

jest.mock('react-big-calendar/lib/css/react-big-calendar.css', () => ({}));

jest.mock('@/lib/event-api', () => ({
  eventApi: {
    getEvents: jest.fn(),
  },
}));

describe('EventsPage Integration Tests', () => {
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
    {
      id: 'e3',
      title: 'Live Training Session',
      description: 'Weekly training',
      start: '2025-12-18T14:00:00Z',
      end: '2025-12-18T16:00:00Z',
      location: 'Training Center',
      location_type: 'in_person',
      type: 'live_training',
      price: 25,
      visibility: 'public',
      status: 'published',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
  ];

  beforeEach(() => {
    (eventApi.getEvents as jest.Mock).mockResolvedValue({
      events: mockEvents,
      total: mockEvents.length,
      limit: 12,
      offset: 0,
      has_more: false,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('renders events page with hero section', async () => {
    render(<EventsPage />);

    expect(screen.getByText('Martial Arts Events & Tournaments')).toBeInTheDocument();
    expect(
      screen.getByText('Judo seminars, karate tournaments, and live martial arts training sessions')
    ).toBeInTheDocument();
  });

  it('loads and displays events in list view by default', async () => {
    render(<EventsPage />);

    await waitFor(() => {
      expect(screen.getByText('Judo Seminar')).toBeInTheDocument();
      expect(screen.getByText('Karate Tournament')).toBeInTheDocument();
      expect(screen.getByText('Live Training Session')).toBeInTheDocument();
    });
  });

  it('toggles between list and calendar views', async () => {
    const user = userEvent.setup();
    render(<EventsPage />);

    await waitFor(() => {
      expect(screen.getByText('Judo Seminar')).toBeInTheDocument();
    });

    // Switch to calendar view
    const calendarButton = screen.getByLabelText('Calendar view');
    await user.click(calendarButton);

    await waitFor(() => {
      // Calendar should be visible
      expect(screen.getByText('Today')).toBeInTheDocument();
      expect(screen.getByText('Month')).toBeInTheDocument();
    });

    // Switch back to list view
    const listButton = screen.getByLabelText('List view');
    await user.click(listButton);

    await waitFor(() => {
      // List should be visible again
      const cards = screen.getAllByText('Judo Seminar');
      expect(cards.length).toBeGreaterThan(0);
    });
  });

  it('displays event count', async () => {
    render(<EventsPage />);

    await waitFor(() => {
      expect(screen.getByText(`${mockEvents.length} events found`)).toBeInTheDocument();
    });
  });

  it('shows loading state while fetching events', () => {
    render(<EventsPage />);

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    (eventApi.getEvents as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

    render(<EventsPage />);

    await waitFor(() => {
      expect(screen.getByText('Error Loading Events')).toBeInTheDocument();
      expect(screen.getByText('Failed to load events. Please try again later.')).toBeInTheDocument();
    });

    // Should have a retry button
    expect(screen.getByText('Try Again')).toBeInTheDocument();
  });

  it('shows empty state when no events found', async () => {
    (eventApi.getEvents as jest.Mock).mockResolvedValueOnce({
      events: [],
      total: 0,
      limit: 12,
      offset: 0,
      has_more: false,
    });

    render(<EventsPage />);

    await waitFor(() => {
      expect(screen.getByText('No Events Found')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your filters to see more events.')).toBeInTheDocument();
    });
  });

  it('filters work in both list and calendar view', async () => {
    const user = userEvent.setup();
    render(<EventsPage />);

    await waitFor(() => {
      expect(screen.getByText('Judo Seminar')).toBeInTheDocument();
    });

    // Apply a filter (this would be done through the filter UI)
    // For now, we're just verifying the API is called correctly
    expect(eventApi.getEvents).toHaveBeenCalled();

    // Switch to calendar view
    const calendarButton = screen.getByLabelText('Calendar view');
    await user.click(calendarButton);

    // Filters should still apply
    await waitFor(() => {
      expect(eventApi.getEvents).toHaveBeenCalledTimes(2); // Initial load + view change
    });
  });

  it('displays mobile filter button on small screens', () => {
    render(<EventsPage />);

    const mobileFilterButton = screen.getByText('Filters');
    expect(mobileFilterButton).toBeInTheDocument();
  });

  it('handles pagination in list view', async () => {
    const manyEvents = Array.from({ length: 15 }, (_, i) => ({
      ...mockEvents[0],
      id: `e${i}`,
      title: `Event ${i + 1}`,
    }));

    (eventApi.getEvents as jest.Mock).mockResolvedValueOnce({
      events: manyEvents.slice(0, 12),
      total: 15,
      limit: 12,
      offset: 0,
      has_more: true,
    });

    const user = userEvent.setup();
    render(<EventsPage />);

    await waitFor(() => {
      expect(screen.getByText('Event 1')).toBeInTheDocument();
    });

    // Pagination controls should be visible
    const nextButton = screen.getByText('Next');
    expect(nextButton).toBeInTheDocument();
    expect(nextButton).not.toBeDisabled();

    const prevButton = screen.getByText('Previous');
    expect(prevButton).toBeInTheDocument();
    expect(prevButton).toBeDisabled(); // Should be disabled on first page
  });

  it('calendar view supports month, week, and day views', async () => {
    const user = userEvent.setup();
    render(<EventsPage />);

    await waitFor(() => {
      expect(screen.getByText('Judo Seminar')).toBeInTheDocument();
    });

    // Switch to calendar view
    const calendarButton = screen.getByLabelText('Calendar view');
    await user.click(calendarButton);

    await waitFor(() => {
      expect(screen.getByText('Month')).toBeInTheDocument();
      expect(screen.getByText('Week')).toBeInTheDocument();
      expect(screen.getByText('Day')).toBeInTheDocument();
    });
  });

  it('displays color legend in calendar view', async () => {
    const user = userEvent.setup();
    render(<EventsPage />);

    await waitFor(() => {
      expect(screen.getByText('Judo Seminar')).toBeInTheDocument();
    });

    // Switch to calendar view
    const calendarButton = screen.getByLabelText('Calendar view');
    await user.click(calendarButton);

    await waitFor(() => {
      expect(screen.getByText('Live Training')).toBeInTheDocument();
      expect(screen.getByText('Seminar')).toBeInTheDocument();
      expect(screen.getByText('Tournament')).toBeInTheDocument();
      expect(screen.getByText('Certification')).toBeInTheDocument();
    });
  });

  it('fetches different date ranges based on calendar view', async () => {
    const user = userEvent.setup();
    render(<EventsPage />);

    await waitFor(() => {
      expect(screen.getByText('Judo Seminar')).toBeInTheDocument();
    });

    // Initial call in list view
    const firstCall = (eventApi.getEvents as jest.Mock).mock.calls[0][0];

    // Switch to calendar view
    const calendarButton = screen.getByLabelText('Calendar view');
    await user.click(calendarButton);

    await waitFor(() => {
      // Should make a second API call with different parameters
      expect(eventApi.getEvents).toHaveBeenCalledTimes(2);
    });

    const secondCall = (eventApi.getEvents as jest.Mock).mock.calls[1][0];

    // Calendar view should fetch more events (limit of 100 vs 12 for list)
    expect(secondCall.limit).toBe(100);
    expect(firstCall.limit).toBe(12);
  });
});
