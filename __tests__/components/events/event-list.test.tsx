import { render, screen } from '@testing-library/react';
import { EventList } from '@/components/events/event-list';
import { EventItem } from '@/lib/types';

// Mock EventCard component
jest.mock('@/components/cards/event-card', () => ({
  EventCard: ({ id, title }: { id: string; title: string }) => (
    <div data-testid={`event-card-${id}`}>{title}</div>
  ),
}));

describe('EventList', () => {
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
      teaser: 'Learn advanced techniques',
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
      teaser: 'Compete for the championship',
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    },
  ];

  it('renders event cards in a grid', () => {
    render(<EventList events={mockEvents} />);

    expect(screen.getByTestId('event-card-e1')).toBeInTheDocument();
    expect(screen.getByTestId('event-card-e2')).toBeInTheDocument();
    expect(screen.getByText('Judo Seminar')).toBeInTheDocument();
    expect(screen.getByText('Karate Tournament')).toBeInTheDocument();
  });

  it('displays empty state when no events', () => {
    render(<EventList events={[]} />);

    expect(screen.getByText('No Events Found')).toBeInTheDocument();
    expect(
      screen.getByText(/No events match your current filters/i)
    ).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<EventList events={mockEvents} className="custom-class" />);

    const gridElement = container.querySelector('.custom-class');
    expect(gridElement).toBeInTheDocument();
  });

  it('renders correct number of event cards', () => {
    render(<EventList events={mockEvents} />);

    const eventCards = screen.getAllByTestId(/event-card-/);
    expect(eventCards).toHaveLength(2);
  });

  it('shows calendar icon in empty state', () => {
    const { container } = render(<EventList events={[]} />);

    const svg = container.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });
});
