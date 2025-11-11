"use client";

import { X, Mic, MicOff, Video, VideoOff, Crown, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";

interface Participant {
  id: string;
  name: string;
  isInstructor: boolean;
  isMuted: boolean;
  hasVideo: boolean;
  isActive: boolean;
}

interface ParticipantListProps {
  participants: Participant[];
  onClose: () => void;
}

export function ParticipantList({
  participants,
  onClose,
}: ParticipantListProps) {
  // Separate instructors and participants
  const instructors = participants.filter((p) => p.isInstructor);
  const regularParticipants = participants.filter((p) => !p.isInstructor);

  // Count active participants
  const activeCount = participants.filter((p) => p.isActive).length;

  const ParticipantItem = ({ participant }: { participant: Participant }) => (
    <div className="flex items-center gap-3 px-3 py-2 hover:bg-gray-700/50 rounded-lg transition-colors">
      <div className="relative">
        <Avatar className="h-10 w-10">
          <AvatarFallback className="bg-dojo-green text-white font-semibold">
            {participant.name
              .split(" ")
              .map((n) => n[0])
              .join("")
              .toUpperCase()
              .slice(0, 2)}
          </AvatarFallback>
        </Avatar>
        {participant.isActive && (
          <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-gray-800 rounded-full"></div>
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-medium text-white truncate">
            {participant.name}
          </p>
          {participant.isInstructor && (
            <Crown className="h-3 w-3 text-yellow-500 flex-shrink-0" />
          )}
        </div>
        <div className="flex items-center gap-2 mt-1">
          <span
            className={`text-xs ${
              participant.isActive ? "text-green-500" : "text-gray-500"
            }`}
          >
            {participant.isActive ? "Active" : "Idle"}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-1">
        {participant.isMuted ? (
          <div className="p-1 bg-red-500/20 rounded">
            <MicOff className="h-3 w-3 text-red-500" />
          </div>
        ) : (
          <div className="p-1 bg-green-500/20 rounded">
            <Mic className="h-3 w-3 text-green-500" />
          </div>
        )}
        {participant.hasVideo ? (
          <div className="p-1 bg-green-500/20 rounded">
            <Video className="h-3 w-3 text-green-500" />
          </div>
        ) : (
          <div className="p-1 bg-gray-500/20 rounded">
            <VideoOff className="h-3 w-3 text-gray-500" />
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-white font-semibold">Participants</h3>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <User className="h-4 w-4 text-gray-400" />
            <span className="text-gray-300">
              {participants.length} Total
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-gray-300">{activeCount} Active</span>
          </div>
        </div>
      </div>

      {/* Participants List */}
      <ScrollArea className="flex-1">
        <div className="px-4 py-2 space-y-4">
          {/* Instructors Section */}
          {instructors.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Crown className="h-4 w-4 text-yellow-500" />
                <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
                  Instructors ({instructors.length})
                </h4>
              </div>
              <div className="space-y-1">
                {instructors.map((participant) => (
                  <ParticipantItem
                    key={participant.id}
                    participant={participant}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Separator */}
          {instructors.length > 0 && regularParticipants.length > 0 && (
            <Separator className="bg-gray-700" />
          )}

          {/* Regular Participants Section */}
          {regularParticipants.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <User className="h-4 w-4 text-gray-400" />
                <h4 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">
                  Participants ({regularParticipants.length})
                </h4>
              </div>
              <div className="space-y-1">
                {regularParticipants.map((participant) => (
                  <ParticipantItem
                    key={participant.id}
                    participant={participant}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {participants.length === 0 && (
            <div className="text-center py-8 text-gray-400">
              <User className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No participants yet</p>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Footer Info */}
      <div className="px-4 py-3 border-t border-gray-700">
        <div className="flex items-start gap-2 text-xs text-gray-400">
          <div className="flex-1">
            <p className="mb-1">Legend:</p>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>Active in session</span>
              </div>
              <div className="flex items-center gap-2">
                <Mic className="h-3 w-3 text-green-500" />
                <span>Microphone on</span>
              </div>
              <div className="flex items-center gap-2">
                <Video className="h-3 w-3 text-green-500" />
                <span>Camera on</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
