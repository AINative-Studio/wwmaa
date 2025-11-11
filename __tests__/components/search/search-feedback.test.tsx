import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { SearchFeedback } from '@/components/search/search-feedback';

// Mock the toast hook
const mockToast = jest.fn();
jest.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

// Mock fetch
global.fetch = jest.fn();

describe('SearchFeedback', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({ success: true }),
    });
  });

  it('renders feedback buttons', () => {
    render(<SearchFeedback resultId="test-result-1" />);
    expect(screen.getByText('Was this helpful?')).toBeInTheDocument();
    expect(screen.getByText('Yes, helpful')).toBeInTheDocument();
    expect(screen.getByText('No, not helpful')).toBeInTheDocument();
  });

  it('allows selecting helpful feedback', () => {
    render(<SearchFeedback resultId="test-result-1" />);
    const helpfulButton = screen.getByText('Yes, helpful');
    fireEvent.click(helpfulButton);
    expect(screen.getByPlaceholderText(/Tell us more/)).toBeInTheDocument();
  });

  it('allows selecting not helpful feedback', () => {
    render(<SearchFeedback resultId="test-result-1" />);
    const notHelpfulButton = screen.getByText('No, not helpful');
    fireEvent.click(notHelpfulButton);
    expect(screen.getByPlaceholderText(/Tell us more/)).toBeInTheDocument();
  });

  it('shows comment textarea after selecting feedback', () => {
    render(<SearchFeedback resultId="test-result-1" />);
    const helpfulButton = screen.getByText('Yes, helpful');
    fireEvent.click(helpfulButton);
    expect(screen.getByLabelText(/Additional feedback/)).toBeInTheDocument();
  });

  it('allows submitting feedback without comment', async () => {
    render(<SearchFeedback resultId="test-result-1" />);

    // Select helpful
    fireEvent.click(screen.getByText('Yes, helpful'));

    // Submit
    const submitButton = screen.getByText('Submit Feedback');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/search/feedback',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            resultId: 'test-result-1',
            helpful: true,
          }),
        })
      );
    });

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Thank you for your feedback!',
        })
      );
    });
  });

  it('allows submitting feedback with comment', async () => {
    render(<SearchFeedback resultId="test-result-1" />);

    // Select not helpful
    fireEvent.click(screen.getByText('No, not helpful'));

    // Add comment
    const textarea = screen.getByPlaceholderText(/Tell us more/);
    fireEvent.change(textarea, { target: { value: 'Needs more detail' } });

    // Submit
    const submitButton = screen.getByText('Submit Feedback');
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/search/feedback',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            resultId: 'test-result-1',
            helpful: false,
            comment: 'Needs more detail',
          }),
        })
      );
    });
  });

  it('shows thank you message after submission', async () => {
    render(<SearchFeedback resultId="test-result-1" />);

    fireEvent.click(screen.getByText('Yes, helpful'));
    fireEvent.click(screen.getByText('Submit Feedback'));

    await waitFor(() => {
      expect(screen.getByText('Thank you for your feedback!')).toBeInTheDocument();
    });
  });

  it('handles submission error', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
    });

    render(<SearchFeedback resultId="test-result-1" />);

    fireEvent.click(screen.getByText('Yes, helpful'));
    fireEvent.click(screen.getByText('Submit Feedback'));

    await waitFor(() => {
      expect(mockToast).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Failed to submit feedback',
          variant: 'destructive',
        })
      );
    });
  });

  it('shows loading state while submitting', async () => {
    (global.fetch as jest.Mock).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ ok: true }), 100))
    );

    render(<SearchFeedback resultId="test-result-1" />);

    fireEvent.click(screen.getByText('Yes, helpful'));
    fireEvent.click(screen.getByText('Submit Feedback'));

    expect(screen.getByText('Submitting...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByText('Submitting...')).not.toBeInTheDocument();
    });
  });

  it('prevents submission without selecting feedback', () => {
    render(<SearchFeedback resultId="test-result-1" />);
    expect(screen.queryByText('Submit Feedback')).not.toBeInTheDocument();
  });

  it('allows toggling feedback selection', () => {
    render(<SearchFeedback resultId="test-result-1" />);

    // Select helpful
    fireEvent.click(screen.getByText('Yes, helpful'));
    expect(screen.getByPlaceholderText(/Tell us more/)).toBeInTheDocument();

    // Click again to deselect
    fireEvent.click(screen.getByText('Yes, helpful'));
    expect(screen.queryByPlaceholderText(/Tell us more/)).not.toBeInTheDocument();
  });
});
