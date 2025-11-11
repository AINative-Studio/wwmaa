import { Metadata } from "next";
import { redirect } from "next/navigation";
import { RTCInterface } from "@/components/training/rtc-interface";

interface LiveSessionPageProps {
  params: {
    sessionId: string;
  };
  searchParams: {
    token?: string;
  };
}

export const metadata: Metadata = {
  title: "Live Training Session | WWMAA",
  description: "Join your live training session",
};

async function getSessionData(sessionId: string) {
  // In production, this would fetch from your backend API
  // For now, we'll return mock data structure
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/training/sessions/${sessionId}`,
      {
        cache: "no-store",
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

async function checkUserAccess(sessionId: string) {
  // In production, this would check user authentication and payment status
  // For now, we'll return a mock structure
  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/training/sessions/${sessionId}/access`,
      {
        cache: "no-store",
      }
    );

    if (!response.ok) {
      return { hasAccess: false, reason: "unauthorized" };
    }

    return await response.json();
  } catch (error) {
    console.error("Error checking user access:", error);
    return { hasAccess: false, reason: "error" };
  }
}

export default async function LiveSessionPage({
  params,
  searchParams,
}: LiveSessionPageProps) {
  const { sessionId } = params;

  // Fetch session data
  const sessionData = await getSessionData(sessionId);

  if (!sessionData) {
    redirect("/events?error=session-not-found");
  }

  // Check if session is live
  const now = new Date();
  const startTime = new Date(sessionData.startDatetime);
  const endTime = new Date(sessionData.endDatetime);

  if (now < startTime) {
    redirect(`/events/${sessionData.eventId}?error=session-not-started`);
  }

  if (now > endTime) {
    redirect(`/events/${sessionData.eventId}?error=session-ended`);
  }

  // Check user access
  const accessCheck = await checkUserAccess(sessionId);

  if (!accessCheck.hasAccess) {
    if (accessCheck.reason === "unauthorized") {
      redirect(`/login?redirect=/training/${sessionId}/live`);
    } else if (accessCheck.reason === "payment-required") {
      redirect(`/checkout?eventId=${sessionData.eventId}`);
    } else if (accessCheck.reason === "terms-not-accepted") {
      redirect(`/events/${sessionData.eventId}?error=terms-required`);
    } else {
      redirect(`/events/${sessionData.eventId}?error=access-denied`);
    }
  }

  // Generate Cloudflare Calls URL (in production)
  // For now, we'll pass the session data to the RTC interface
  const callsConfig = {
    sessionId: sessionData.id,
    userId: accessCheck.userId,
    userName: accessCheck.userName,
    userRole: accessCheck.userRole,
    isInstructor: accessCheck.isInstructor || false,
    // In production, these would be generated server-side
    callsUrl: searchParams.token
      ? `https://calls.cloudflare.com/${sessionId}?token=${searchParams.token}`
      : undefined,
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <RTCInterface
        sessionId={sessionId}
        sessionTitle={sessionData.title}
        eventId={sessionData.eventId}
        config={callsConfig}
        startDatetime={sessionData.startDatetime}
        endDatetime={sessionData.endDatetime}
      />
    </div>
  );
}
