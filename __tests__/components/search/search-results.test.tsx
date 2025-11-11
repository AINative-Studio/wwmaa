import { render, screen, fireEvent } from '@testing-library/react';
import { SearchResults } from '@/components/search/search-results';
import { SearchResult } from '@/components/search/types';

// Mock the child components
jest.mock('@/components/search/video-embed', () => ({
  VideoEmbed: ({ videoUrl }: { videoUrl: string }) => (
    <div data-testid="video-embed">{videoUrl}</div>
  ),
}));

jest.mock('@/components/search/image-gallery', () => ({
  ImageGallery: ({ images }: { images: any[] }) => (
    <div data-testid="image-gallery">{images.length} images</div>
  ),
}));

jest.mock('@/components/search/search-feedback', () => ({
  SearchFeedback: ({ resultId }: { resultId: string }) => (
    <div data-testid="search-feedback">{resultId}</div>
  ),
}));

const mockResult: SearchResult = {
  id: 'test-result-1',
  query: 'test query',
  answer: '# Test Answer\n\nThis is a test answer with **bold** text.',
  sources: [
    {
      id: 'source-1',
      title: 'Test Source 1',
      url: 'https://example.com/1',
      snippet: 'Test snippet 1',
    },
    {
      id: 'source-2',
      title: 'Test Source 2',
      url: 'https://example.com/2',
      snippet: 'Test snippet 2',
    },
  ],
  relatedQueries: ['related query 1', 'related query 2'],
  timestamp: new Date().toISOString(),
};

describe('SearchResults', () => {
  it('renders the AI answer', () => {
    render(<SearchResults result={mockResult} />);
    expect(screen.getByText('AI Answer')).toBeInTheDocument();
  });

  it('renders markdown content correctly', () => {
    render(<SearchResults result={mockResult} />);
    expect(screen.getByText(/This is a test answer/)).toBeInTheDocument();
  });

  it('renders sources when provided', () => {
    render(<SearchResults result={mockResult} />);
    expect(screen.getByText('Sources')).toBeInTheDocument();
    expect(screen.getByText('Test Source 1')).toBeInTheDocument();
    expect(screen.getByText('Test Source 2')).toBeInTheDocument();
  });

  it('renders source links with correct URLs', () => {
    render(<SearchResults result={mockResult} />);
    const links = screen.getAllByRole('link');
    const sourceLinks = links.filter(link =>
      link.getAttribute('href')?.includes('example.com')
    );
    expect(sourceLinks.length).toBeGreaterThan(0);
  });

  it('renders related queries when provided', () => {
    render(<SearchResults result={mockResult} />);
    expect(screen.getByText('Related Searches')).toBeInTheDocument();
    expect(screen.getByText('related query 1')).toBeInTheDocument();
    expect(screen.getByText('related query 2')).toBeInTheDocument();
  });

  it('renders video embed when videoUrl is provided', () => {
    const resultWithVideo = {
      ...mockResult,
      videoUrl: 'https://cloudflarestream.com/test-video',
    };
    render(<SearchResults result={resultWithVideo} />);
    expect(screen.getByTestId('video-embed')).toBeInTheDocument();
  });

  it('does not render video section when videoUrl is not provided', () => {
    render(<SearchResults result={mockResult} />);
    expect(screen.queryByTestId('video-embed')).not.toBeInTheDocument();
  });

  it('renders image gallery when images are provided', () => {
    const resultWithImages = {
      ...mockResult,
      images: [
        {
          id: 'img-1',
          url: 'https://example.com/image1.jpg',
          alt: 'Test image 1',
        },
        {
          id: 'img-2',
          url: 'https://example.com/image2.jpg',
          alt: 'Test image 2',
        },
      ],
    };
    render(<SearchResults result={resultWithImages} />);
    expect(screen.getByTestId('image-gallery')).toBeInTheDocument();
  });

  it('does not render image gallery when images are not provided', () => {
    render(<SearchResults result={mockResult} />);
    expect(screen.queryByTestId('image-gallery')).not.toBeInTheDocument();
  });

  it('renders search feedback component', () => {
    render(<SearchResults result={mockResult} />);
    expect(screen.getByTestId('search-feedback')).toBeInTheDocument();
  });

  it('allows collapsing and expanding the answer', () => {
    render(<SearchResults result={mockResult} />);
    const collapseButton = screen.getByRole('button', { name: /collapse/i });
    fireEvent.click(collapseButton);
    expect(screen.getByRole('button', { name: /expand/i })).toBeInTheDocument();
  });

  it('does not render sources section when no sources provided', () => {
    const resultWithoutSources = {
      ...mockResult,
      sources: undefined,
    };
    render(<SearchResults result={resultWithoutSources} />);
    expect(screen.queryByText('Sources')).not.toBeInTheDocument();
  });

  it('does not render related queries when none provided', () => {
    const resultWithoutRelated = {
      ...mockResult,
      relatedQueries: undefined,
    };
    render(<SearchResults result={resultWithoutRelated} />);
    expect(screen.queryByText('Related Searches')).not.toBeInTheDocument();
  });
});
