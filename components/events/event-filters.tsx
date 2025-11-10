"use client";

import { EventType, EventLocationType } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { X } from "lucide-react";

interface EventFiltersProps {
  filters: {
    type?: EventType;
    location?: EventLocationType;
    price?: "free" | "paid";
    date_range?: "upcoming" | "this_week" | "this_month";
  };
  onFilterChange: (key: string, value: string | undefined) => void;
  onClearAll: () => void;
}

/**
 * EventFilters Component
 *
 * Provides filter controls for event type, location, price, and date range.
 * Supports both desktop sidebar and mobile modal layouts.
 */
export function EventFilters({ filters, onFilterChange, onClearAll }: EventFiltersProps) {
  const hasActiveFilters = Boolean(
    filters.type || filters.location || filters.price || filters.date_range
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg text-dojo-navy">Filters</h3>
        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onClearAll}
            className="text-dojo-green hover:text-dojo-green/80"
          >
            Clear All
          </Button>
        )}
      </div>

      {/* Event Type Filter */}
      <div className="space-y-3">
        <Label className="text-sm font-semibold text-gray-700">Event Type</Label>
        <RadioGroup
          value={filters.type ?? "all"}
          onValueChange={(value) => onFilterChange("type", value === "all" ? undefined : value)}
        >
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="all" id="type-all" />
              <Label htmlFor="type-all" className="font-normal cursor-pointer">
                All Types
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="live_training" id="type-live" />
              <Label htmlFor="type-live" className="font-normal cursor-pointer">
                Live Training
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="seminar" id="type-seminar" />
              <Label htmlFor="type-seminar" className="font-normal cursor-pointer">
                Seminar
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="tournament" id="type-tournament" />
              <Label htmlFor="type-tournament" className="font-normal cursor-pointer">
                Tournament
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="certification" id="type-cert" />
              <Label htmlFor="type-cert" className="font-normal cursor-pointer">
                Certification
              </Label>
            </div>
          </div>
        </RadioGroup>
      </div>

      <div className="border-t border-gray-200" />

      {/* Date Range Filter */}
      <div className="space-y-3">
        <Label className="text-sm font-semibold text-gray-700">Date Range</Label>
        <RadioGroup
          value={filters.date_range ?? "upcoming"}
          onValueChange={(value) => onFilterChange("date_range", value)}
        >
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="upcoming" id="date-upcoming" />
              <Label htmlFor="date-upcoming" className="font-normal cursor-pointer">
                All Upcoming
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="this_week" id="date-week" />
              <Label htmlFor="date-week" className="font-normal cursor-pointer">
                This Week
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="this_month" id="date-month" />
              <Label htmlFor="date-month" className="font-normal cursor-pointer">
                This Month
              </Label>
            </div>
          </div>
        </RadioGroup>
      </div>

      <div className="border-t border-gray-200" />

      {/* Location Type Filter */}
      <div className="space-y-3">
        <Label className="text-sm font-semibold text-gray-700">Location</Label>
        <RadioGroup
          value={filters.location ?? "all"}
          onValueChange={(value) => onFilterChange("location", value === "all" ? undefined : value)}
        >
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="all" id="location-all" />
              <Label htmlFor="location-all" className="font-normal cursor-pointer">
                All Locations
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="in_person" id="location-person" />
              <Label htmlFor="location-person" className="font-normal cursor-pointer">
                In-Person
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="online" id="location-online" />
              <Label htmlFor="location-online" className="font-normal cursor-pointer">
                Online
              </Label>
            </div>
          </div>
        </RadioGroup>
      </div>

      <div className="border-t border-gray-200" />

      {/* Price Filter */}
      <div className="space-y-3">
        <Label className="text-sm font-semibold text-gray-700">Price</Label>
        <RadioGroup
          value={filters.price ?? "all"}
          onValueChange={(value) => onFilterChange("price", value === "all" ? undefined : value)}
        >
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="all" id="price-all" />
              <Label htmlFor="price-all" className="font-normal cursor-pointer">
                All Prices
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="free" id="price-free" />
              <Label htmlFor="price-free" className="font-normal cursor-pointer">
                Free Events
              </Label>
            </div>
            <div className="flex items-center space-x-2">
              <RadioGroupItem value="paid" id="price-paid" />
              <Label htmlFor="price-paid" className="font-normal cursor-pointer">
                Paid Events
              </Label>
            </div>
          </div>
        </RadioGroup>
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <>
          <div className="border-t border-gray-200" />
          <div className="space-y-2">
            <Label className="text-sm font-semibold text-gray-700">Active Filters</Label>
            <div className="flex flex-wrap gap-2">
              {filters.type && (
                <button
                  onClick={() => onFilterChange("type", undefined)}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-dojo-navy/10 text-dojo-navy hover:bg-dojo-navy/20 transition-colors"
                >
                  {filters.type.replace("_", " ")}
                  <X className="w-3 h-3" />
                </button>
              )}
              {filters.location && (
                <button
                  onClick={() => onFilterChange("location", undefined)}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-dojo-navy/10 text-dojo-navy hover:bg-dojo-navy/20 transition-colors"
                >
                  {filters.location.replace("_", " ")}
                  <X className="w-3 h-3" />
                </button>
              )}
              {filters.price && (
                <button
                  onClick={() => onFilterChange("price", undefined)}
                  className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-dojo-navy/10 text-dojo-navy hover:bg-dojo-navy/20 transition-colors"
                >
                  {filters.price}
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
