const testData = {
  events: [{
    id: '5726cdd8-59ac-4d70-b7f5-0255238b0227',
    data: {
      title: 'Karate Workshop - Advanced Techniques',
      description: 'Join us for an intensive workshop',
      start_date: '2025-12-13T18:47:16.381470',
      end_date: '2025-12-13T21:47:16.381509',
      location: 'WWMAA Headquarters',
      is_online: false,
      event_type: 'workshop',
      price: 50.0,
      visibility: 'public',
      status: 'published'
    }
  }],
  total: 1
};

function mapEventType(backendType) {
  const typeMap = {
    'workshop': 'seminar',
    'seminar': 'seminar',
    'competition': 'tournament',
    'tournament': 'tournament',
    'live_training': 'live_training',
    'training': 'live_training',
    'certification': 'certification',
  };
  return typeMap[backendType] || 'seminar';
}

function mapBackendEvent(backendEvent) {
  const data = backendEvent.data || backendEvent;
  return {
    id: backendEvent.id,
    title: data.title || 'Untitled Event',
    description: data.description,
    start: data.start_date,
    end: data.end_date,
    location: data.location || (data.is_online ? 'Online' : 'TBD'),
    location_type: data.is_online ? 'online' : 'in_person',
    type: mapEventType(data.event_type),
    price: data.price !== undefined ? data.price : 0,
    visibility: data.visibility || 'public',
    status: data.status || 'published',
  };
}

const mapped = mapBackendEvent(testData.events[0]);
console.log(JSON.stringify(mapped, null, 2));
