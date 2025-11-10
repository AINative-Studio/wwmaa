"use client";

import Image from "next/image";
import { Calendar, MapPin, Users, DollarSign } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface EventHeroProps {
  title: string;
  featuredImageUrl?: string;
  eventType: string;
  startDatetime: string;
  endDatetime: string;
  timezone: string;
  locationName?: string;
  city?: string;
  state?: string;
  isVirtual: boolean;
  virtualUrl?: string;
  maxAttendees?: number;
  spotsRemaining?: number;
  registrationFee?: number;
  visibility: string;
}

export function EventHero({
  title,
  featuredImageUrl,
  eventType,
  startDatetime,
  endDatetime,
  timezone,
  locationName,
  city,
  state,
  isVirtual,
  virtualUrl,
  maxAttendees,
  spotsRemaining,
  registrationFee,
  visibility,
}: EventHeroProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      timeZoneName: "short",
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
    <div className="relative bg-gradient-to-br from-dojo-navy to-dojo-navy/90">
      {/* Background Image */}
      {featuredImageUrl && (
        <div className="absolute inset-0 opacity-20">
          <Image
            src={featuredImageUrl}
            alt=""
            fill
            className="object-cover"
            priority
          />
        </div>
      )}

      {/* Content */}
      <div className="relative mx-auto max-w-7xl px-6 py-16 sm:py-24">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left Column - Main Info */}
          <div className="lg:col-span-2">
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <Badge
                className={`${getEventTypeColor(eventType)} text-white`}
              >
                {eventType.charAt(0).toUpperCase() + eventType.slice(1)}
              </Badge>
              {visibility === "members_only" && (
                <Badge variant="outline" className="border-white text-white">
                  Members Only
                </Badge>
              )}
              {visibility === "invite_only" && (
                <Badge variant="outline" className="border-white text-white">
                  Invite Only
                </Badge>
              )}
            </div>

            <h1 className="font-display text-4xl font-bold text-white sm:text-5xl lg:text-6xl mb-6">
              {title}
            </h1>

            {/* Date & Time */}
            <div className="flex flex-wrap items-center gap-6 text-white/90">
              <div className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                <div>
                  <p className="font-medium">{formatDate(startDatetime)}</p>
                  <p className="text-sm text-white/70">
                    {formatTime(startDatetime)} - {formatTime(endDatetime)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column - Quick Info Card */}
          <div className="rounded-2xl bg-white p-6 shadow-2xl lg:self-start">
            <div className="space-y-4">
              {/* Location */}
              <div className="flex items-start gap-3">
                <MapPin className="h-5 w-5 text-dojo-green flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  {isVirtual ? (
                    <>
                      <p className="font-semibold text-dojo-navy">
                        Virtual Event
                      </p>
                      <p className="text-sm text-gray-600">
                        Join from anywhere
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="font-semibold text-dojo-navy">
                        {locationName || "Location TBD"}
                      </p>
                      {city && state && (
                        <p className="text-sm text-gray-600">
                          {city}, {state}
                        </p>
                      )}
                    </>
                  )}
                </div>
              </div>

              {/* Capacity */}
              {maxAttendees && (
                <div className="flex items-start gap-3">
                  <Users className="h-5 w-5 text-dojo-green flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <p className="font-semibold text-dojo-navy">
                      {spotsRemaining !== undefined && spotsRemaining > 0
                        ? `${spotsRemaining} spots remaining`
                        : spotsRemaining === 0
                        ? "Event Full"
                        : `${maxAttendees} max attendees`}
                    </p>
                    <p className="text-sm text-gray-600">
                      Limited capacity
                    </p>
                  </div>
                </div>
              )}

              {/* Price */}
              <div className="flex items-start gap-3">
                <DollarSign className="h-5 w-5 text-dojo-green flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <p className="font-semibold text-dojo-navy">
                    {registrationFee && registrationFee > 0
                      ? `$${registrationFee.toFixed(2)}`
                      : "Free"}
                  </p>
                  {registrationFee && registrationFee > 0 && (
                    <p className="text-sm text-gray-600">
                      Registration fee
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
