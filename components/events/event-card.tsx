"use client";

import Link from "next/link";
import Image from "next/image";
import { EventItem } from "@/lib/types";
import { Calendar, MapPin, Users, DollarSign, Globe, MapPinned } from "lucide-react";
import { format } from "date-fns";

interface EventCardProps {
  event: EventItem;
}

const eventTypeConfig = {
  live_training: {
    label: "Live Training",
    color: "bg-dojo-orange text-white",
  },
  seminar: {
    label: "Seminar",
    color: "bg-dojo-green text-white",
  },
  tournament: {
    label: "Tournament",
    color: "bg-dojo-navy text-white",
  },
  certification: {
    label: "Certification",
    color: "bg-purple-600 text-white",
  },
};

const locationTypeConfig = {
  online: {
    icon: Globe,
    label: "Online Event",
  },
  in_person: {
    icon: MapPinned,
    label: "In-Person Event",
  },
};

/**
 * EventCard Component
 *
 * Displays event information in a card format with image, title, date, location, price, and badges.
 * Optimized for responsive grid layouts.
 */
export function EventCard({ event }: EventCardProps) {
  const typeConfig = eventTypeConfig[event.type];
  const locationConfig = locationTypeConfig[event.location_type];
  const LocationIcon = locationConfig.icon;

  const isFree = event.price === 0;
  const isMembersOnly = event.visibility === "members_only";
  const isFull = event.max_participants && event.current_participants && event.current_participants >= event.max_participants;

  // Format date
  const startDate = new Date(event.start);
  const formattedDate = format(startDate, "EEE, MMM d 'at' h:mm a");

  // Calculate spots remaining
  const spotsRemaining = event.max_participants && event.current_participants
    ? event.max_participants - event.current_participants
    : null;

  return (
    <Link
      href={`/events/${event.id}`}
      className="group block h-full bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden border border-gray-100"
      aria-label={`View details for ${event.title}`}
      data-testid="event-card"
    >
      {/* Event Image */}
      <div className="relative h-48 bg-gradient-to-br from-dojo-navy/5 to-dojo-green/5 overflow-hidden">
        {event.image ? (
          <Image
            src={event.image}
            alt={event.title}
            fill
            className="object-cover transition-transform duration-300 group-hover:scale-105"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Calendar className="w-16 h-16 text-gray-300" />
          </div>
        )}

        {/* Badges Overlay */}
        <div className="absolute top-3 left-3 flex flex-col gap-2">
          {/* Event Type Badge */}
          <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${typeConfig.color}`}>
            {typeConfig.label}
          </span>

          {/* Members Only Badge */}
          {isMembersOnly && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-amber-500 text-white">
              Members Only
            </span>
          )}

          {/* Full Badge */}
          {isFull && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-red-500 text-white">
              Full
            </span>
          )}
        </div>

        {/* Price Badge */}
        <div className="absolute top-3 right-3">
          {isFree ? (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-green-500 text-white">
              Free
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-white text-dojo-navy">
              <DollarSign className="w-3 h-3" />
              {event.price}
            </span>
          )}
        </div>
      </div>

      {/* Event Details */}
      <div className="p-6 space-y-4">
        {/* Title */}
        <h3 className="font-semibold text-xl text-dojo-navy group-hover:text-dojo-green transition-colors line-clamp-2">
          {event.title}
        </h3>

        {/* Teaser */}
        {event.teaser && (
          <p className="text-gray-600 text-sm line-clamp-2">
            {event.teaser}
          </p>
        )}

        {/* Event Info */}
        <div className="space-y-2 text-sm">
          {/* Date */}
          <div className="flex items-start gap-2 text-gray-700">
            <Calendar className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <time dateTime={event.start}>{formattedDate}</time>
          </div>

          {/* Location */}
          <div className="flex items-start gap-2 text-gray-700">
            <LocationIcon className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span className="line-clamp-1">{event.location}</span>
          </div>

          {/* Instructor */}
          {event.instructor && (
            <div className="flex items-start gap-2 text-gray-700">
              <Users className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>with {event.instructor}</span>
            </div>
          )}

          {/* Spots Remaining */}
          {spotsRemaining !== null && spotsRemaining > 0 && (
            <div className="flex items-center gap-2 text-gray-700">
              <Users className="w-4 h-4 flex-shrink-0" />
              <span className="text-xs">
                {spotsRemaining} {spotsRemaining === 1 ? "spot" : "spots"} remaining
              </span>
            </div>
          )}
        </div>

        {/* CTA */}
        <div className="pt-2">
          <div className="inline-flex items-center gap-2 text-dojo-green font-semibold group-hover:gap-3 transition-all">
            View Details
            <svg
              className="w-4 h-4 transition-transform group-hover:translate-x-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </div>
        </div>
      </div>
    </Link>
  );
}
