// Quick test script to verify event API mapping
const testEvent = {
  "id": "5726cdd8-59ac-4d70-b7f5-0255238b0227",
  "data": {
    "price": 50.0,
    "title": "Karate Workshop - Advanced Techniques",
    "status": "published",
    "capacity": 30,
    "currency": "USD",
    "end_date": "2025-12-13T21:47:16.381509",
    "location": "WWMAA Headquarters",
    "is_online": false,
    "created_by": "9d89b30f-1651-4cac-aedb-478a1d4512e2",
    "event_type": "workshop",
    "is_deleted": false,
    "start_date": "2025-12-13T18:47:16.381470",
    "visibility": "public",
    "description": "Join us for an intensive workshop covering advanced Karate techniques including kata and kumite strategies.",
    "is_published": true,
    "registered_count": 5
  }
};

// Simulate the mapEventType function
function mapEventType(backendType) {
  const typeMap = {
    "workshop": "seminar",
    "seminar": "seminar",
    "competition": "tournament",
    "tournament": "tournament",
    "live_training": "live_training",
    "training": "live_training",
    "certification": "certification",
  };
  return typeMap[backendType] || "seminar";
}

// Simulate the mapBackendEvent function
function mapBackendEvent(backendEvent) {
  const data = backendEvent.data || backendEvent;

  return {
    id: backendEvent.id,
    title: data.title || "Untitled Event",
    description: data.description,
    start: data.start_date,
    end: data.end_date,
    location: data.location || (data.is_online ? "Online" : "TBD"),
    location_type: data.is_online ? "online" : "in_person",
    type: mapEventType(data.event_type),
    price: data.price !== undefined ? data.price : 0,
    visibility: data.visibility || "public",
    status: data.status || "published",
    teaser: data.teaser || data.description?.substring(0, 150),
    image: data.featured_image_url,
    max_participants: data.capacity,
    current_participants: data.registered_count || 0,
    instructor: data.instructor_info,
    created_at: data.created_at || new Date().toISOString(),
    updated_at: data.updated_at || new Date().toISOString(),
  };
}

const mappedEvent = mapBackendEvent(testEvent);
console.log('Mapped Event:');
console.log(JSON.stringify(mappedEvent, null, 2));
console.log('\nKey fields:');
console.log('- Type:', mappedEvent.type);
console.log('- Start:', mappedEvent.start);
console.log('- End:', mappedEvent.end);
console.log('- Location:', mappedEvent.location);
console.log('- Location Type:', mappedEvent.location_type);
console.log('- Price:', mappedEvent.price);
console.log('- Current Participants:', mappedEvent.current_participants);
