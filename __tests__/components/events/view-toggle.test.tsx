import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ViewToggle } from '@/components/events/view-toggle';

describe('ViewToggle', () => {
  const mockOnViewChange = jest.fn();

  beforeEach(() => {
    mockOnViewChange.mockClear();
  });

  it('renders list and calendar buttons', () => {
    render(<ViewToggle view="list" onViewChange={mockOnViewChange} />);

    expect(screen.getByLabelText('List view')).toBeInTheDocument();
    expect(screen.getByLabelText('Calendar view')).toBeInTheDocument();
  });

  it('shows active state for list view', () => {
    render(<ViewToggle view="list" onViewChange={mockOnViewChange} />);

    const listButton = screen.getByLabelText('List view');
    expect(listButton).toHaveAttribute('data-state', 'on');
  });

  it('shows active state for calendar view', () => {
    render(<ViewToggle view="calendar" onViewChange={mockOnViewChange} />);

    const calendarButton = screen.getByLabelText('Calendar view');
    expect(calendarButton).toHaveAttribute('data-state', 'on');
  });

  it('calls onViewChange when clicking list button', async () => {
    const user = userEvent.setup();
    render(<ViewToggle view="calendar" onViewChange={mockOnViewChange} />);

    const listButton = screen.getByLabelText('List view');
    await user.click(listButton);

    expect(mockOnViewChange).toHaveBeenCalledWith('list');
  });

  it('calls onViewChange when clicking calendar button', async () => {
    const user = userEvent.setup();
    render(<ViewToggle view="list" onViewChange={mockOnViewChange} />);

    const calendarButton = screen.getByLabelText('Calendar view');
    await user.click(calendarButton);

    expect(mockOnViewChange).toHaveBeenCalledWith('calendar');
  });

  it('does not call onViewChange when clicking already active view', async () => {
    const user = userEvent.setup();
    render(<ViewToggle view="list" onViewChange={mockOnViewChange} />);

    const listButton = screen.getByLabelText('List view');
    await user.click(listButton);

    // Should not call because it's already the active view
    expect(mockOnViewChange).not.toHaveBeenCalled();
  });

  it('renders icons for list and calendar', () => {
    const { container } = render(<ViewToggle view="list" onViewChange={mockOnViewChange} />);

    // Check for lucide-react icons (they render as SVGs)
    const svgs = container.querySelectorAll('svg');
    expect(svgs.length).toBeGreaterThanOrEqual(2);
  });
});
