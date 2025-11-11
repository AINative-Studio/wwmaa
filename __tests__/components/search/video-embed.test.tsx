import { render, screen } from '@testing-library/react';
import { VideoEmbed } from '@/components/search/video-embed';

describe('VideoEmbed', () => {
  it('renders iframe for valid Cloudflare Stream URL', () => {
    render(<VideoEmbed videoUrl="https://cloudflarestream.com/test-video-id" />);
    const iframe = screen.getByTitle('Video');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', 'https://iframe.cloudflarestream.com/test-video-id');
  });

  it('renders iframe for customer subdomain URL', () => {
    render(
      <VideoEmbed videoUrl="https://customer-xxxxx.cloudflarestream.com/test-video-id/manifest/video.m3u8" />
    );
    const iframe = screen.getByTitle('Video');
    expect(iframe).toBeInTheDocument();
  });

  it('renders iframe for direct video ID', () => {
    render(<VideoEmbed videoUrl="abc123xyz" />);
    const iframe = screen.getByTitle('Video');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', 'https://iframe.cloudflarestream.com/abc123xyz');
  });

  it('renders iframe even for simple string (treats as video ID)', () => {
    // The component treats any simple string without slashes as a video ID
    render(<VideoEmbed videoUrl="not-a-valid-url" />);
    const iframe = screen.getByTitle('Video');
    expect(iframe).toBeInTheDocument();
    expect(iframe).toHaveAttribute('src', 'https://iframe.cloudflarestream.com/not-a-valid-url');
  });

  it('uses custom title when provided', () => {
    render(
      <VideoEmbed
        videoUrl="https://cloudflarestream.com/test-video-id"
        title="Custom Video Title"
      />
    );
    const iframe = screen.getByTitle('Custom Video Title');
    expect(iframe).toBeInTheDocument();
  });

  it('sets iframe attributes correctly', () => {
    render(<VideoEmbed videoUrl="https://cloudflarestream.com/test-video-id" />);
    const iframe = screen.getByTitle('Video') as HTMLIFrameElement;

    expect(iframe).toHaveAttribute('allowfullscreen');
    expect(iframe).toHaveAttribute(
      'allow',
      'accelerometer; gyroscope; autoplay; encrypted-media; picture-in-picture;'
    );
  });

  it('displays loading state initially', () => {
    const { container } = render(<VideoEmbed videoUrl="test-video-id" />);
    // Check for skeleton loading state
    const skeleton = container.querySelector('.animate-pulse');
    expect(skeleton).toBeInTheDocument();
  });
});
