import { Metadata } from "next";
import { notFound } from "next/navigation";
import { EventHero } from "@/components/events/event-hero";
import { EventDetails } from "@/components/events/event-details";
import { EventMap } from "@/components/events/event-map";
import { ShareButtons } from "@/components/events/share-buttons";
import { AddToCalendar } from "@/components/events/add-to-calendar";
import { RelatedEvents } from "@/components/events/related-events";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

interface EventPageProps {
  params: {
    id: string;
  };
}

// Fetch event data
async function getEvent(id: string) {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const response = await fetch(`${apiUrl}/api/events/${id}`, {
      cache: "no-store", // Always fetch fresh data
    });

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`Failed to fetch event: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error fetching event:", error);
    return null;
  }
}

// Generate metadata for SEO
export async function generateMetadata({
  params,
}: EventPageProps): Promise<Metadata> {
  const data = await getEvent(params.id);

  if (!data || !data.event) {
    return {
      title: "Event Not Found | WWMAA",
      description: "The requested event could not be found.",
    };
  }

  const event = data.event;
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://wwmaa.ainative.studio";
  const eventUrl = `${siteUrl}/events/${params.id}`;

  // Format date for description
  const startDate = new Date(event.start_datetime);
  const formattedDate = startDate.toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  });

  // Build description
  const description =
    event.description
      ?.replace(/<[^>]*>/g, "")
      .substring(0, 160) ||
    `Join us for ${event.title} on ${formattedDate}. ${event.is_virtual ? "Virtual event" : event.location_name || "Event"} hosted by WWMAA.`;

  return {
    title: `${event.title} | WWMAA Events`,
    description,
    openGraph: {
      title: event.title,
      description,
      type: "website",
      url: eventUrl,
      images: event.featured_image_url
        ? [
            {
              url: event.featured_image_url,
              width: 1200,
              height: 630,
              alt: event.title,
            },
          ]
        : [
            {
              url: `${siteUrl}/images/logo.png`,
              width: 1200,
              height: 630,
              alt: "WWMAA",
            },
          ],
      siteName: "Women's Martial Arts Association of America",
    },
    twitter: {
      card: "summary_large_image",
      title: event.title,
      description,
      images: event.featured_image_url
        ? [event.featured_image_url]
        : [`${siteUrl}/images/logo.png`],
    },
    alternates: {
      canonical: eventUrl,
    },
  };
}

export default async function EventDetailPage({ params }: EventPageProps) {
  const data = await getEvent(params.id);

  if (!data || !data.event) {
    notFound();
  }

  const { event, rsvp_count, spots_remaining, related_events, instructor_info } = data;

  // Format instructor info to match component props
  const formattedInstructorInfo = instructor_info
    ? {
        id: instructor_info.id,
        firstName: instructor_info.first_name,
        lastName: instructor_info.last_name,
        displayName: instructor_info.display_name,
        bio: instructor_info.bio,
        avatarUrl: instructor_info.avatar_url,
        disciplines: instructor_info.disciplines,
        ranks: instructor_info.ranks,
        instructorCertifications: instructor_info.instructor_certifications,
      }
    : undefined;

  // Generate Schema.org Event structured data
  const eventSchema = {
    "@context": "https://schema.org",
    "@type": "Event",
    name: event.title,
    description: event.description?.replace(/<[^>]*>/g, "") || "",
    startDate: event.start_datetime,
    endDate: event.end_datetime,
    eventStatus: event.is_canceled
      ? "https://schema.org/EventCancelled"
      : "https://schema.org/EventScheduled",
    eventAttendanceMode: event.is_virtual
      ? "https://schema.org/OnlineEventAttendanceMode"
      : "https://schema.org/OfflineEventAttendanceMode",
    location: event.is_virtual
      ? {
          "@type": "VirtualLocation",
          url: event.virtual_url || "",
        }
      : {
          "@type": "Place",
          name: event.location_name || "",
          address: {
            "@type": "PostalAddress",
            streetAddress: event.address || "",
            addressLocality: event.city || "",
            addressRegion: event.state || "",
            addressCountry: "US",
          },
        },
    image: event.featured_image_url || "",
    organizer: {
      "@type": "Organization",
      name: "Women's Martial Arts Association of America",
      url: process.env.NEXT_PUBLIC_SITE_URL || "https://wwmaa.ainative.studio",
    },
    offers: event.registration_fee
      ? {
          "@type": "Offer",
          price: event.registration_fee,
          priceCurrency: "USD",
          availability:
            spots_remaining && spots_remaining > 0
              ? "https://schema.org/InStock"
              : "https://schema.org/SoldOut",
          url: `${process.env.NEXT_PUBLIC_SITE_URL || "https://wwmaa.ainative.studio"}/events/${params.id}`,
        }
      : {
          "@type": "Offer",
          price: 0,
          priceCurrency: "USD",
          availability: "https://schema.org/InStock",
        },
    performer: instructor_info
      ? {
          "@type": "Person",
          name:
            instructor_info.display_name ||
            `${instructor_info.first_name || ""} ${instructor_info.last_name || ""}`.trim(),
        }
      : undefined,
  };

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "https://wwmaa.ainative.studio";
  const eventUrl = `${siteUrl}/events/${params.id}`;

  return (
    <>
      {/* Schema.org JSON-LD */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(eventSchema) }}
      />

      <main className="min-h-screen">
        {/* Hero Section */}
        <EventHero
          title={event.title}
          featuredImageUrl={event.featured_image_url}
          eventType={event.event_type}
          startDatetime={event.start_datetime}
          endDatetime={event.end_datetime}
          timezone={event.timezone}
          locationName={event.location_name}
          city={event.city}
          state={event.state}
          isVirtual={event.is_virtual}
          virtualUrl={event.virtual_url}
          maxAttendees={event.max_attendees}
          spotsRemaining={spots_remaining}
          registrationFee={event.registration_fee}
          visibility={event.visibility}
        />

        {/* Content Section */}
        <section className="py-12 bg-gray-50">
          <div className="mx-auto max-w-7xl px-6">
            {/* Action Bar */}
            <div className="mb-8 flex flex-wrap items-center justify-between gap-4 rounded-xl bg-white p-6 shadow-sm">
              <div className="flex flex-wrap items-center gap-4">
                <AddToCalendar
                  title={event.title}
                  description={event.description}
                  startDatetime={event.start_datetime}
                  endDatetime={event.end_datetime}
                  location={event.address}
                  locationName={event.location_name}
                  city={event.city}
                  state={event.state}
                  isVirtual={event.is_virtual}
                  virtualUrl={event.virtual_url}
                />
                <ShareButtons
                  title={event.title}
                  description={event.description}
                  url={eventUrl}
                />
              </div>

              {/* RSVP Button */}
              <div className="flex items-center gap-4">
                {event.visibility === "members_only" ? (
                  <div className="text-sm text-gray-600">
                    Members Only - Please log in to RSVP
                  </div>
                ) : spots_remaining !== undefined && spots_remaining === 0 ? (
                  <Button disabled className="bg-gray-400">
                    Event Full
                  </Button>
                ) : (
                  <Button className="gradient-green">
                    {event.registration_required ? "Register Now" : "RSVP"}
                  </Button>
                )}
              </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid gap-8 lg:grid-cols-3">
              {/* Left Column - Event Details */}
              <div className="lg:col-span-2 space-y-8">
                <EventDetails
                  description={event.description}
                  startDatetime={event.start_datetime}
                  endDatetime={event.end_datetime}
                  timezone={event.timezone}
                  locationName={event.location_name}
                  address={event.address}
                  city={event.city}
                  state={event.state}
                  isVirtual={event.is_virtual}
                  virtualUrl={event.virtual_url}
                  maxAttendees={event.max_attendees}
                  rsvpCount={rsvp_count}
                  spotsRemaining={spots_remaining}
                  waitlistEnabled={event.waitlist_enabled}
                  registrationRequired={event.registration_required}
                  registrationDeadline={event.registration_deadline}
                  registrationFee={event.registration_fee}
                  tags={event.tags}
                  instructorInfo={formattedInstructorInfo}
                />

                {/* Map for in-person events */}
                <EventMap
                  locationName={event.location_name}
                  address={event.address}
                  city={event.city}
                  state={event.state}
                  isVirtual={event.is_virtual}
                />
              </div>

              {/* Right Column - Sidebar */}
              <div className="space-y-6">
                {/* Quick Actions Card */}
                <div className="rounded-xl bg-white p-6 shadow-sm sticky top-6">
                  <h3 className="font-semibold text-gray-900 mb-4">
                    Quick Actions
                  </h3>
                  <div className="space-y-3">
                    <Button className="w-full gradient-green">
                      {event.registration_required ? "Register Now" : "RSVP"}
                    </Button>
                    {event.is_virtual && event.virtual_url && (
                      <Button
                        variant="outline"
                        className="w-full"
                        onClick={() =>
                          window.open(event.virtual_url, "_blank")
                        }
                      >
                        Join Virtual Event
                      </Button>
                    )}
                    <Separator />
                    <div className="text-sm text-gray-600">
                      <p className="mb-2">
                        <strong>Attendees:</strong> {rsvp_count}
                        {event.max_attendees && ` / ${event.max_attendees}`}
                      </p>
                      {spots_remaining !== undefined && (
                        <p>
                          <strong>Spots Remaining:</strong>{" "}
                          {spots_remaining > 0 ? spots_remaining : "Full"}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Related Events */}
            {related_events && related_events.length > 0 && (
              <div className="mt-12">
                <RelatedEvents events={related_events} />
              </div>
            )}
          </div>
        </section>
      </main>
    </>
  );
}
