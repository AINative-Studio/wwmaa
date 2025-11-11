# VOD Player Developer Guide

## Quick Start

### Accessing a VOD Session
```typescript
// Navigate to:
/training/[sessionId]/vod

// Example:
/training/abc123/vod
```

### Component Architecture

```
VOD Page (Server Component)
├── VOD Player (Client Component)
│   ├── Video Element
│   ├── Custom Controls Overlay
│   └── Progress Tracking
├── Transcript Panel (Client Component)
│   ├── VTT Parser
│   ├── Search Feature
│   └── Download Feature
├── Bookmarks Panel (Client Component)
│   ├── Bookmark List
│   ├── Add Bookmark Dialog
│   ├── Edit Bookmark Dialog
│   └── Delete Confirmation
└── Related Videos (Client Component)
    ├── Video Grid
    └── Lazy Loading
```

## Custom Events System

The VOD player uses a custom event system for communication between components:

### Video Time Updates
```typescript
// Dispatched by: VOD Player
// Listened by: Transcript Panel, Bookmarks Panel

window.dispatchEvent(
  new CustomEvent("vod-time-update", {
    detail: { currentTime: 120 }
  })
);

// Listen for updates:
window.addEventListener("vod-time-update", (e) => {
  console.log("Current time:", e.detail.currentTime);
});
```

### Seek Commands
```typescript
// Dispatched by: Transcript Panel, Bookmarks Panel
// Listened by: VOD Player

window.dispatchEvent(
  new CustomEvent("vod-seek-to", {
    detail: { time: 180 }
  })
);

// Listen for seeks:
window.addEventListener("vod-seek-to", (e) => {
  videoRef.current.currentTime = e.detail.time;
});
```

## API Integration

### Fetching Watch Progress
```typescript
const response = await fetch(
  `/api/training/${sessionId}/progress?userId=${userId}`
);
const data = await response.json();
// Returns: { position: number, completed: boolean, totalWatchTime: number }
```

### Saving Watch Progress
```typescript
await fetch(`/api/training/${sessionId}/progress`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    userId: "user-123",
    lastWatchedPosition: 120,
    totalWatchTime: 120,
    completed: false
  })
});
```

### Managing Bookmarks

**List Bookmarks:**
```typescript
const response = await fetch(
  `/api/training/${sessionId}/bookmarks?userId=${userId}`
);
const data = await response.json();
// Returns: { bookmarks: Bookmark[], count: number }
```

**Create Bookmark:**
```typescript
await fetch(`/api/training/${sessionId}/bookmarks`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    userId: "user-123",
    timestamp: 120,
    note: "Important moment"
  })
});
```

**Update Bookmark:**
```typescript
await fetch(`/api/training/${sessionId}/bookmarks/${bookmarkId}`, {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    userId: "user-123",
    note: "Updated note"
  })
});
```

**Delete Bookmark:**
```typescript
await fetch(`/api/training/${sessionId}/bookmarks/${bookmarkId}`, {
  method: "DELETE",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ userId: "user-123" })
});
```

## Component Props

### VODPlayer
```typescript
interface VODPlayerProps {
  sessionId: string;           // Session identifier
  streamUrl: string;           // Video stream URL
  title: string;               // Video title
  duration?: number;           // Video duration in seconds
  thumbnailUrl?: string;       // Poster image URL
  initialPosition?: number;    // Resume position in seconds
  userId: string;              // Current user ID
}
```

### TranscriptPanel
```typescript
interface TranscriptPanelProps {
  sessionId: string;           // Session identifier
  transcriptUrl: string;       // VTT file URL
}
```

### BookmarksPanel
```typescript
interface BookmarksPanelProps {
  sessionId: string;           // Session identifier
  userId: string;              // Current user ID
}
```

### RelatedVideos
```typescript
interface RelatedVideosProps {
  sessions: RelatedSession[];  // Array of related sessions
}

interface RelatedSession {
  id: string;
  title: string;
  description?: string;
  thumbnailUrl?: string;
  duration?: number;
  instructorName: string;
  category?: string;
  requiredTier?: string;
  recordingId?: string;
}
```

## Keyboard Shortcuts Reference

| Key | Action |
|-----|--------|
| `Space` or `K` | Toggle play/pause |
| `F` | Toggle fullscreen |
| `M` | Toggle mute |
| `←` or `J` | Skip back 10 seconds |
| `→` or `L` | Skip forward 10 seconds |
| `↑` | Increase volume |
| `↓` | Decrease volume |
| `0-9` | Jump to 0%-90% of video |

## Time Formatting

```typescript
// Format seconds to MM:SS or HH:MM:SS
function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);

  if (h > 0) {
    return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  }
  return `${m}:${s.toString().padStart(2, "0")}`;
}
```

## VTT Transcript Format

```vtt
WEBVTT

00:00:00.000 --> 00:00:05.000
First caption text here.

00:00:05.000 --> 00:00:10.000
Second caption text here.

00:00:10.000 --> 00:00:15.000
Third caption text here.
```

## Access Control Flow

```typescript
// Server-side in page.tsx
async function checkUserAccess(sessionId: string) {
  // 1. Check if user is authenticated
  if (!isAuthenticated) {
    return { hasAccess: false, reason: "unauthorized" };
  }

  // 2. Check user tier vs session requirement
  const session = await getSession(sessionId);
  const userTier = await getUserTier(userId);

  if (!hasSufficientTier(userTier, session.requiredTier)) {
    return { hasAccess: false, reason: "tier-insufficient" };
  }

  // 3. Grant access
  return { hasAccess: true, userId, userTier };
}
```

## Database Schema (ZeroDB)

### session_attendance Collection
```typescript
{
  id: string;
  userId: string;
  sessionId: string;
  lastWatchedPosition: number;     // in seconds
  totalWatchTime: number;          // in seconds
  completed: boolean;              // true if watched 90%+
  updatedAt: string;               // ISO timestamp
}
```

### user_bookmarks Collection
```typescript
{
  id: string;
  userId: string;
  sessionId: string;
  timestamp: number;               // in seconds
  note: string;
  createdAt: string;               // ISO timestamp
  updatedAt: string;               // ISO timestamp
}
```

## Testing

### Running Tests
```bash
# Test all VOD components
npm test -- __tests__/components/training/vod-player.test.tsx
npm test -- __tests__/components/training/transcript-panel.test.tsx
npm test -- __tests__/components/training/bookmarks-panel.test.tsx
npm test -- __tests__/components/training/related-videos.test.tsx

# Test all VOD APIs
npm test -- __tests__/api/training/progress.test.ts
npm test -- __tests__/api/training/bookmarks.test.ts

# Test with coverage
npm test -- __tests__/components/training --coverage
```

### Example Test
```typescript
import { render, screen } from "@testing-library/react";
import { VODPlayer } from "@/components/training/vod-player";

test("renders video player", () => {
  render(
    <VODPlayer
      sessionId="test-session"
      streamUrl="https://example.com/video.mp4"
      title="Test Video"
      userId="user-123"
    />
  );

  expect(screen.getByText("Test Video")).toBeInTheDocument();
});
```

## Common Issues & Solutions

### Issue: Video doesn't play
**Solution:** Check that streamUrl is valid and accessible. Ensure CORS headers are set correctly.

### Issue: Progress not saving
**Solution:** Verify userId is passed correctly. Check network tab for failed API calls.

### Issue: Bookmarks not showing
**Solution:** Ensure API endpoint is returning data. Check userId matches between creation and retrieval.

### Issue: Transcript not syncing
**Solution:** Verify VTT file format is correct. Check that time update events are firing.

### Issue: Keyboard shortcuts not working
**Solution:** Ensure no input elements are focused. Check for event listener conflicts.

## Performance Tips

1. **Lazy Load Related Videos:** Only show 3 initially, load more on demand
2. **Debounce Progress Saves:** Save every 10 seconds, not on every time update
3. **Memo Callbacks:** Use `useCallback` for event handlers
4. **Optimize Re-renders:** Use `React.memo` for pure components
5. **Clean Up Events:** Always remove event listeners on unmount

## Security Checklist

✅ Validate user ownership for bookmarks
✅ Verify session access before serving video
✅ Use signed URLs with expiry for streams
✅ Sanitize user input in notes
✅ Rate limit API endpoints
✅ Implement CSRF protection

## Deployment Checklist

✅ Environment variables configured
✅ Database migrations run
✅ CDN configured for video delivery
✅ Error tracking enabled
✅ Analytics configured
✅ Mobile testing completed
✅ Load testing passed
✅ Security audit completed

## Support & Documentation

- **Full Implementation Doc:** `/docs/US-048-VOD-PLAYER-IMPLEMENTATION.md`
- **Completion Summary:** `/US-048-IMPLEMENTATION-COMPLETE.md`
- **Component Tests:** `/__tests__/components/training/`
- **API Tests:** `/__tests__/api/training/`

## Quick Commands

```bash
# Start development server
npm run dev

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Type check
npm run typecheck

# Build for production
npm run build

# Start production server
npm start
```

---

**Last Updated:** November 10, 2024
**Version:** 1.0.0
**Status:** Production Ready
