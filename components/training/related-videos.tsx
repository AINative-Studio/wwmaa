"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Play, Clock, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface RelatedSession {
  id: string;
  title: string;
  description?: string;
  thumbnailUrl?: string;
  duration?: number;
  instructorName: string;
  category?: string;
  requiredTier?: string;
  recordingId?: string;
  recordingUrl?: string;
}

interface RelatedVideosProps {
  sessions: RelatedSession[];
}

export function RelatedVideos({ sessions }: RelatedVideosProps) {
  const [visibleCount, setVisibleCount] = useState(3);

  // Format duration as MM:SS
  const formatDuration = (seconds?: number): string => {
    if (!seconds) return "N/A";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) {
      return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
    }
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const visibleSessions = sessions.slice(0, visibleCount);
  const hasMore = sessions.length > visibleCount;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Related Videos</CardTitle>
        <CardDescription>
          More training sessions you might enjoy
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {visibleSessions.map((session) => (
            <Link
              key={session.id}
              href={`/training/${session.id}/vod`}
              className="block group"
            >
              <div className="flex gap-3 p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
                {/* Thumbnail */}
                <div className="relative w-40 h-24 flex-shrink-0 bg-gray-200 dark:bg-gray-700 rounded overflow-hidden">
                  {session.thumbnailUrl ? (
                    <Image
                      src={session.thumbnailUrl}
                      alt={session.title}
                      fill
                      className="object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Play className="h-8 w-8 text-gray-400" />
                    </div>
                  )}

                  {/* Duration Badge */}
                  {session.duration && (
                    <div className="absolute bottom-1 right-1 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded">
                      {formatDuration(session.duration)}
                    </div>
                  )}

                  {/* Play Overlay */}
                  <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="bg-white/90 rounded-full p-2">
                        <Play className="h-6 w-6 text-gray-900 fill-gray-900" />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-sm line-clamp-2 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors mb-1">
                    {session.title}
                  </h3>

                  {/* Metadata */}
                  <div className="flex flex-col gap-1 text-xs text-gray-600 dark:text-gray-400">
                    <div className="flex items-center gap-1">
                      <User className="h-3 w-3" />
                      <span className="truncate">{session.instructorName}</span>
                    </div>

                    {/* Tags */}
                    <div className="flex items-center gap-2 flex-wrap">
                      {session.category && (
                        <Badge variant="secondary" className="text-xs px-1.5 py-0">
                          {session.category}
                        </Badge>
                      )}
                      {session.requiredTier && session.requiredTier !== "Basic" && (
                        <Badge variant="outline" className="text-xs px-1.5 py-0 border-amber-500 text-amber-700 dark:text-amber-400">
                          {session.requiredTier}
                        </Badge>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </Link>
          ))}

          {/* Load More Button */}
          {hasMore && (
            <Button
              variant="outline"
              className="w-full"
              onClick={() => setVisibleCount((prev) => prev + 3)}
            >
              Load More ({sessions.length - visibleCount} remaining)
            </Button>
          )}

          {/* No more videos */}
          {!hasMore && sessions.length > 3 && (
            <div className="text-center text-sm text-gray-500 dark:text-gray-400 py-2">
              No more videos
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
