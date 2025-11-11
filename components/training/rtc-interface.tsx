"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  Mic,
  MicOff,
  Video,
  VideoOff,
  MonitorUp,
  PhoneOff,
  Settings,
  MessageSquare,
  Users,
  Wifi,
  WifiOff,
  Circle,
  ThumbsUp,
  Heart,
  Flame,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatPanel } from "./chat-panel";
import { ParticipantList } from "./participant-list";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface RTCConfig {
  sessionId: string;
  userId: string;
  userName: string;
  userRole: string;
  isInstructor: boolean;
  callsUrl?: string;
}

interface RTCInterfaceProps {
  sessionId: string;
  sessionTitle: string;
  eventId: string;
  config: RTCConfig;
  startDatetime: string;
  endDatetime: string;
}

interface Participant {
  id: string;
  name: string;
  isInstructor: boolean;
  isMuted: boolean;
  hasVideo: boolean;
  isActive: boolean;
}

interface Reaction {
  id: string;
  type: string;
  icon: React.ReactNode | string;
  timestamp: number;
  x: number;
  y: number;
}

export function RTCInterface({
  sessionId,
  sessionTitle,
  eventId,
  config,
  startDatetime,
  endDatetime,
}: RTCInterfaceProps) {
  // State management
  const [isMuted, setIsMuted] = useState(true);
  const [hasVideo, setHasVideo] = useState(false);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isParticipantsOpen, setIsParticipantsOpen] = useState(false);
  const [connectionQuality, setConnectionQuality] = useState<
    "good" | "medium" | "poor"
  >("good");
  const [isRecording, setIsRecording] = useState(false);
  const [showLeaveDialog, setShowLeaveDialog] = useState(false);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [reactions, setReactions] = useState<Reaction[]>([]);
  const [audioDevices, setAudioDevices] = useState<MediaDeviceInfo[]>([]);
  const [videoDevices, setVideoDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedAudioDevice, setSelectedAudioDevice] = useState<string>("");
  const [selectedVideoDevice, setSelectedVideoDevice] = useState<string>("");
  const [localStream, setLocalStream] = useState<MediaStream | null>(null);

  // Refs
  const localVideoRef = useRef<HTMLVideoElement>(null);
  const peerConnectionRef = useRef<RTCPeerConnection | null>(null);

  // Initialize media devices
  useEffect(() => {
    async function getDevices() {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter(
          (device) => device.kind === "audioinput"
        );
        const videoInputs = devices.filter(
          (device) => device.kind === "videoinput"
        );

        setAudioDevices(audioInputs);
        setVideoDevices(videoInputs);

        if (audioInputs.length > 0) {
          setSelectedAudioDevice(audioInputs[0].deviceId);
        }
        if (videoInputs.length > 0) {
          setSelectedVideoDevice(videoInputs[0].deviceId);
        }
      } catch (error) {
        console.error("Error enumerating devices:", error);
      }
    }

    getDevices();
  }, []);

  // Initialize local media stream
  useEffect(() => {
    async function initMediaStream() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: selectedAudioDevice
            ? { deviceId: { exact: selectedAudioDevice } }
            : true,
          video: false, // Start with video off
        });

        setLocalStream(stream);

        // Mute by default
        stream.getAudioTracks().forEach((track) => {
          track.enabled = false;
        });

        if (localVideoRef.current) {
          localVideoRef.current.srcObject = stream;
        }
      } catch (error) {
        console.error("Error accessing media devices:", error);
      }
    }

    if (selectedAudioDevice) {
      initMediaStream();
    }

    return () => {
      if (localStream) {
        localStream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [selectedAudioDevice]);

  // Track attendance
  useEffect(() => {
    // Record join time
    const recordJoin = async () => {
      try {
        await fetch(`/api/training/${sessionId}/attend`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            userId: config.userId,
            joinedAt: new Date().toISOString(),
          }),
        });
      } catch (error) {
        console.error("Error recording attendance:", error);
      }
    };

    recordJoin();

    // Update watch time every minute
    const watchTimeInterval = setInterval(async () => {
      try {
        await fetch(`/api/training/${sessionId}/attend`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            userId: config.userId,
            watchTime: 60, // 1 minute
          }),
        });
      } catch (error) {
        console.error("Error updating watch time:", error);
      }
    }, 60000);

    return () => {
      clearInterval(watchTimeInterval);
    };
  }, [sessionId, config.userId]);

  // Toggle microphone
  const toggleMute = useCallback(() => {
    if (localStream) {
      const audioTracks = localStream.getAudioTracks();
      audioTracks.forEach((track) => {
        track.enabled = !track.enabled;
      });
      setIsMuted(!isMuted);
    }
  }, [localStream, isMuted]);

  // Toggle video
  const toggleVideo = useCallback(async () => {
    if (!localStream) return;

    if (hasVideo) {
      // Turn off video
      const videoTracks = localStream.getVideoTracks();
      videoTracks.forEach((track) => {
        track.stop();
        localStream.removeTrack(track);
      });
      setHasVideo(false);
    } else {
      // Turn on video
      try {
        const videoStream = await navigator.mediaDevices.getUserMedia({
          video: selectedVideoDevice
            ? { deviceId: { exact: selectedVideoDevice } }
            : true,
        });

        const videoTrack = videoStream.getVideoTracks()[0];
        localStream.addTrack(videoTrack);

        if (localVideoRef.current) {
          localVideoRef.current.srcObject = localStream;
        }

        setHasVideo(true);
      } catch (error) {
        console.error("Error enabling video:", error);
      }
    }
  }, [localStream, hasVideo, selectedVideoDevice]);

  // Toggle screen share
  const toggleScreenShare = useCallback(async () => {
    if (!config.isInstructor) return;

    if (isScreenSharing) {
      // Stop screen sharing
      setIsScreenSharing(false);
    } else {
      // Start screen sharing
      try {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
        });

        // Handle when user clicks "Stop sharing" in browser UI
        screenStream.getVideoTracks()[0].addEventListener("ended", () => {
          setIsScreenSharing(false);
        });

        setIsScreenSharing(true);
      } catch (error) {
        console.error("Error sharing screen:", error);
      }
    }
  }, [isScreenSharing, config.isInstructor]);

  // Leave session
  const handleLeaveSession = () => {
    setShowLeaveDialog(true);
  };

  const confirmLeave = async () => {
    // Stop all tracks
    if (localStream) {
      localStream.getTracks().forEach((track) => track.stop());
    }

    // Close peer connection
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
    }

    // Redirect to event page
    window.location.href = `/events/${eventId}`;
  };

  // Send reaction
  const sendReaction = (type: string, icon: React.ReactNode | string) => {
    const newReaction: Reaction = {
      id: `${Date.now()}-${Math.random()}`,
      type,
      icon,
      timestamp: Date.now(),
      x: Math.random() * 80 + 10, // 10-90% from left
      y: 100,
    };

    setReactions((prev) => [...prev, newReaction]);

    // Remove reaction after animation
    setTimeout(() => {
      setReactions((prev) => prev.filter((r) => r.id !== newReaction.id));
    }, 3000);
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      switch (e.key.toLowerCase()) {
        case " ":
          e.preventDefault();
          toggleMute();
          break;
        case "v":
          e.preventDefault();
          toggleVideo();
          break;
        case "s":
          if (config.isInstructor) {
            e.preventDefault();
            toggleScreenShare();
          }
          break;
        case "c":
          e.preventDefault();
          setIsChatOpen((prev) => !prev);
          break;
        case "p":
          e.preventDefault();
          setIsParticipantsOpen((prev) => !prev);
          break;
        case "escape":
          e.preventDefault();
          handleLeaveSession();
          break;
      }
    };

    window.addEventListener("keydown", handleKeyPress);
    return () => window.removeEventListener("keydown", handleKeyPress);
  }, [toggleMute, toggleVideo, toggleScreenShare, config.isInstructor]);

  // Mock participants (in production, this would come from WebRTC)
  useEffect(() => {
    setParticipants([
      {
        id: config.userId,
        name: config.userName,
        isInstructor: config.isInstructor,
        isMuted,
        hasVideo,
        isActive: true,
      },
    ]);
  }, [config, isMuted, hasVideo]);

  return (
    <div className="flex flex-col h-screen bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between px-2 sm:px-4 py-3 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-2 sm:gap-4 min-w-0">
          <h1 className="text-white font-semibold text-sm sm:text-lg truncate max-w-[150px] sm:max-w-md">
            {sessionTitle}
          </h1>
          {isRecording && (
            <Badge variant="destructive" className="flex items-center gap-1 text-xs">
              <Circle className="h-2 w-2 fill-current animate-pulse" />
              <span className="hidden sm:inline">Recording</span>
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-1 sm:gap-2">
          {/* Connection Quality */}
          <div className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 bg-gray-700 rounded-full">
            {connectionQuality === "good" ? (
              <Wifi className="h-3 w-3 sm:h-4 sm:w-4 text-green-500" />
            ) : connectionQuality === "medium" ? (
              <Wifi className="h-3 w-3 sm:h-4 sm:w-4 text-yellow-500" />
            ) : (
              <WifiOff className="h-3 w-3 sm:h-4 sm:w-4 text-red-500" />
            )}
            <span className="text-xs text-gray-300 hidden sm:inline">
              {connectionQuality === "good"
                ? "Good"
                : connectionQuality === "medium"
                ? "Fair"
                : "Poor"}
            </span>
          </div>

          {/* Participant count */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsParticipantsOpen(!isParticipantsOpen)}
            className="text-white hover:bg-gray-700"
          >
            <Users className="h-3 w-3 sm:h-4 sm:w-4 sm:mr-2" />
            <span className="hidden sm:inline">{participants.length}</span>
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
        {/* Video Area */}
        <div className="flex-1 relative">
          {/* Instructor Video (Large) */}
          <div className="absolute inset-2 sm:inset-4 bg-gray-800 rounded-lg overflow-hidden">
            <video
              ref={localVideoRef}
              autoPlay
              muted
              playsInline
              className={cn(
                "w-full h-full object-cover",
                !hasVideo && "hidden"
              )}
            />
            {!hasVideo && (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="w-16 h-16 sm:w-24 sm:h-24 bg-dojo-green rounded-full flex items-center justify-center mx-auto mb-2 sm:mb-4">
                    <span className="text-2xl sm:text-4xl text-white font-bold">
                      {config.userName.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <p className="text-white font-medium text-sm sm:text-base">{config.userName}</p>
                  {config.isInstructor && (
                    <Badge className="mt-2">Instructor</Badge>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Participant Grid (Bottom) - Hidden on mobile when chat is open */}
          <div className={cn(
            "absolute bottom-2 sm:bottom-4 left-2 sm:left-4 right-2 sm:right-4 flex gap-1 sm:gap-2 overflow-x-auto",
            isChatOpen && "hidden md:flex"
          )}>
            {participants.slice(0, 6).map((participant) => (
              <div
                key={participant.id}
                className="flex-shrink-0 w-20 h-16 sm:w-32 sm:h-24 bg-gray-800 rounded-lg relative overflow-hidden border-2 border-gray-700"
              >
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="w-8 h-8 sm:w-12 sm:h-12 bg-gray-700 rounded-full flex items-center justify-center mx-auto">
                      <span className="text-sm sm:text-lg text-white font-semibold">
                        {participant.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs text-white mt-1 truncate px-1 sm:px-2 hidden sm:block">
                      {participant.name}
                    </p>
                  </div>
                </div>
                {participant.isMuted && (
                  <div className="absolute top-1 right-1 bg-red-500 rounded-full p-0.5 sm:p-1">
                    <MicOff className="h-2 w-2 sm:h-3 sm:w-3 text-white" />
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Reactions Overlay */}
          <div className="absolute inset-0 pointer-events-none">
            {reactions.map((reaction) => (
              <div
                key={reaction.id}
                className="absolute animate-float-up text-2xl sm:text-4xl"
                style={{
                  left: `${reaction.x}%`,
                  bottom: "10%",
                }}
              >
                {reaction.icon}
              </div>
            ))}
          </div>
        </div>

        {/* Chat Panel - Full width on mobile, sidebar on desktop */}
        {isChatOpen && (
          <div className="w-full md:w-80 h-64 md:h-auto border-t md:border-t-0 md:border-l border-gray-700 bg-gray-800">
            <ChatPanel
              sessionId={sessionId}
              currentUserId={config.userId}
              currentUserName={config.userName}
              onClose={() => setIsChatOpen(false)}
            />
          </div>
        )}

        {/* Participant List Panel - Full width on mobile, sidebar on desktop */}
        {isParticipantsOpen && (
          <div className="w-full md:w-80 h-64 md:h-auto border-t md:border-t-0 md:border-l border-gray-700 bg-gray-800">
            <ParticipantList
              participants={participants}
              onClose={() => setIsParticipantsOpen(false)}
            />
          </div>
        )}
      </div>

      {/* Controls Bar */}
      <div className="px-2 sm:px-4 py-3 sm:py-4 bg-gray-800 border-t border-gray-700">
        <div className="flex flex-col gap-2 sm:gap-3">
          <div className="flex items-center justify-between max-w-4xl mx-auto w-full">
            {/* Left: Main Controls */}
            <div className="flex items-center gap-1 sm:gap-2">
              <Button
                variant={isMuted ? "destructive" : "secondary"}
                size="lg"
                onClick={toggleMute}
                className="rounded-full h-10 w-10 sm:h-12 sm:w-12 p-0"
              >
                {isMuted ? (
                  <MicOff className="h-4 w-4 sm:h-5 sm:w-5" />
                ) : (
                  <Mic className="h-4 w-4 sm:h-5 sm:w-5" />
                )}
              </Button>

              <Button
                variant={hasVideo ? "secondary" : "destructive"}
                size="lg"
                onClick={toggleVideo}
                className="rounded-full h-10 w-10 sm:h-12 sm:w-12 p-0"
              >
                {hasVideo ? (
                  <Video className="h-4 w-4 sm:h-5 sm:w-5" />
                ) : (
                  <VideoOff className="h-4 w-4 sm:h-5 sm:w-5" />
                )}
              </Button>

              {config.isInstructor && (
                <Button
                  variant={isScreenSharing ? "default" : "secondary"}
                  size="lg"
                  onClick={toggleScreenShare}
                  className="rounded-full h-10 w-10 sm:h-12 sm:w-12 p-0 hidden sm:flex"
                >
                  <MonitorUp className="h-4 w-4 sm:h-5 sm:w-5" />
                </Button>
              )}

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="secondary" size="lg" className="rounded-full h-10 w-10 sm:h-12 sm:w-12 p-0 hidden sm:flex">
                    <Settings className="h-4 w-4 sm:h-5 sm:w-5" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-64">
                  <DropdownMenuLabel>Audio Settings</DropdownMenuLabel>
                  {audioDevices.map((device) => (
                    <DropdownMenuItem
                      key={device.deviceId}
                      onClick={() => setSelectedAudioDevice(device.deviceId)}
                    >
                      {device.label || `Microphone ${device.deviceId.slice(0, 5)}`}
                      {selectedAudioDevice === device.deviceId && " ✓"}
                    </DropdownMenuItem>
                  ))}
                  <DropdownMenuSeparator />
                  <DropdownMenuLabel>Video Settings</DropdownMenuLabel>
                  {videoDevices.map((device) => (
                    <DropdownMenuItem
                      key={device.deviceId}
                      onClick={() => setSelectedVideoDevice(device.deviceId)}
                    >
                      {device.label || `Camera ${device.deviceId.slice(0, 5)}`}
                      {selectedVideoDevice === device.deviceId && " ✓"}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            {/* Center: Reactions - Hidden on mobile */}
            <div className="hidden sm:flex items-center gap-1 sm:gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => sendReaction("thumbs-up", "👍")}
                className="text-white hover:bg-gray-700 h-8 w-8 p-0"
              >
                👍
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => sendReaction("clap", "👏")}
                className="text-white hover:bg-gray-700 h-8 w-8 p-0"
              >
                👏
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => sendReaction("heart", "❤️")}
                className="text-white hover:bg-gray-700 h-8 w-8 p-0"
              >
                ❤️
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => sendReaction("fire", "🔥")}
                className="text-white hover:bg-gray-700 h-8 w-8 p-0"
              >
                🔥
              </Button>
            </div>

            {/* Right: Secondary Controls */}
            <div className="flex items-center gap-1 sm:gap-2">
              <Button
                variant="secondary"
                size="lg"
                onClick={() => setIsChatOpen(!isChatOpen)}
                className={cn(
                  "rounded-full h-10 w-10 sm:h-12 sm:w-12 p-0",
                  isChatOpen && "bg-dojo-green text-white"
                )}
              >
                <MessageSquare className="h-4 w-4 sm:h-5 sm:w-5" />
              </Button>

              <Button
                variant="destructive"
                size="lg"
                onClick={handleLeaveSession}
                className="rounded-full h-10 w-10 sm:h-12 sm:w-12 p-0"
              >
                <PhoneOff className="h-4 w-4 sm:h-5 sm:w-5" />
              </Button>
            </div>
          </div>

          {/* Keyboard Shortcuts Hint - Hidden on mobile */}
          <div className="text-center hidden sm:block">
            <p className="text-xs text-gray-400">
              Shortcuts: Space=Mute | V=Video | {config.isInstructor && "S=Share | "}
              C=Chat | P=Participants | Esc=Leave
            </p>
          </div>
        </div>
      </div>

      {/* Leave Confirmation Dialog */}
      <Dialog open={showLeaveDialog} onOpenChange={setShowLeaveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Leave Session?</DialogTitle>
            <DialogDescription>
              Are you sure you want to leave this training session? You can rejoin
              at any time while the session is active.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2 mt-4">
            <Button
              variant="outline"
              onClick={() => setShowLeaveDialog(false)}
            >
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmLeave}>
              Leave Session
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <style jsx>{`
        @keyframes float-up {
          0% {
            transform: translateY(0) scale(1);
            opacity: 1;
          }
          100% {
            transform: translateY(-300px) scale(1.5);
            opacity: 0;
          }
        }
        .animate-float-up {
          animation: float-up 3s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
