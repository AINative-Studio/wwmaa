"use client";

import { useState, useEffect, useRef } from "react";
import { Send, X, Smile, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import useWebSocket, { ReadyState } from "react-use-websocket";
import EmojiPicker, { EmojiClickData } from "emoji-picker-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

interface ChatMessage {
  id: string;
  userId: string;
  userName: string;
  message: string;
  timestamp: string;
  isInstructor?: boolean;
}

interface ChatPanelProps {
  sessionId: string;
  currentUserId: string;
  currentUserName: string;
  onClose: () => void;
}

export function ChatPanel({
  sessionId,
  currentUserId,
  currentUserName,
  onClose,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [newMessage, setNewMessage] = useState("");
  const [typingUsers, setTypingUsers] = useState<Set<string>>(new Set());
  const [isEmojiPickerOpen, setIsEmojiPickerOpen] = useState(false);
  const [rateLimitRemaining, setRateLimitRemaining] = useState(10);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // WebSocket connection
  const socketUrl = `${
    process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"
  }/ws/training/${sessionId}/chat`;

  const { sendMessage: sendWsMessage, lastMessage, readyState } = useWebSocket(
    socketUrl,
    {
      onOpen: () => console.log("WebSocket connected"),
      onClose: () => console.log("WebSocket disconnected"),
      onError: (error) => console.error("WebSocket error:", error),
      shouldReconnect: () => true,
      reconnectAttempts: 10,
      reconnectInterval: 3000,
    }
  );

  // Handle incoming messages
  useEffect(() => {
    if (lastMessage !== null) {
      try {
        const data = JSON.parse(lastMessage.data);

        switch (data.type) {
          case "message":
            setMessages((prev) => [
              ...prev,
              {
                id: data.id,
                userId: data.userId,
                userName: data.userName,
                message: data.message,
                timestamp: data.timestamp,
                isInstructor: data.isInstructor,
              },
            ]);
            // Remove user from typing indicator
            setTypingUsers((prev) => {
              const newSet = new Set(prev);
              newSet.delete(data.userId);
              return newSet;
            });
            break;

          case "typing":
            if (data.userId !== currentUserId) {
              setTypingUsers((prev) => new Set(prev).add(data.userName));
              // Remove typing indicator after 3 seconds
              setTimeout(() => {
                setTypingUsers((prev) => {
                  const newSet = new Set(prev);
                  newSet.delete(data.userName);
                  return newSet;
                });
              }, 3000);
            }
            break;

          case "rate_limit":
            setRateLimitRemaining(data.remaining);
            break;

          default:
            break;
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    }
  }, [lastMessage, currentUserId]);

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Send typing indicator
  const handleTyping = () => {
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    sendWsMessage(
      JSON.stringify({
        type: "typing",
        userId: currentUserId,
        userName: currentUserName,
      })
    );

    typingTimeoutRef.current = setTimeout(() => {
      // Stop typing indicator after 3 seconds
    }, 3000);
  };

  // Send message
  const handleSendMessage = () => {
    if (!newMessage.trim() || readyState !== ReadyState.OPEN) {
      return;
    }

    if (rateLimitRemaining <= 0) {
      alert("You are sending messages too quickly. Please wait a moment.");
      return;
    }

    const messageData = {
      type: "message",
      id: `${Date.now()}-${Math.random()}`,
      userId: currentUserId,
      userName: currentUserName,
      message: newMessage.trim(),
      timestamp: new Date().toISOString(),
    };

    sendWsMessage(JSON.stringify(messageData));
    setNewMessage("");
    setRateLimitRemaining((prev) => Math.max(0, prev - 1));

    // Reset rate limit after 10 seconds
    setTimeout(() => {
      setRateLimitRemaining((prev) => Math.min(10, prev + 1));
    }, 10000);
  };

  // Handle emoji selection
  const handleEmojiClick = (emojiData: EmojiClickData) => {
    setNewMessage((prev) => prev + emojiData.emoji);
    setIsEmojiPickerOpen(false);
  };

  // Format timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  };

  const connectionStatus = {
    [ReadyState.CONNECTING]: "Connecting...",
    [ReadyState.OPEN]: "Connected",
    [ReadyState.CLOSING]: "Closing...",
    [ReadyState.CLOSED]: "Disconnected",
    [ReadyState.UNINSTANTIATED]: "Not connected",
  }[readyState];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <h3 className="text-white font-semibold">Chat</h3>
          <Badge
            variant={readyState === ReadyState.OPEN ? "default" : "secondary"}
            className="text-xs"
          >
            {readyState === ReadyState.OPEN ? (
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                Live
              </span>
            ) : (
              <span className="flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" />
                {connectionStatus}
              </span>
            )}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className="text-gray-400 hover:text-white"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 px-4 py-2">
        <div className="space-y-3">
          {messages.length === 0 && (
            <div className="text-center py-8 text-gray-400">
              <p className="text-sm">No messages yet</p>
              <p className="text-xs mt-1">Be the first to say something!</p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${
                msg.userId === currentUserId ? "items-end" : "items-start"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs text-gray-400">
                  {msg.userName}
                  {msg.isInstructor && (
                    <Badge className="ml-1 text-xs" variant="secondary">
                      Instructor
                    </Badge>
                  )}
                </span>
                <span className="text-xs text-gray-500">
                  {formatTime(msg.timestamp)}
                </span>
              </div>
              <div
                className={`px-3 py-2 rounded-lg max-w-[80%] break-words ${
                  msg.userId === currentUserId
                    ? "bg-dojo-green text-white"
                    : "bg-gray-700 text-white"
                }`}
              >
                <p className="text-sm">{msg.message}</p>
              </div>
            </div>
          ))}

          {/* Typing Indicators */}
          {typingUsers.size > 0 && (
            <div className="flex items-center gap-2 text-gray-400">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></span>
              </div>
              <span className="text-xs">
                {Array.from(typingUsers).join(", ")} {typingUsers.size === 1 ? "is" : "are"} typing...
              </span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="px-4 py-3 border-t border-gray-700">
        {rateLimitRemaining < 3 && (
          <div className="mb-2 text-xs text-yellow-500">
            Rate limit: {rateLimitRemaining} messages remaining
          </div>
        )}

        <div className="flex items-center gap-2">
          <Popover open={isEmojiPickerOpen} onOpenChange={setIsEmojiPickerOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="text-gray-400 hover:text-white"
              >
                <Smile className="h-5 w-5" />
              </Button>
            </PopoverTrigger>
            <PopoverContent side="top" align="start" className="w-auto p-0">
              <EmojiPicker onEmojiClick={handleEmojiClick} />
            </PopoverContent>
          </Popover>

          <Input
            value={newMessage}
            onChange={(e) => {
              setNewMessage(e.target.value);
              handleTyping();
            }}
            onKeyPress={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            placeholder="Type a message..."
            className="flex-1 bg-gray-700 border-gray-600 text-white placeholder:text-gray-400"
            maxLength={500}
            disabled={readyState !== ReadyState.OPEN}
          />

          <Button
            onClick={handleSendMessage}
            disabled={
              !newMessage.trim() ||
              readyState !== ReadyState.OPEN ||
              rateLimitRemaining <= 0
            }
            size="sm"
            className="bg-dojo-green hover:bg-dojo-green/90"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>

        <p className="text-xs text-gray-500 mt-2">
          Press Enter to send • Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
