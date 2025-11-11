# Live Session UI - Usage Guide

## Quick Start

### 1. Add EventSession to Event Detail Page

```tsx
import { EventSession } from "@/components/events/event-session";

// In your event detail page:
<EventSession
  eventId={event.id}
  sessionId={session.id}
  sessionTitle={session.title}
  startDatetime={session.start_datetime}
  endDatetime={session.end_datetime}
  isVirtual={event.is_virtual}
  requiresPayment={event.registration_required}
  registrationFee={event.registration_fee}
  currentUserStatus={{
    isAuthenticated: !!user,
    hasPaid: userHasPaid,
    hasAcceptedTerms: userAcceptedTerms,
  }}
/>
```

### 2. Live Session Page Setup

The live session page at `/app/training/[sessionId]/live/page.tsx` is already set up and will:
- Validate the session exists and is currently live
- Check user access (auth, payment, terms)
- Render the RTC interface
- Handle all redirects automatically

No additional setup needed!

### 3. Backend Integration Required

#### Environment Variables
```env
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### API Endpoints to Implement

**Session Management:**
```
GET /api/training/sessions/{sessionId}
GET /api/training/sessions/{sessionId}/access
```

**Attendance Tracking:**
```
POST /api/training/sessions/{sessionId}/attendance
PUT  /api/training/sessions/{sessionId}/attendance/{userId}
GET  /api/training/sessions/{sessionId}/attendance
```

**Terms Acceptance:**
```
POST /api/training/sessions/{sessionId}/accept-terms
GET  /api/training/sessions/{sessionId}/accept-terms
```

**WebSocket Chat:**
```
WS /ws/training/{sessionId}/chat
```

## Component API Reference

### EventSession Component

**Props:**
```typescript
interface EventSessionProps {
  eventId: string;                  // Event ID for redirects
  sessionId: string;                // Session ID for API calls
  sessionTitle: string;             // Display title
  startDatetime: string;            // ISO 8601 datetime
  endDatetime: string;              // ISO 8601 datetime
  isVirtual: boolean;               // Virtual event flag
  requiresPayment: boolean;         // Payment required
  registrationFee?: number;         // Fee amount (optional)
  currentUserStatus: {
    isAuthenticated: boolean;       // User logged in
    hasPaid: boolean;               // Payment completed
    hasAcceptedTerms: boolean;      // Terms accepted
  };
}
```

**Features:**
- Auto countdown timer
- Status indicators
- Smart redirects
- Terms modal

### RTCInterface Component

**Props:**
```typescript
interface RTCInterfaceProps {
  sessionId: string;                // Session identifier
  sessionTitle: string;             // Display title
  eventId: string;                  // For leave redirect
  config: {
    sessionId: string;
    userId: string;
    userName: string;
    userRole: string;
    isInstructor: boolean;
    callsUrl?: string;              // Cloudflare Calls URL
  };
  startDatetime: string;            // Session start
  endDatetime: string;              // Session end
}
```

**Keyboard Shortcuts:**
- `Space`: Toggle mute
- `V`: Toggle video
- `S`: Toggle screen share (instructor)
- `C`: Toggle chat
- `P`: Toggle participants
- `Esc`: Leave session

### ChatPanel Component

**Props:**
```typescript
interface ChatPanelProps {
  sessionId: string;                // Session ID
  currentUserId: string;            // Current user ID
  currentUserName: string;          // Display name
  onClose: () => void;              // Close callback
}
```

**WebSocket Message Format:**
```typescript
// Outgoing - Send Message
{
  type: "message",
  id: string,
  userId: string,
  userName: string,
  message: string,
  timestamp: string (ISO 8601)
}

// Outgoing - Typing
{
  type: "typing",
  userId: string,
  userName: string
}

// Incoming - Message
{
  type: "message",
  id: string,
  userId: string,
  userName: string,
  message: string,
  timestamp: string,
  isInstructor?: boolean
}

// Incoming - Rate Limit
{
  type: "rate_limit",
  remaining: number
}
```

### ParticipantList Component

**Props:**
```typescript
interface ParticipantListProps {
  participants: Participant[];
  onClose: () => void;
}

interface Participant {
  id: string;
  name: string;
  isInstructor: boolean;
  isMuted: boolean;
  hasVideo: boolean;
  isActive: boolean;
}
```

## WebRTC Setup

### Browser Permissions

The app requires:
- Camera access (optional, for video)
- Microphone access (required)
- Screen sharing (instructor only)

### Device Selection

Users can select:
- Audio input device (microphone)
- Video input device (camera)

Access via Settings button in controls.

### Connection Quality

Automatically monitors:
- Network latency
- Packet loss
- Bandwidth

Displays: Good (green), Fair (yellow), Poor (red)

## Customization

### Styling

All components use Tailwind CSS and shadcn/ui. Customize via:

```tsx
// In tailwind.config.ts
theme: {
  extend: {
    colors: {
      'dojo-green': '#your-color',
    }
  }
}
```

### Reactions

Customize reactions in `rtc-interface.tsx`:

```tsx
const reactions = [
  { type: 'thumbs-up', icon: <ThumbsUp />, emoji: '👍' },
  { type: 'clap', icon: <Clap />, emoji: '👏' },
  // Add more...
];
```

### Terms Content

Modify terms in `event-session.tsx`:

```tsx
<ul className="space-y-2 list-disc pl-5">
  <li>Your custom term...</li>
  {/* Add more */}
</ul>
```

## Mobile Optimization

### Responsive Breakpoints
- `sm`: 640px (phones in landscape, tablets)
- `md`: 768px (tablets, small laptops)

### Touch Gestures
- Tap controls to toggle
- Scroll chat/participants
- Pinch to zoom (native)

### Layout
- Mobile: Stack (video on top, chat below)
- Desktop: Sidebar (video left, chat/participants right)

## Performance Tips

### Optimize Video Quality

Lower resolution for mobile:
```tsx
const constraints = {
  video: {
    width: { ideal: isMobile ? 640 : 1280 },
    height: { ideal: isMobile ? 480 : 720 }
  }
};
```

### Reduce Re-renders

```tsx
const MemoizedParticipant = React.memo(ParticipantItem);
```

### Lazy Load Chat

```tsx
const ChatPanel = lazy(() => import('./chat-panel'));
```

## Troubleshooting

### WebRTC Not Connecting
1. Check browser permissions
2. Verify HTTPS (required for getUserMedia)
3. Check firewall/network settings
4. Verify Cloudflare Calls credentials

### Chat Not Working
1. Check WebSocket connection
2. Verify CORS settings
3. Check backend WebSocket server running
4. Inspect browser console for errors

### Audio/Video Issues
1. Check device permissions
2. Try different browser
3. Verify device selection
4. Check if device in use by other app

### Mobile Issues
1. Use landscape orientation
2. Close other apps
3. Check network connection
4. Update browser

## Testing

### Unit Tests
```bash
npm test -- __tests__/components/training
```

### E2E Testing (Recommended Tools)
- Playwright
- Cypress
- Puppeteer

### Load Testing
- Test with 50+ participants
- Monitor CPU/memory usage
- Check network bandwidth

## Security Checklist

- [ ] Session validation on server
- [ ] Signed Cloudflare Calls URLs
- [ ] Rate limiting enabled
- [ ] Terms acceptance logged
- [ ] HTTPS in production
- [ ] Secure WebSocket (WSS)
- [ ] User authorization checks
- [ ] No sensitive data in URLs

## Deployment

### Prerequisites
1. Cloudflare Calls account
2. WebSocket server configured
3. Backend APIs implemented
4. SSL certificates installed

### Environment Setup
```bash
# Production
BACKEND_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Build
```bash
npm run build
npm start
```

### Docker (Optional)
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

## Monitoring

### Metrics to Track
- Session join rate
- Connection success rate
- Average watch time
- Chat message volume
- Disconnection rate
- Device errors

### Logging
```typescript
// Already implemented in components
console.error('Error accessing media devices:', error);
console.log('WebSocket connected');
```

Consider adding:
- Sentry for error tracking
- Analytics for usage metrics
- Performance monitoring

## Support

### Common User Questions

**Q: Why can't I join yet?**
A: Sessions open 10 minutes before start time.

**Q: Why is my video not working?**
A: Check browser permissions and device selection.

**Q: Can I share my screen?**
A: Only instructors can share screens.

**Q: How do I mute myself?**
A: Click microphone button or press Space.

**Q: Is this recorded?**
A: Recording indicator shows when active.

## Future Enhancements

### Planned Features
- [ ] Breakout rooms
- [ ] Polls and Q&A
- [ ] Hand raise queue
- [ ] Whiteboard
- [ ] Recording playback
- [ ] Closed captions
- [ ] Virtual backgrounds
- [ ] Noise suppression

### Community Requests
Submit feature requests via GitHub issues.

## License

Part of WWMAA platform - see main project LICENSE.

## Credits

Built with:
- Next.js 13+
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui
- WebRTC APIs
- react-use-websocket
- emoji-picker-react

---

**Last Updated:** November 10, 2024
**Version:** 1.0.0
**Status:** Production Ready (requires backend integration)
