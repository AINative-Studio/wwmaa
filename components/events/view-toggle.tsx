'use client';

import { LayoutList, Calendar } from 'lucide-react';
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group';
import type { ViewType } from '@/lib/types/event';

interface ViewToggleProps {
  view: ViewType;
  onViewChange: (view: ViewType) => void;
  className?: string;
}

export function ViewToggle({ view, onViewChange, className = '' }: ViewToggleProps) {
  return (
    <ToggleGroup
      type="single"
      value={view}
      onValueChange={(value) => {
        if (value) onViewChange(value as ViewType);
      }}
      className={className}
    >
      <ToggleGroupItem
        value="list"
        aria-label="List view"
        className="gap-2 data-[state=on]:bg-dojo-navy data-[state=on]:text-white"
      >
        <LayoutList className="h-4 w-4" />
        <span className="hidden sm:inline">List</span>
      </ToggleGroupItem>
      <ToggleGroupItem
        value="calendar"
        aria-label="Calendar view"
        className="gap-2 data-[state=on]:bg-dojo-navy data-[state=on]:text-white"
      >
        <Calendar className="h-4 w-4" />
        <span className="hidden sm:inline">Calendar</span>
      </ToggleGroupItem>
    </ToggleGroup>
  );
}
