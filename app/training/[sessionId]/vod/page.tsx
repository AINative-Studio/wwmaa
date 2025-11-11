import { Metadata } from "next";
import { redirect } from "next/navigation";
import { VODPlayer } from "@/components/training/vod-player";
import { TranscriptPanel } from "@/components/training/transcript-panel";
import { BookmarksPanel } from "@/components/training/bookmarks-panel";
import { RelatedVideos } from "@/components/training/related-videos";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Lock, Crown } from "lucide-react";
import Link from "next/link";

interface VODPageProps {
  params: {
    sessionId: string;
  };
}

export const metadata: Metadata = {
  title: "Training Session Recording | WWMAA",
  description: "Watch recorded training session",
};

interface SessionData {
  id: string;
  title: string;
  description: string;
  eventId: string;
  startDatetime: string;
  endDatetime: string;
  instructorName: string;
  instructorId: string;
  recordingUrl?: string;
  recordingId?: string;
  thumbnailUrl?: string;
  duration?: number;
  requiredTier: string;
  transcriptUrl?: string;
  category?: string;
}

interface AccessCheck {
  hasAccess: boolean;
  reason?: string;
  userId?: string;
  userName?: string;
  userTier?: string;
  isAuthenticated: boolean;
}

async function getSessionData(sessionId: string): Promise<SessionData | null> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/training/sessions/${sessionId}`,
      {
        cache: "no-store",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching session data:", error);
    return null;
  }
}

async function checkUserAccess(sessionId: string): Promise<AccessCheck> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/training/sessions/${sessionId}/vod-access`,
      {
        cache: "no-store",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      }
    );

    if (!response.ok) {
      return { hasAccess: false, reason: "unauthorized", isAuthenticated: false };
    }

    return await response.json();
  } catch (error) {
    console.error("Error checking user access:", error);
    return { hasAccess: false, reason: "error", isAuthenticated: false };
  }
}

async function getSignedStreamUrl(recordingId: string, sessionId: string): Promise<string | null> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/training/sessions/${sessionId}/stream-url`,
      {
        cache: "no-store",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      }
    );

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    return data.signedUrl;
  } catch (error) {
    console.error("Error getting signed stream URL:", error);
    return null;
  }
}

async function getRelatedSessions(sessionId: string, category?: string, instructorId?: string): Promise<any[]> {
  try {
    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (instructorId) params.append("instructorId", instructorId);
    params.append("limit", "6");
    params.append("exclude", sessionId);

    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/training/sessions/related?${params.toString()}`,
      {
        cache: "no-store",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      return [];
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching related sessions:", error);
    return [];
  }
}

async function getWatchProgress(sessionId: string): Promise<{ position: number; completed: boolean } | null> {
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/training/${sessionId}/progress`,
      {
        cache: "no-store",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
      }
    );

    if (!response.ok) {
      return null;
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching watch progress:", error);
    return null;
  }
}

export default async function VODPage({ params }: VODPageProps) {
  const { sessionId } = params;

  // Fetch session data
  const sessionData = await getSessionData(sessionId);

  if (!sessionData) {
    redirect("/events?error=session-not-found");
  }

  // Check if recording is available
  if (!sessionData.recordingId && !sessionData.recordingUrl) {
    redirect(`/events/${sessionData.eventId}?error=recording-not-available`);
  }

  // Check user access
  const accessCheck = await checkUserAccess(sessionId);

  // Redirect to login if not authenticated
  if (!accessCheck.isAuthenticated) {
    redirect(`/login?redirect=/training/${sessionId}/vod`);
  }

  // Check tier-based access
  if (!accessCheck.hasAccess) {
    if (accessCheck.reason === "tier-insufficient") {
      return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
          <div className="container mx-auto px-4 py-12 max-w-4xl">
            <Alert className="mb-8 border-amber-500 bg-amber-50 dark:bg-amber-950">
              <Crown className="h-4 w-4 text-amber-600" />
              <AlertTitle>Premium Content</AlertTitle>
              <AlertDescription>
                This training session is only available to {sessionData.requiredTier} members.
                Your current tier: {accessCheck.userTier || "Basic"}
              </AlertDescription>
            </Alert>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 text-center">
              <Lock className="h-16 w-16 mx-auto mb-4 text-gray-400" />
              <h1 className="text-3xl font-bold mb-4">{sessionData.title}</h1>
              <p className="text-gray-600 dark:text-gray-300 mb-8">
                Upgrade your membership to access this exclusive training content.
              </p>
              <div className="flex gap-4 justify-center">
                <Button asChild size="lg">
                  <Link href="/membership/upgrade">
                    <Crown className="mr-2 h-5 w-5" />
                    Upgrade Membership
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg">
                  <Link href="/events">Browse Events</Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      );
    } else {
      redirect(`/events/${sessionData.eventId}?error=access-denied`);
    }
  }

  // Get signed stream URL
  const signedStreamUrl = sessionData.recordingId
    ? await getSignedStreamUrl(sessionData.recordingId, sessionId)
    : sessionData.recordingUrl;

  if (!signedStreamUrl) {
    redirect(`/events/${sessionData.eventId}?error=stream-unavailable`);
  }

  // Get related sessions
  const relatedSessions = await getRelatedSessions(
    sessionId,
    sessionData.category,
    sessionData.instructorId
  );

  // Get watch progress
  const watchProgress = await getWatchProgress(sessionId);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">{sessionData.title}</h1>
          <p className="text-gray-600 dark:text-gray-300">
            Instructor: {sessionData.instructorName}
          </p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Video Player Column */}
          <div className="lg:col-span-2 space-y-6">
            <VODPlayer
              sessionId={sessionId}
              streamUrl={signedStreamUrl}
              title={sessionData.title}
              duration={sessionData.duration}
              thumbnailUrl={sessionData.thumbnailUrl}
              initialPosition={watchProgress?.position || 0}
              userId={accessCheck.userId!}
            />

            {/* Description */}
            <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
              <h2 className="text-xl font-semibold mb-4">About this session</h2>
              <p className="text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                {sessionData.description}
              </p>
            </div>

            {/* Transcript Panel */}
            {sessionData.transcriptUrl && (
              <TranscriptPanel
                sessionId={sessionId}
                transcriptUrl={sessionData.transcriptUrl}
              />
            )}
          </div>

          {/* Sidebar Column */}
          <div className="space-y-6">
            {/* Bookmarks Panel */}
            <BookmarksPanel
              sessionId={sessionId}
              userId={accessCheck.userId!}
            />

            {/* Related Videos */}
            {relatedSessions.length > 0 && (
              <RelatedVideos sessions={relatedSessions} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
