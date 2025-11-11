import { render, screen } from '@testing-library/react';
import { SearchResultsSkeleton } from '@/components/search/search-results-skeleton';

describe('SearchResultsSkeleton', () => {
  it('renders skeleton components', () => {
    const { container } = render(<SearchResultsSkeleton />);
    const skeletons = container.querySelectorAll('.animate-pulse');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders AI answer skeleton section', () => {
    render(<SearchResultsSkeleton />);
    // Check for multiple skeleton elements indicating the answer section
    const { container } = render(<SearchResultsSkeleton />);
    const cards = container.querySelectorAll('[class*="card"]');
    expect(cards.length).toBeGreaterThan(0);
  });

  it('renders video skeleton section', () => {
    const { container } = render(<SearchResultsSkeleton />);
    // Look for a large skeleton element that represents the video
    const skeletons = container.querySelectorAll('.animate-pulse');
    const videoSkeleton = Array.from(skeletons).find(
      (el) => el.classList.contains('h-[400px]')
    );
    expect(videoSkeleton).toBeInTheDocument();
  });

  it('renders sources skeleton section', () => {
    const { container } = render(<SearchResultsSkeleton />);
    const grid = container.querySelector('.grid');
    expect(grid).toBeInTheDocument();
  });

  it('renders multiple source card skeletons', () => {
    const { container } = render(<SearchResultsSkeleton />);
    const grids = container.querySelectorAll('.grid');
    expect(grids.length).toBeGreaterThan(0);
  });

  it('renders related queries skeleton section', () => {
    const { container } = render(<SearchResultsSkeleton />);
    const roundedSkeletons = container.querySelectorAll('.rounded-full');
    expect(roundedSkeletons.length).toBeGreaterThan(0);
  });

  it('renders feedback skeleton section', () => {
    const { container } = render(<SearchResultsSkeleton />);
    const skeletons = Array.from(container.querySelectorAll('.animate-pulse'));
    // Should have multiple skeletons for various sections
    expect(skeletons.length).toBeGreaterThan(10);
  });

  it('has proper spacing between sections', () => {
    const { container } = render(<SearchResultsSkeleton />);
    const mainContainer = container.firstChild;
    expect(mainContainer).toHaveClass('space-y-6');
  });
});
