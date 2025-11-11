import { render, screen, fireEvent } from '@testing-library/react';
import { SearchError } from '@/components/search/search-error';

describe('SearchError', () => {
  it('renders error message', () => {
    render(<SearchError message="Test error message" />);
    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('displays timeout error title for timeout errors', () => {
    render(<SearchError message="Search timed out. Please try again." />);
    expect(screen.getByText('Search Timeout')).toBeInTheDocument();
  });

  it('displays network error title for network errors', () => {
    render(<SearchError message="Network error occurred" />);
    expect(screen.getByText('Network Error')).toBeInTheDocument();
  });

  it('displays server error title for server errors', () => {
    render(<SearchError message="Server error occurred" />);
    expect(screen.getByText('Server Error')).toBeInTheDocument();
  });

  it('displays generic error title for other errors', () => {
    render(<SearchError message="Something went wrong" />);
    expect(screen.getByText('Search Error')).toBeInTheDocument();
  });

  it('shows suggestions for timeout errors', () => {
    render(<SearchError message="Search timed out" />);
    expect(screen.getByText('Suggestions:')).toBeInTheDocument();
    expect(screen.getByText('Try a simpler search query')).toBeInTheDocument();
    expect(screen.getByText('Check your internet connection')).toBeInTheDocument();
  });

  it('shows suggestions for network errors', () => {
    render(<SearchError message="Network connection failed" />);
    expect(screen.getByText('Suggestions:')).toBeInTheDocument();
    expect(screen.getByText('Check your internet connection')).toBeInTheDocument();
    expect(screen.getByText('Try again in a moment')).toBeInTheDocument();
  });

  it('shows suggestions for server errors', () => {
    render(<SearchError message="Internal server error" />);
    expect(screen.getByText('Suggestions:')).toBeInTheDocument();
    expect(screen.getByText('Our servers may be experiencing issues')).toBeInTheDocument();
    expect(screen.getByText('Please try again later')).toBeInTheDocument();
  });

  it('renders retry button when onRetry is provided', () => {
    const mockRetry = jest.fn();
    render(<SearchError message="Test error" onRetry={mockRetry} />);
    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument();
  });

  it('does not render retry button when onRetry is not provided', () => {
    render(<SearchError message="Test error" />);
    expect(screen.queryByRole('button', { name: /try again/i })).not.toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', () => {
    const mockRetry = jest.fn();
    render(<SearchError message="Test error" onRetry={mockRetry} />);

    const retryButton = screen.getByRole('button', { name: /try again/i });
    fireEvent.click(retryButton);

    expect(mockRetry).toHaveBeenCalledTimes(1);
  });

  it('displays alert with destructive variant', () => {
    const { container } = render(<SearchError message="Test error" />);
    const alert = container.querySelector('[role="alert"]');
    expect(alert).toBeInTheDocument();
  });
});
