import type { Event } from '@/lib/types/event';

/**
 * Mock event data for testing and development
 */
export const mockEvents: Event[] = [
  {
    id: '1',
    title: 'Advanced Judo Techniques Workshop',
    description: 'Master advanced throwing techniques with Olympic-level instructors. Learn from the best in the martial arts community.',
    teaser: 'Master advanced throwing techniques with Olympic-level instructors.',
    type: 'seminar',
    status: 'upcoming',
    startDate: new Date(2025, 10, 15, 9, 0).toISOString(),
    endDate: new Date(2025, 10, 15, 17, 0).toISOString(),
    location: {
      type: 'in_person',
      venue: 'WWMAA National Training Center',
      address: '123 Martial Arts Blvd',
      city: 'Los Angeles',
      state: 'CA',
      country: 'USA',
      zipCode: '90001',
    },
    price: {
      isFree: false,
      amount: 150,
      currency: 'USD',
      memberPrice: 100,
    },
    capacity: 50,
    registered: 32,
    imageUrl: '/images/events/judo-workshop.jpg',
    instructor: 'Master Takashi Yamamoto',
    membersOnly: false,
    tags: ['judo', 'advanced', 'techniques'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '2',
    title: 'Online Karate Kata Masterclass',
    description: 'Perfect your kata performance with detailed instruction and feedback.',
    teaser: 'Perfect your kata performance with detailed instruction.',
    type: 'live_training',
    status: 'upcoming',
    startDate: new Date(2025, 10, 18, 19, 0).toISOString(),
    endDate: new Date(2025, 10, 18, 21, 0).toISOString(),
    location: {
      type: 'online',
      virtualUrl: 'https://wwmaa.zoom.us/j/123456789',
    },
    price: {
      isFree: true,
    },
    capacity: 100,
    registered: 78,
    instructor: 'Sensei Maria Rodriguez',
    membersOnly: true,
    tags: ['karate', 'kata', 'online'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '3',
    title: 'National Martial Arts Tournament',
    description: 'Annual championship tournament featuring divisions for all belt ranks and age groups.',
    teaser: 'Annual championship tournament for all belt ranks.',
    type: 'tournament',
    status: 'upcoming',
    startDate: new Date(2025, 10, 20, 8, 0).toISOString(),
    endDate: new Date(2025, 10, 22, 18, 0).toISOString(),
    location: {
      type: 'in_person',
      venue: 'Dallas Convention Center',
      address: '650 S Griffin St',
      city: 'Dallas',
      state: 'TX',
      country: 'USA',
      zipCode: '75202',
    },
    price: {
      isFree: false,
      amount: 75,
      currency: 'USD',
      memberPrice: 50,
    },
    capacity: 500,
    registered: 287,
    membersOnly: false,
    tags: ['tournament', 'competition', 'all-styles'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '4',
    title: 'Black Belt Certification Exam',
    description: 'Official WWMAA black belt examination for qualified candidates.',
    teaser: 'Official black belt examination for qualified candidates.',
    type: 'certification',
    status: 'upcoming',
    startDate: new Date(2025, 10, 25, 9, 0).toISOString(),
    endDate: new Date(2025, 10, 25, 16, 0).toISOString(),
    location: {
      type: 'in_person',
      venue: 'WWMAA Headquarters Dojo',
      address: '456 Honor Way',
      city: 'Chicago',
      state: 'IL',
      country: 'USA',
      zipCode: '60601',
    },
    price: {
      isFree: false,
      amount: 200,
      currency: 'USD',
      memberPrice: 200,
    },
    capacity: 20,
    registered: 15,
    membersOnly: true,
    tags: ['certification', 'black-belt', 'exam'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '5',
    title: 'Beginner Self-Defense Workshop',
    description: 'Free introductory workshop covering basic self-defense techniques.',
    teaser: 'Free workshop covering basic self-defense techniques.',
    type: 'seminar',
    status: 'upcoming',
    startDate: new Date(2025, 10, 28, 14, 0).toISOString(),
    endDate: new Date(2025, 10, 28, 16, 0).toISOString(),
    location: {
      type: 'hybrid',
      venue: 'Community Center',
      address: '789 Main Street',
      city: 'Seattle',
      state: 'WA',
      country: 'USA',
      zipCode: '98101',
      virtualUrl: 'https://wwmaa.zoom.us/j/987654321',
    },
    price: {
      isFree: true,
    },
    capacity: 75,
    registered: 45,
    instructor: 'Instructor Sarah Chen',
    membersOnly: false,
    tags: ['self-defense', 'beginner', 'free'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '6',
    title: 'Weapons Training Intensive',
    description: 'Three-day intensive training in traditional martial arts weapons.',
    teaser: 'Three-day intensive in traditional weapons training.',
    type: 'live_training',
    status: 'upcoming',
    startDate: new Date(2025, 11, 1, 9, 0).toISOString(),
    endDate: new Date(2025, 11, 3, 17, 0).toISOString(),
    location: {
      type: 'in_person',
      venue: 'Mountain Retreat Dojo',
      address: '321 Summit Road',
      city: 'Denver',
      state: 'CO',
      country: 'USA',
      zipCode: '80201',
    },
    price: {
      isFree: false,
      amount: 450,
      currency: 'USD',
      memberPrice: 350,
    },
    capacity: 30,
    registered: 22,
    instructor: 'Master Robert Kim',
    membersOnly: false,
    tags: ['weapons', 'intensive', 'traditional'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '7',
    title: 'Youth Martial Arts Championship',
    description: 'Regional tournament for youth competitors ages 8-17.',
    teaser: 'Regional tournament for youth competitors.',
    type: 'tournament',
    status: 'upcoming',
    startDate: new Date(2025, 11, 5, 9, 0).toISOString(),
    endDate: new Date(2025, 11, 5, 18, 0).toISOString(),
    location: {
      type: 'in_person',
      venue: 'Youth Sports Complex',
      address: '555 Athletic Drive',
      city: 'Atlanta',
      state: 'GA',
      country: 'USA',
      zipCode: '30301',
    },
    price: {
      isFree: false,
      amount: 50,
      currency: 'USD',
      memberPrice: 35,
    },
    capacity: 200,
    registered: 145,
    membersOnly: false,
    tags: ['youth', 'tournament', 'regional'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
  {
    id: '8',
    title: 'Instructor Certification Program',
    description: 'Comprehensive instructor certification program spanning four weeks.',
    teaser: 'Four-week instructor certification program.',
    type: 'certification',
    status: 'upcoming',
    startDate: new Date(2025, 11, 10, 9, 0).toISOString(),
    endDate: new Date(2025, 11, 10, 17, 0).toISOString(),
    location: {
      type: 'online',
      virtualUrl: 'https://wwmaa.zoom.us/j/instructor-cert',
    },
    price: {
      isFree: false,
      amount: 600,
      currency: 'USD',
      memberPrice: 500,
    },
    capacity: 25,
    registered: 18,
    instructor: 'Director John Martinez',
    membersOnly: true,
    tags: ['instructor', 'certification', 'professional'],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  },
];

/**
 * Helper function to filter events based on criteria
 */
export function filterEvents(
  events: Event[],
  filters: {
    type?: string[];
    locationType?: string[];
    isFree?: boolean;
    dateFrom?: string;
    dateTo?: string;
    searchQuery?: string;
  }
): Event[] {
  return events.filter((event) => {
    // Filter by type
    if (filters.type && filters.type.length > 0) {
      if (!filters.type.includes(event.type)) return false;
    }

    // Filter by location type
    if (filters.locationType && filters.locationType.length > 0) {
      if (!filters.locationType.includes(event.location.type)) return false;
    }

    // Filter by price
    if (filters.isFree === true) {
      if (!event.price.isFree) return false;
    }

    // Filter by date range
    if (filters.dateFrom) {
      const eventStart = new Date(event.startDate);
      const filterStart = new Date(filters.dateFrom);
      if (eventStart < filterStart) return false;
    }

    if (filters.dateTo) {
      const eventEnd = new Date(event.endDate);
      const filterEnd = new Date(filters.dateTo);
      if (eventEnd > filterEnd) return false;
    }

    // Filter by search query
    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase();
      const matchTitle = event.title.toLowerCase().includes(query);
      const matchDescription = event.description?.toLowerCase().includes(query);
      const matchTags = event.tags?.some((tag) => tag.toLowerCase().includes(query));
      if (!matchTitle && !matchDescription && !matchTags) return false;
    }

    return true;
  });
}
