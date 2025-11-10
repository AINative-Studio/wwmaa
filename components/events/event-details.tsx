"use client";

import { Clock, Calendar, MapPin, Users, Tag } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

interface InstructorInfo {
  id: string;
  firstName?: string;
  lastName?: string;
  displayName?: string;
  bio?: string;
  avatarUrl?: string;
  disciplines?: string[];
  ranks?: Record<string, string>;
  instructorCertifications?: string[];
}

interface EventDetailsProps {
  description?: string;
  startDatetime: string;
  endDatetime: string;
  timezone: string;
  locationName?: string;
  address?: string;
  city?: string;
  state?: string;
  isVirtual: boolean;
  virtualUrl?: string;
  maxAttendees?: number;
  rsvpCount: number;
  spotsRemaining?: number;
  waitlistEnabled: boolean;
  registrationRequired: boolean;
  registrationDeadline?: string;
  registrationFee?: number;
  tags?: string[];
  instructorInfo?: InstructorInfo;
}

export function EventDetails({
  description,
  startDatetime,
  endDatetime,
  timezone,
  locationName,
  address,
  city,
  state,
  isVirtual,
  virtualUrl,
  maxAttendees,
  rsvpCount,
  spotsRemaining,
  waitlistEnabled,
  registrationRequired,
  registrationDeadline,
  registrationFee,
  tags,
  instructorInfo,
}: EventDetailsProps) {
  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      timeZoneName: "short",
    });
  };

  const calculateDuration = () => {
    const start = new Date(startDatetime);
    const end = new Date(endDatetime);
    const durationMs = end.getTime() - start.getTime();
    const hours = Math.floor(durationMs / (1000 * 60 * 60));
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0 && minutes > 0) {
      return `${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours} hour${hours > 1 ? "s" : ""}`;
    } else {
      return `${minutes} minute${minutes > 1 ? "s" : ""}`;
    }
  };

  return (
    <div className="space-y-8">
      {/* Description */}
      {description && (
        <Card>
          <CardHeader>
            <CardTitle>About This Event</CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className="prose prose-gray max-w-none"
              dangerouslySetInnerHTML={{ __html: description }}
            />
          </CardContent>
        </Card>
      )}

      {/* Event Details Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Date & Time */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-dojo-green" />
              Date & Time
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="text-sm font-medium text-gray-500">Start</p>
              <p className="text-gray-900">{formatDateTime(startDatetime)}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">End</p>
              <p className="text-gray-900">{formatDateTime(endDatetime)}</p>
            </div>
            <Separator />
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-gray-400" />
              <p className="text-sm text-gray-600">
                Duration: {calculateDuration()}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Timezone: {timezone}</p>
            </div>
          </CardContent>
        </Card>

        {/* Location */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPin className="h-5 w-5 text-dojo-green" />
              Location
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {isVirtual ? (
              <>
                <p className="font-medium text-gray-900">Virtual Event</p>
                <p className="text-sm text-gray-600">
                  This is an online event. Join from anywhere with an internet
                  connection.
                </p>
                {virtualUrl && (
                  <a
                    href={virtualUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm font-medium text-dojo-green hover:text-dojo-green/80"
                  >
                    Join Virtual Event
                    <svg
                      className="h-4 w-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                  </a>
                )}
              </>
            ) : (
              <>
                {locationName && (
                  <p className="font-medium text-gray-900">{locationName}</p>
                )}
                {address && <p className="text-gray-700">{address}</p>}
                {city && state && (
                  <p className="text-gray-700">
                    {city}, {state}
                  </p>
                )}
                {address && (
                  <a
                    href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
                      `${locationName || ""} ${address} ${city || ""} ${state || ""}`
                    )}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-sm font-medium text-dojo-green hover:text-dojo-green/80"
                  >
                    Get Directions
                    <svg
                      className="h-4 w-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                  </a>
                )}
              </>
            )}
          </CardContent>
        </Card>

        {/* Registration Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-dojo-green" />
              Registration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {registrationRequired ? (
              <>
                <div>
                  <p className="text-sm font-medium text-gray-500">
                    Registration Fee
                  </p>
                  <p className="text-lg font-semibold text-gray-900">
                    {registrationFee && registrationFee > 0
                      ? `$${registrationFee.toFixed(2)}`
                      : "Free"}
                  </p>
                </div>
                {registrationDeadline && (
                  <div>
                    <p className="text-sm font-medium text-gray-500">
                      Registration Deadline
                    </p>
                    <p className="text-gray-900">
                      {new Date(registrationDeadline).toLocaleDateString(
                        "en-US",
                        {
                          weekday: "long",
                          month: "long",
                          day: "numeric",
                        }
                      )}
                    </p>
                  </div>
                )}
                {maxAttendees && (
                  <>
                    <Separator />
                    <div>
                      <p className="text-sm font-medium text-gray-500">
                        Capacity
                      </p>
                      <p className="text-gray-900">
                        {rsvpCount} / {maxAttendees} registered
                      </p>
                      {spotsRemaining !== undefined && (
                        <p className="text-sm text-gray-600 mt-1">
                          {spotsRemaining > 0
                            ? `${spotsRemaining} spot${spotsRemaining !== 1 ? "s" : ""} remaining`
                            : waitlistEnabled
                            ? "Full - Waitlist available"
                            : "Event Full"}
                        </p>
                      )}
                    </div>
                  </>
                )}
              </>
            ) : (
              <p className="text-gray-600">
                No registration required. Simply show up!
              </p>
            )}
          </CardContent>
        </Card>

        {/* Instructor Info */}
        {instructorInfo && (
          <Card>
            <CardHeader>
              <CardTitle>Instructor</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-start gap-4">
                {instructorInfo.avatarUrl && (
                  <img
                    src={instructorInfo.avatarUrl}
                    alt={instructorInfo.displayName || "Instructor"}
                    className="h-16 w-16 rounded-full object-cover"
                  />
                )}
                <div className="flex-1">
                  <p className="font-semibold text-gray-900">
                    {instructorInfo.displayName ||
                      `${instructorInfo.firstName || ""} ${instructorInfo.lastName || ""}`.trim()}
                  </p>
                  {instructorInfo.disciplines &&
                    instructorInfo.disciplines.length > 0 && (
                      <p className="text-sm text-gray-600">
                        {instructorInfo.disciplines.join(", ")}
                      </p>
                    )}
                </div>
              </div>
              {instructorInfo.bio && (
                <p className="text-sm text-gray-700">{instructorInfo.bio}</p>
              )}
              {instructorInfo.instructorCertifications &&
                instructorInfo.instructorCertifications.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-500 mb-2">
                      Certifications
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {instructorInfo.instructorCertifications.map(
                        (cert, idx) => (
                          <Badge key={idx} variant="secondary">
                            {cert}
                          </Badge>
                        )
                      )}
                    </div>
                  </div>
                )}
            </CardContent>
          </Card>
        )}
      </div>

      {/* Tags */}
      {tags && tags.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Tag className="h-5 w-5 text-dojo-green" />
              Topics & Tags
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag, idx) => (
                <Badge key={idx} variant="outline">
                  {tag}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
