/**
 * Event Type Definitions
 * Types for event-related data structures
 */

export type EventType = 'live_training' | 'seminar' | 'tournament' | 'certification';

export type LocationType = 'in_person' | 'online' | 'hybrid';

export type EventStatus = 'upcoming' | 'ongoing' | 'completed' | 'cancelled';

export interface EventLocation {
  type: LocationType;
  venue?: string;
  address?: string;
  city?: string;
  state?: string;
  country?: string;
  zipCode?: string;
  virtualUrl?: string;
}

export interface EventPrice {
  isFree: boolean;
  amount?: number;
  currency?: string;
  memberPrice?: number;
}

export interface Event {
  id: string;
  title: string;
  description: string;
  teaser?: string;
  type: EventType;
  status: EventStatus;
  startDate: string;
  endDate: string;
  location: EventLocation;
  price: EventPrice;
  capacity?: number;
  registered?: number;
  imageUrl?: string;
  instructor?: string;
  membersOnly: boolean;
  tags?: string[];
  createdAt: string;
  updatedAt: string;
}

export interface EventFilters {
  type?: EventType[];
  locationType?: LocationType[];
  isFree?: boolean;
  dateFrom?: string;
  dateTo?: string;
  searchQuery?: string;
}

export interface EventsResponse {
  events: Event[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export type ViewType = 'list' | 'calendar';
export type CalendarView = 'month' | 'week' | 'day';
