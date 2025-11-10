"use client";

import Link from "next/link";
import Image from "next/image";
import { Calendar, MapPin, DollarSign } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface RelatedEvent {
  id: string;
  title: string;
  event_type: string;
  start_datetime: string;
  location_name?: string;
  city?: string;
  state?: string;
  is_virtual: boolean;
  featured_image_url?: string;
  registration_fee?: number;
}

interface RelatedEventsProps {
  events: RelatedEvent[];
}

export function RelatedEvents({ events }: RelatedEventsProps) {
  if (!events || events.length === 0) {
    return null;
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const getEventTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      training: "bg-dojo-green",
      seminar: "bg-dojo-navy",
      competition: "bg-dojo-orange",
      social: "bg-purple-500",
      meeting: "bg-blue-500",
      other: "bg-gray-500",
    };
    return colors[type.toLowerCase()] || "bg-gray-500";
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Related Events</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {events.map((event) => (
            <Link
              key={event.id}
              href={`/events/${event.id}`}
              className="group block"
            >
              <div className="overflow-hidden rounded-lg border border-gray-200 transition-all hover:border-dojo-green hover:shadow-lg">
                {/* Event Image */}
                <div className="relative h-40 bg-gradient-to-br from-dojo-navy to-dojo-navy/80">
                  {event.featured_image_url ? (
                    <Image
                      src={event.featured_image_url}
                      alt={event.title}
                      fill
                      className="object-cover transition-transform group-hover:scale-105"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center">
                      <Calendar className="h-12 w-12 text-white/50" />
                    </div>
                  )}
                  {/* Event Type Badge */}
                  <div className="absolute top-2 left-2">
                    <Badge
                      className={`${getEventTypeColor(event.event_type)} text-white text-xs`}
                    >
                      {event.event_type.charAt(0).toUpperCase() +
                        event.event_type.slice(1)}
                    </Badge>
                  </div>
                </div>

                {/* Event Info */}
                <div className="p-4 space-y-3">
                  <h3 className="font-semibold text-gray-900 line-clamp-2 group-hover:text-dojo-green transition-colors">
                    {event.title}
                  </h3>

                  <div className="space-y-2 text-sm text-gray-600">
                    {/* Date */}
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-gray-400 flex-shrink-0" />
                      <span>{formatDate(event.start_datetime)}</span>
                    </div>

                    {/* Location */}
                    <div className="flex items-center gap-2">
                      <MapPin className="h-4 w-4 text-gray-400 flex-shrink-0" />
                      <span className="truncate">
                        {event.is_virtual
                          ? "Virtual Event"
                          : event.location_name ||
                            (event.city && event.state
                              ? `${event.city}, ${event.state}`
                              : "Location TBD")}
                      </span>
                    </div>

                    {/* Price */}
                    {event.registration_fee !== undefined && (
                      <div className="flex items-center gap-2">
                        <DollarSign className="h-4 w-4 text-gray-400 flex-shrink-0" />
                        <span className="font-medium text-dojo-green">
                          {event.registration_fee > 0
                            ? `$${event.registration_fee.toFixed(2)}`
                            : "Free"}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
