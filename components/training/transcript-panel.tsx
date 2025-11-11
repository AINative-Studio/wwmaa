"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Download, Search, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/use-toast";

interface TranscriptPanelProps {
  sessionId: string;
  transcriptUrl: string;
}

interface TranscriptCue {
  id: string;
  startTime: number;
  endTime: number;
  text: string;
}

export function TranscriptPanel({
  sessionId,
  transcriptUrl,
}: TranscriptPanelProps) {
  const { toast } = useToast();
  const [isOpen, setIsOpen] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptCue[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [currentCueId, setCurrentCueId] = useState<string | null>(null);
  const [filteredTranscript, setFilteredTranscript] = useState<TranscriptCue[]>([]);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const activeLineRef = useRef<HTMLDivElement>(null);

  // Parse VTT format
  const parseVTT = (vttContent: string): TranscriptCue[] => {
    const lines = vttContent.split("\n");
    const cues: TranscriptCue[] = [];
    let currentCue: Partial<TranscriptCue> = {};
    let cueId = 0;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();

      // Skip WEBVTT header and empty lines
      if (line.startsWith("WEBVTT") || line === "") {
        continue;
      }

      // Check if line is a timestamp
      if (line.includes("-->")) {
        const [startStr, endStr] = line.split("-->").map((s) => s.trim());
        currentCue.startTime = parseVTTTimestamp(startStr);
        currentCue.endTime = parseVTTTimestamp(endStr);
      } else if (currentCue.startTime !== undefined) {
        // This is the text content
        currentCue.text = line;
        currentCue.id = `cue-${cueId++}`;
        cues.push(currentCue as TranscriptCue);
        currentCue = {};
      }
    }

    return cues;
  };

  // Parse VTT timestamp to seconds
  const parseVTTTimestamp = (timestamp: string): number => {
    const parts = timestamp.split(":");
    if (parts.length === 3) {
      const [hours, minutes, seconds] = parts;
      return (
        parseInt(hours) * 3600 +
        parseInt(minutes) * 60 +
        parseFloat(seconds)
      );
    } else if (parts.length === 2) {
      const [minutes, seconds] = parts;
      return parseInt(minutes) * 60 + parseFloat(seconds);
    }
    return 0;
  };

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  // Load transcript
  const loadTranscript = useCallback(async () => {
    if (transcript.length > 0) return; // Already loaded

    setLoading(true);
    try {
      const response = await fetch(transcriptUrl);
      if (!response.ok) {
        throw new Error("Failed to load transcript");
      }

      const vttContent = await response.text();
      const parsedCues = parseVTT(vttContent);
      setTranscript(parsedCues);
      setFilteredTranscript(parsedCues);
    } catch (error) {
      console.error("Error loading transcript:", error);
      toast({
        title: "Error",
        description: "Failed to load transcript",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [transcriptUrl, transcript.length, toast]);

  // Load transcript when panel is opened
  useEffect(() => {
    if (isOpen) {
      loadTranscript();
    }
  }, [isOpen, loadTranscript]);

  // Filter transcript based on search
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredTranscript(transcript);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = transcript.filter((cue) =>
      cue.text.toLowerCase().includes(query)
    );
    setFilteredTranscript(filtered);
  }, [searchQuery, transcript]);

  // Listen for video time updates (from parent via custom event)
  useEffect(() => {
    const handleTimeUpdate = (e: CustomEvent<{ currentTime: number }>) => {
      const { currentTime } = e.detail;
      const currentCue = transcript.find(
        (cue) => currentTime >= cue.startTime && currentTime <= cue.endTime
      );
      if (currentCue && currentCue.id !== currentCueId) {
        setCurrentCueId(currentCue.id);
      }
    };

    window.addEventListener(
      "vod-time-update" as any,
      handleTimeUpdate as EventListener
    );
    return () =>
      window.removeEventListener(
        "vod-time-update" as any,
        handleTimeUpdate as EventListener
      );
  }, [transcript, currentCueId]);

  // Auto-scroll to active line
  useEffect(() => {
    if (activeLineRef.current && scrollAreaRef.current) {
      activeLineRef.current.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  }, [currentCueId]);

  // Seek to timestamp in video
  const seekToTime = (time: number) => {
    // Dispatch custom event to tell video player to seek
    window.dispatchEvent(
      new CustomEvent("vod-seek-to", { detail: { time } })
    );
  };

  // Download transcript
  const downloadTranscript = () => {
    const text = transcript.map((cue) => cue.text).join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `transcript-${sessionId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    toast({
      title: "Transcript Downloaded",
      description: "Transcript has been saved to your device",
    });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <CardTitle>Transcript</CardTitle>
            <CardDescription>
              Click on any line to jump to that moment
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {transcript.length > 0 && (
              <Button
                size="sm"
                variant="outline"
                onClick={downloadTranscript}
              >
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
            )}
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setIsOpen(!isOpen)}
            >
              {isOpen ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      {isOpen && (
        <CardContent>
          {/* Search */}
          <div className="mb-4 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="text"
              placeholder="Search transcript..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Transcript Content */}
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-gray-500">Loading transcript...</div>
            </div>
          ) : filteredTranscript.length === 0 ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-gray-500">
                {searchQuery
                  ? "No results found"
                  : "No transcript available"}
              </div>
            </div>
          ) : (
            <ScrollArea ref={scrollAreaRef} className="h-96">
              <div className="space-y-2">
                {filteredTranscript.map((cue) => (
                  <div
                    key={cue.id}
                    ref={cue.id === currentCueId ? activeLineRef : null}
                    className={cn(
                      "p-3 rounded-lg cursor-pointer transition-colors hover:bg-gray-100 dark:hover:bg-gray-800",
                      cue.id === currentCueId &&
                        "bg-blue-50 dark:bg-blue-950 border-l-4 border-blue-500"
                    )}
                    onClick={() => seekToTime(cue.startTime)}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-xs font-mono text-gray-500 dark:text-gray-400 min-w-[3rem]">
                        {formatTime(cue.startTime)}
                      </span>
                      <p
                        className={cn(
                          "text-sm flex-1",
                          cue.id === currentCueId
                            ? "font-medium text-blue-900 dark:text-blue-100"
                            : "text-gray-700 dark:text-gray-300"
                        )}
                      >
                        {cue.text}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}

          {/* Search Results Count */}
          {searchQuery && filteredTranscript.length > 0 && (
            <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Found {filteredTranscript.length} result
              {filteredTranscript.length !== 1 ? "s" : ""}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
