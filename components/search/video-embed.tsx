'use client';

import { useState } from 'react';
import { Play } from 'lucide-react';
import { AspectRatio } from '@/components/ui/aspect-ratio';
import { Skeleton } from '@/components/ui/skeleton';

interface VideoEmbedProps {
  videoUrl: string;
  title?: string;
}

export function VideoEmbed({ videoUrl, title = 'Video' }: VideoEmbedProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  // Extract video ID from Cloudflare Stream URL
  const getVideoId = (url: string): string | null => {
    // Support various Cloudflare Stream URL formats
    // https://customer-XXXXX.cloudflarestream.com/VIDEO_ID/manifest/video.m3u8
    // https://cloudflarestream.com/VIDEO_ID/manifest/video.m3u8
    // https://iframe.cloudflarestream.com/VIDEO_ID

    try {
      const streamMatch = url.match(/cloudflarestream\.com\/([^/]+)/);
      if (streamMatch) {
        return streamMatch[1];
      }

      // If it's already just an ID (alphanumeric, dashes, underscores), return it
      if (/^[a-zA-Z0-9_-]+$/.test(url)) {
        return url;
      }

      return null;
    } catch {
      return null;
    }
  };

  const videoId = getVideoId(videoUrl);

  if (!videoId) {
    return (
      <div className="bg-muted rounded-lg p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Invalid video URL format
        </p>
      </div>
    );
  }

  if (hasError) {
    return (
      <div className="bg-muted rounded-lg p-8 text-center">
        <p className="text-sm text-muted-foreground">
          Failed to load video. Please try again later.
        </p>
      </div>
    );
  }

  const embedUrl = `https://iframe.cloudflarestream.com/${videoId}`;

  return (
    <AspectRatio ratio={16 / 9} className="bg-muted rounded-lg overflow-hidden">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <Skeleton className="w-full h-full" />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="bg-background/80 rounded-full p-4">
              <Play className="h-12 w-12 text-muted-foreground" />
            </div>
          </div>
        </div>
      )}
      <iframe
        src={embedUrl}
        title={title}
        allow="accelerometer; gyroscope; autoplay; encrypted-media; picture-in-picture;"
        allowFullScreen
        className="absolute inset-0 w-full h-full"
        onLoad={() => setIsLoading(false)}
        onError={() => {
          setIsLoading(false);
          setHasError(true);
        }}
      />
    </AspectRatio>
  );
}
