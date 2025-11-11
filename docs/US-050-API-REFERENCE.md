# US-050: Chat & Interaction Features - API Reference

## Table of Contents
1. [WebSocket API](#websocket-api)
2. [REST API Endpoints](#rest-api-endpoints)
3. [Message Types](#message-types)
4. [Error Handling](#error-handling)
5. [Rate Limits](#rate-limits)

---

## WebSocket API

### Connection
```
wss://api.wwmaa.com/ws/training/{session_id}/chat?token={jwt_token}
```

**Parameters:**
- `session_id` (path): Training session UUID
- `token` (query): JWT authentication token

**Connection Flow:**
1. Client connects with JWT token
2. Server validates token and user
3. Server sends `user_joined` to other participants
4. Client receives all subsequent messages

---

## Message Types

### Client → Server

#### 1. Send Chat Message
```json
{
  "type": "chat_message",
  "message": "Hello, everyone!",
  "is_private": false,
  "recipient_id": null
}
```

**Fields:**
- `message` (string, required): Message text (1-2000 chars)
- `is_private` (boolean): Private message flag
- `recipient_id` (string): Recipient UUID for private messages

#### 2. Add Reaction
```json
{
  "type": "reaction_added",
  "message_id": "msg_uuid",
  "reaction": "👍"
}
```

**Supported Reactions:**
- 👍 (thumbs up)
- 👏 (clap)
- ❤️ (heart)
- 🔥 (fire)

#### 3. Raise Hand
```json
{
  "type": "hand_raised"
}
```

#### 4. Lower Hand
```json
{
  "type": "hand_lowered",
  "acknowledged_by": "instructor_uuid"  // optional
}
```

#### 5. Start Typing
```json
{
  "type": "typing_start"
}
```

#### 6. Stop Typing
```json
{
  "type": "typing_stop"
}
```

#### 7. Delete Message (Instructor Only)
```json
{
  "type": "delete_message",
  "message_id": "msg_uuid"
}
```

#### 8. Mute User (Instructor Only)
```json
{
  "type": "mute_user",
  "user_id": "user_uuid",
  "duration_minutes": 15,  // null for permanent
  "reason": "Spam"
}
```

#### 9. Unmute User (Instructor Only)
```json
{
  "type": "unmute_user",
  "user_id": "user_uuid"
}
```

---

### Server → Client

#### 1. Chat Message
```json
{
  "type": "chat_message",
  "id": "msg_uuid",
  "user_id": "user_uuid",
  "user_name": "John Doe",
  "message": "Hello, everyone!",
  "timestamp": "2025-11-10T14:30:00Z",
  "is_private": false,
  "recipient_id": null,
  "recipient_name": null,
  "reactions": {}
}
```

#### 2. Message Deleted
```json
{
  "type": "message_deleted",
  "message_id": "msg_uuid",
  "deleted_by": "instructor_uuid"
}
```

#### 3. User Muted
```json
{
  "type": "user_muted",
  "user_id": "user_uuid",
  "muted_by": "instructor_uuid",
  "duration_minutes": 15,
  "reason": "Spam"
}
```

#### 4. User Unmuted
```json
{
  "type": "user_unmuted",
  "user_id": "user_uuid",
  "unmuted_by": "instructor_uuid"
}
```

#### 5. Reaction Added
```json
{
  "type": "reaction_added",
  "message_id": "msg_uuid",
  "reaction": "👍",
  "user_id": "user_uuid"
}
```

#### 6. Hand Raised
```json
{
  "type": "hand_raised",
  "user_id": "user_uuid",
  "user_name": "Jane Smith",
  "raised_at": "2025-11-10T14:30:00Z"
}
```

#### 7. Hand Lowered
```json
{
  "type": "hand_lowered",
  "user_id": "user_uuid",
  "user_name": "Jane Smith",
  "acknowledged_by": "instructor_uuid"  // optional
}
```

#### 8. Typing Start
```json
{
  "type": "typing_start",
  "user_id": "user_uuid",
  "user_name": "John Doe"
}
```

#### 9. Typing Stop
```json
{
  "type": "typing_stop",
  "user_id": "user_uuid",
  "user_name": "John Doe"
}
```

#### 10. User Joined
```json
{
  "type": "user_joined",
  "user_id": "user_uuid",
  "user_name": "New User",
  "timestamp": "2025-11-10T14:30:00Z"
}
```

#### 11. User Left
```json
{
  "type": "user_left",
  "user_id": "user_uuid",
  "user_name": "Former User",
  "timestamp": "2025-11-10T14:30:00Z"
}
```

#### 12. Error
```json
{
  "type": "error",
  "error": "Rate limit exceeded: 5 messages per 10 seconds"
}
```

---

## REST API Endpoints

### 1. Send Message
```http
POST /api/training/sessions/{session_id}/chat
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "message": "Hello, class!",
  "is_private": false,
  "recipient_id": null
}
```

**Response (201 Created):**
```json
{
  "id": "msg_uuid",
  "session_id": "session_uuid",
  "user_id": "user_uuid",
  "user_name": "John Doe",
  "message": "Hello, class!",
  "is_private": false,
  "recipient_id": null,
  "recipient_name": null,
  "reactions": {},
  "timestamp": "2025-11-10T14:30:00Z",
  "is_deleted": false
}
```

---

### 2. Get Messages
```http
GET /api/training/sessions/{session_id}/chat?limit=100&offset=0
Authorization: Bearer {jwt_token}
```

**Query Parameters:**
- `limit` (integer, default: 100): Maximum messages to return (1-500)
- `offset` (integer, default: 0): Number of messages to skip

**Response (200 OK):**
```json
[
  {
    "id": "msg_uuid",
    "session_id": "session_uuid",
    "user_id": "user_uuid",
    "user_name": "John Doe",
    "message": "Hello, class!",
    "is_private": false,
    "recipient_id": null,
    "recipient_name": null,
    "reactions": {"👍": 5, "👏": 2},
    "timestamp": "2025-11-10T14:30:00Z",
    "is_deleted": false
  }
]
```

---

### 3. Delete Message (Instructor Only)
```http
DELETE /api/training/sessions/{session_id}/chat/{message_id}
Authorization: Bearer {jwt_token}
```

**Response (204 No Content)**

**Error (403 Forbidden):**
```json
{
  "detail": "Only instructors can delete messages"
}
```

---

### 4. Mute User (Instructor Only)
```http
POST /api/training/sessions/{session_id}/chat/mute
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "user_id": "user_uuid",
  "duration_minutes": 15,
  "reason": "Spam"
}
```

**Duration Options:**
- `null` - Permanent mute
- `5` - 5 minutes
- `15` - 15 minutes
- `30` - 30 minutes
- Custom value (any integer)

**Response (204 No Content)**

---

### 5. Unmute User (Instructor Only)
```http
DELETE /api/training/sessions/{session_id}/chat/mute/{user_id}
Authorization: Bearer {jwt_token}
```

**Response (204 No Content)**

---

### 6. Add Reaction
```http
POST /api/training/sessions/{session_id}/chat/reaction
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "message_id": "msg_uuid",
  "reaction": "👍"
}
```

**Response (204 No Content)**

**Error (400 Bad Request):**
```json
{
  "detail": "Invalid reaction. Must be one of: ['👍', '👏', '❤️', '🔥']"
}
```

---

### 7. Raise Hand
```http
POST /api/training/sessions/{session_id}/chat/raise-hand
Authorization: Bearer {jwt_token}
```

**Response (201 Created):**
```json
{
  "id": "hand_uuid",
  "session_id": "session_uuid",
  "user_id": "user_uuid",
  "user_name": "John Doe",
  "is_active": true,
  "raised_at": "2025-11-10T14:30:00Z"
}
```

---

### 8. Lower Hand
```http
DELETE /api/training/sessions/{session_id}/chat/raise-hand
Authorization: Bearer {jwt_token}
```

**Response (204 No Content)**

---

### 9. Get Raised Hands
```http
GET /api/training/sessions/{session_id}/chat/raise-hand
Authorization: Bearer {jwt_token}
```

**Response (200 OK):**
```json
[
  {
    "id": "hand_uuid",
    "session_id": "session_uuid",
    "user_id": "user_uuid",
    "user_name": "John Doe",
    "is_active": true,
    "raised_at": "2025-11-10T14:30:00Z"
  }
]
```

---

### 10. Export Chat (Instructor Only)
```http
GET /api/training/sessions/{session_id}/chat/export?format=json&include_private=false
Authorization: Bearer {jwt_token}
```

**Query Parameters:**
- `format` (string, required): Export format - `json`, `csv`, or `txt`
- `include_private` (boolean, default: false): Include private messages

**Response (200 OK):**
- Content-Type: `application/json`, `text/csv`, or `text/plain`
- Content-Disposition: `attachment; filename=chat_{session_id}.{format}`

**JSON Format:**
```json
[
  {
    "id": "msg_uuid",
    "session_id": "session_uuid",
    "user_id": "user_uuid",
    "user_name": "John Doe",
    "message": "Hello, class!",
    "timestamp": "2025-11-10T14:30:00Z",
    "reactions": {"👍": 5}
  }
]
```

**CSV Format:**
```csv
timestamp,user_name,message,is_private,reactions
2025-11-10T14:30:00Z,John Doe,Hello class!,false,"{""👍"": 5}"
```

**Plain Text Format:**
```
[2025-11-10T14:30:00Z] John Doe: Hello, class! | Reactions: 👍x5
```

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Error message description"
}
```

### Common HTTP Status Codes

#### 400 Bad Request
- Invalid message content
- Invalid reaction type
- Missing required fields

#### 401 Unauthorized
- Invalid or expired JWT token
- Missing authentication

#### 403 Forbidden
- Non-instructor attempting moderation actions
- User is muted
- Insufficient permissions

#### 404 Not Found
- Session not found
- Message not found
- User not found

#### 429 Too Many Requests
- Rate limit exceeded
- Message rate limit: 5 per 10 seconds
- Reaction rate limit: 10 per minute

#### 500 Internal Server Error
- Database errors
- Service failures
- Unexpected errors

---

## Rate Limits

### Message Sending
- **Limit**: 5 messages per 10 seconds
- **Scope**: Per user, per session
- **Bypass**: Instructors bypass rate limits
- **Error**: HTTP 429 or WebSocket error message

### Reactions
- **Limit**: 10 reactions per minute
- **Scope**: Per user, globally
- **Bypass**: Instructors bypass rate limits
- **Error**: HTTP 429 or WebSocket error message

### Typing Indicators
- **Throttle**: Maximum 1 event per second
- **Auto-Clear**: After 5 seconds of inactivity
- **Scope**: Per user, per session

---

## Profanity Filter

### Behavior
- Automatic detection and censoring
- Replaces profane words with asterisks
- Logs violations to audit trail

### Strike System
- **Threshold**: 3 strikes per hour
- **Action**: Auto-mute for 15 minutes
- **Reset**: Strikes expire after 1 hour
- **Notification**: User receives error message when muted

---

## Authentication

### JWT Token
Required in both WebSocket (query param) and REST API (Bearer token).

**Token Payload:**
```json
{
  "sub": "user_uuid",
  "role": "member",
  "email": "user@example.com",
  "exp": 1699632000
}
```

**Roles:**
- `public` - No chat access
- `member` - Can send messages, react, raise hand
- `instructor` - Full access including moderation
- `admin` - Full access including moderation
- `board_member` - Full access including moderation

---

## Best Practices

### WebSocket Usage
1. **Connection Management**:
   - Implement reconnection logic with exponential backoff
   - Handle connection drops gracefully
   - Store messages locally until connection restored

2. **Message Handling**:
   - Validate message types before processing
   - Handle unknown message types gracefully
   - Display errors to user in UI

3. **Performance**:
   - Throttle typing indicator events (max 1/second)
   - Batch render messages for better performance
   - Implement virtual scrolling for long chat histories

### REST API Usage
1. **Fallback Strategy**:
   - Use REST API when WebSocket unavailable
   - Poll for new messages with reasonable interval
   - Implement exponential backoff for polling

2. **Pagination**:
   - Use `limit` and `offset` for large chat histories
   - Load more messages on scroll
   - Cache loaded messages client-side

3. **Error Handling**:
   - Display rate limit errors to user
   - Retry failed requests with exponential backoff
   - Log errors for debugging

---

## Example Client Implementation

### JavaScript/TypeScript

```typescript
class ChatClient {
  private ws: WebSocket | null = null;
  private token: string;
  private sessionId: string;

  constructor(sessionId: string, token: string) {
    this.sessionId = sessionId;
    this.token = token;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const url = `wss://api.wwmaa.com/ws/training/${this.sessionId}/chat?token=${this.token}`;
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('Connected to chat');
        resolve();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      };

      this.ws.onclose = () => {
        console.log('Disconnected from chat');
        // Implement reconnection logic
        setTimeout(() => this.connect(), 5000);
      };
    });
  }

  sendMessage(message: string, isPrivate = false, recipientId?: string) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    this.ws.send(JSON.stringify({
      type: 'chat_message',
      message,
      is_private: isPrivate,
      recipient_id: recipientId
    }));
  }

  addReaction(messageId: string, reaction: string) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    this.ws.send(JSON.stringify({
      type: 'reaction_added',
      message_id: messageId,
      reaction
    }));
  }

  raiseHand() {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket not connected');
    }

    this.ws.send(JSON.stringify({
      type: 'hand_raised'
    }));
  }

  private handleMessage(data: any) {
    switch (data.type) {
      case 'chat_message':
        this.onChatMessage(data);
        break;
      case 'hand_raised':
        this.onHandRaised(data);
        break;
      case 'error':
        this.onError(data);
        break;
      // Handle other message types...
    }
  }

  private onChatMessage(data: any) {
    // Implement UI update logic
    console.log('New message:', data);
  }

  private onHandRaised(data: any) {
    // Implement UI notification
    console.log('Hand raised:', data.user_name);
  }

  private onError(data: any) {
    // Display error to user
    console.error('Chat error:', data.error);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

### Usage
```typescript
const chat = new ChatClient('session-uuid', 'jwt-token');

await chat.connect();

chat.sendMessage('Hello, everyone!');
chat.addReaction('message-uuid', '👍');
chat.raiseHand();

// Later...
chat.disconnect();
```

---

## Support

For issues or questions:
- Backend API: Contact backend team
- WebSocket connectivity: Check network and firewall settings
- Rate limiting: Review usage patterns
- Authentication: Verify JWT token validity

## Version
API Version: 1.0
Last Updated: November 10, 2025
