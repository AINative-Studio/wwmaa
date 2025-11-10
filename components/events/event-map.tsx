"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MapPin } from "lucide-react";

interface EventMapProps {
  locationName?: string;
  address?: string;
  city?: string;
  state?: string;
  isVirtual: boolean;
}

export function EventMap({
  locationName,
  address,
  city,
  state,
  isVirtual,
}: EventMapProps) {
  // Don't render map for virtual events
  if (isVirtual || !address) {
    return null;
  }

  // Build full address for embed
  const fullAddress = [locationName, address, city, state]
    .filter(Boolean)
    .join(", ");

  // Google Maps Embed API URL
  const mapEmbedUrl = `https://www.google.com/maps/embed/v1/place?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY || "YOUR_API_KEY"}&q=${encodeURIComponent(fullAddress)}`;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MapPin className="h-5 w-5 text-dojo-green" />
          Event Location
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Location Details */}
          <div>
            {locationName && (
              <p className="font-semibold text-gray-900">{locationName}</p>
            )}
            {address && <p className="text-gray-700">{address}</p>}
            {city && state && (
              <p className="text-gray-700">
                {city}, {state}
              </p>
            )}
          </div>

          {/* Map Embed */}
          <div className="relative w-full h-[300px] rounded-lg overflow-hidden border border-gray-200">
            <iframe
              title="Event Location Map"
              width="100%"
              height="100%"
              style={{ border: 0 }}
              loading="lazy"
              allowFullScreen
              referrerPolicy="no-referrer-when-downgrade"
              src={mapEmbedUrl}
            />
          </div>

          {/* Get Directions Link */}
          <a
            href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(fullAddress)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-sm font-medium text-dojo-green hover:text-dojo-green/80"
          >
            <MapPin className="h-4 w-4" />
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
        </div>
      </CardContent>
    </Card>
  );
}
