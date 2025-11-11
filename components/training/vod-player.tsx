"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  Minimize,
  Settings,
  PictureInPicture,
  SkipBack,
  SkipForward,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/use-toast";

interface VODPlayerProps {
  sessionId: string;
  streamUrl: string;
  title: string;
  duration?: number;
  thumbnailUrl?: string;
  initialPosition?: number;
  userId: string;
}

interface PlayerState {
  playing: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  muted: boolean;
  playbackRate: number;
  quality: string;
  buffering: boolean;
  fullscreen: boolean;
}

const PLAYBACK_RATES = [0.5, 0.75, 1, 1.25, 1.5, 2];
const QUALITY_OPTIONS = ["auto", "1080p", "720p", "480p", "360p"];
const PROGRESS_SAVE_INTERVAL = 10000; // Save every 10 seconds

export function VODPlayer({
  sessionId,
  streamUrl,
  title,
  duration: initialDuration,
  thumbnailUrl,
  initialPosition = 0,
  userId,
}: VODPlayerProps) {
  const { toast } = useToast();
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const progressTimerRef = useRef<NodeJS.Timeout>();
  const lastSavedPositionRef = useRef<number>(0);
  const controlsTimeoutRef = useRef<NodeJS.Timeout>();

  const [state, setState] = useState<PlayerState>({
    playing: false,
    currentTime: initialPosition,
    duration: initialDuration || 0,
    volume: 1,
    muted: false,
    playbackRate: 1,
    quality: "auto",
    buffering: false,
    fullscreen: false,
  });

  const [showControls, setShowControls] = useState(true);
  const [seeking, setSeeking] = useState(false);
  const [hoveredTime, setHoveredTime] = useState<number | null>(null);

  // Save watch progress to backend
  const saveProgress = useCallback(
    async (position: number, force = false) => {
      // Only save if position has changed significantly or forced
      if (!force && Math.abs(position - lastSavedPositionRef.current) < 5) {
        return;
      }

      try {
        const response = await fetch(
          `/api/training/${sessionId}/progress`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              userId,
              lastWatchedPosition: Math.floor(position),
              totalWatchTime: Math.floor(position),
              completed: state.duration > 0 && position >= state.duration * 0.9,
            }),
          }
        );

        if (response.ok) {
          lastSavedPositionRef.current = position;
        }
      } catch (error) {
        console.error("Error saving progress:", error);
      }
    },
    [sessionId, userId, state.duration]
  );

  // Format time as MM:SS or HH:MM:SS
  const formatTime = (seconds: number): string => {
    if (isNaN(seconds)) return "0:00";
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    if (h > 0) {
      return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
    }
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  // Play/Pause toggle
  const togglePlay = useCallback(() => {
    if (!videoRef.current) return;

    if (state.playing) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
  }, [state.playing]);

  // Seek to position
  const seekTo = useCallback((time: number) => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = time;
  }, []);

  // Skip forward/backward
  const skip = useCallback(
    (seconds: number) => {
      if (!videoRef.current) return;
      const newTime = Math.max(
        0,
        Math.min(state.duration, state.currentTime + seconds)
      );
      seekTo(newTime);
    },
    [state.currentTime, state.duration, seekTo]
  );

  // Toggle mute
  const toggleMute = useCallback(() => {
    if (!videoRef.current) return;
    videoRef.current.muted = !state.muted;
    setState((prev) => ({ ...prev, muted: !prev.muted }));
  }, [state.muted]);

  // Set volume
  const setVolume = useCallback((value: number[]) => {
    if (!videoRef.current) return;
    const volume = value[0];
    videoRef.current.volume = volume;
    videoRef.current.muted = volume === 0;
    setState((prev) => ({ ...prev, volume, muted: volume === 0 }));
  }, []);

  // Set playback rate
  const setPlaybackRate = useCallback((rate: string) => {
    if (!videoRef.current) return;
    const rateNum = parseFloat(rate);
    videoRef.current.playbackRate = rateNum;
    setState((prev) => ({ ...prev, playbackRate: rateNum }));
  }, []);

  // Toggle fullscreen
  const toggleFullscreen = useCallback(async () => {
    if (!containerRef.current) return;

    try {
      if (!document.fullscreenElement) {
        await containerRef.current.requestFullscreen();
        setState((prev) => ({ ...prev, fullscreen: true }));
      } else {
        await document.exitFullscreen();
        setState((prev) => ({ ...prev, fullscreen: false }));
      }
    } catch (error) {
      console.error("Fullscreen error:", error);
      toast({
        title: "Fullscreen Error",
        description: "Unable to toggle fullscreen mode",
        variant: "destructive",
      });
    }
  }, [toast]);

  // Toggle Picture-in-Picture
  const togglePiP = useCallback(async () => {
    if (!videoRef.current) return;

    try {
      if (document.pictureInPictureElement) {
        await document.exitPictureInPicture();
      } else {
        await videoRef.current.requestPictureInPicture();
      }
    } catch (error) {
      console.error("PiP error:", error);
      toast({
        title: "Picture-in-Picture Error",
        description: "Unable to toggle picture-in-picture mode",
        variant: "destructive",
      });
    }
  }, [toast]);

  // Jump to percentage
  const jumpToPercent = useCallback(
    (percent: number) => {
      if (!videoRef.current || state.duration === 0) return;
      const time = (state.duration * percent) / 100;
      seekTo(time);
    },
    [state.duration, seekTo]
  );

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't handle if user is typing in an input
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      switch (e.key) {
        case " ":
        case "k":
          e.preventDefault();
          togglePlay();
          break;
        case "f":
          e.preventDefault();
          toggleFullscreen();
          break;
        case "m":
          e.preventDefault();
          toggleMute();
          break;
        case "ArrowLeft":
        case "j":
          e.preventDefault();
          skip(-10);
          break;
        case "ArrowRight":
        case "l":
          e.preventDefault();
          skip(10);
          break;
        case "ArrowUp":
          e.preventDefault();
          setVolume([Math.min(1, state.volume + 0.1)]);
          break;
        case "ArrowDown":
          e.preventDefault();
          setVolume([Math.max(0, state.volume - 0.1)]);
          break;
        case "0":
        case "1":
        case "2":
        case "3":
        case "4":
        case "5":
        case "6":
        case "7":
        case "8":
        case "9":
          e.preventDefault();
          jumpToPercent(parseInt(e.key) * 10);
          break;
        default:
          break;
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
    togglePlay,
    toggleFullscreen,
    toggleMute,
    skip,
    setVolume,
    jumpToPercent,
    state.volume,
  ]);

  // Video event handlers
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handlePlay = () => setState((prev) => ({ ...prev, playing: true }));
    const handlePause = () => setState((prev) => ({ ...prev, playing: false }));
    const handleTimeUpdate = () => {
      setState((prev) => ({ ...prev, currentTime: video.currentTime }));
    };
    const handleDurationChange = () => {
      setState((prev) => ({ ...prev, duration: video.duration }));
    };
    const handleWaiting = () => setState((prev) => ({ ...prev, buffering: true }));
    const handleCanPlay = () => setState((prev) => ({ ...prev, buffering: false }));
    const handleVolumeChange = () => {
      setState((prev) => ({
        ...prev,
        volume: video.volume,
        muted: video.muted,
      }));
    };

    video.addEventListener("play", handlePlay);
    video.addEventListener("pause", handlePause);
    video.addEventListener("timeupdate", handleTimeUpdate);
    video.addEventListener("durationchange", handleDurationChange);
    video.addEventListener("waiting", handleWaiting);
    video.addEventListener("canplay", handleCanPlay);
    video.addEventListener("volumechange", handleVolumeChange);

    return () => {
      video.removeEventListener("play", handlePlay);
      video.removeEventListener("pause", handlePause);
      video.removeEventListener("timeupdate", handleTimeUpdate);
      video.removeEventListener("durationchange", handleDurationChange);
      video.removeEventListener("waiting", handleWaiting);
      video.removeEventListener("canplay", handleCanPlay);
      video.removeEventListener("volumechange", handleVolumeChange);
    };
  }, []);

  // Fullscreen change handler
  useEffect(() => {
    const handleFullscreenChange = () => {
      setState((prev) => ({
        ...prev,
        fullscreen: !!document.fullscreenElement,
      }));
    };

    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () =>
      document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, []);

  // Auto-hide controls
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleMouseMove = () => {
      setShowControls(true);
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
      if (state.playing) {
        controlsTimeoutRef.current = setTimeout(() => {
          setShowControls(false);
        }, 3000);
      }
    };

    const handleMouseLeave = () => {
      if (state.playing) {
        setShowControls(false);
      }
    };

    container.addEventListener("mousemove", handleMouseMove);
    container.addEventListener("mouseleave", handleMouseLeave);

    return () => {
      container.removeEventListener("mousemove", handleMouseMove);
      container.removeEventListener("mouseleave", handleMouseLeave);
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
    };
  }, [state.playing]);

  // Progress save interval
  useEffect(() => {
    if (state.playing) {
      progressTimerRef.current = setInterval(() => {
        saveProgress(state.currentTime);
      }, PROGRESS_SAVE_INTERVAL);
    } else {
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current);
      }
    }

    return () => {
      if (progressTimerRef.current) {
        clearInterval(progressTimerRef.current);
      }
    };
  }, [state.playing, state.currentTime, saveProgress]);

  // Save progress on unmount
  useEffect(() => {
    return () => {
      if (state.currentTime > 0) {
        saveProgress(state.currentTime, true);
      }
    };
  }, [state.currentTime, saveProgress]);

  // Resume from initial position
  useEffect(() => {
    if (initialPosition > 0 && videoRef.current && state.duration > 0) {
      seekTo(initialPosition);
    }
  }, [initialPosition, state.duration, seekTo]);

  return (
    <div
      ref={containerRef}
      className={cn(
        "relative bg-black rounded-lg overflow-hidden aspect-video group",
        state.fullscreen && "aspect-auto h-screen w-screen"
      )}
    >
      {/* Video Element */}
      <video
        ref={videoRef}
        className="w-full h-full"
        poster={thumbnailUrl}
        onClick={togglePlay}
        playsInline
      >
        <source src={streamUrl} type="video/mp4" />
        Your browser does not support the video tag.
      </video>

      {/* Loading Spinner */}
      {state.buffering && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/50">
          <Loader2 className="h-12 w-12 animate-spin text-white" />
        </div>
      )}

      {/* Controls Overlay */}
      <div
        className={cn(
          "absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent transition-opacity duration-300",
          showControls || !state.playing ? "opacity-100" : "opacity-0"
        )}
      >
        {/* Center Play Button */}
        {!state.playing && !state.buffering && (
          <div className="absolute inset-0 flex items-center justify-center">
            <Button
              size="lg"
              variant="ghost"
              className="h-20 w-20 rounded-full bg-white/20 hover:bg-white/30 backdrop-blur-sm"
              onClick={togglePlay}
            >
              <Play className="h-10 w-10 text-white fill-white" />
            </Button>
          </div>
        )}

        {/* Bottom Controls */}
        <div className="absolute bottom-0 left-0 right-0 p-4 space-y-2">
          {/* Progress Bar */}
          <div className="relative group/progress">
            <Slider
              value={[state.currentTime]}
              max={state.duration || 100}
              step={0.1}
              onValueChange={(value) => {
                setSeeking(true);
                setState((prev) => ({ ...prev, currentTime: value[0] }));
              }}
              onValueCommit={(value) => {
                seekTo(value[0]);
                setSeeking(false);
              }}
              className="cursor-pointer"
              onMouseMove={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                const percent = (e.clientX - rect.left) / rect.width;
                setHoveredTime(percent * state.duration);
              }}
              onMouseLeave={() => setHoveredTime(null)}
            />
            {/* Time tooltip on hover */}
            {hoveredTime !== null && (
              <div
                className="absolute bottom-full mb-2 px-2 py-1 bg-black/90 text-white text-xs rounded pointer-events-none"
                style={{
                  left: `${(hoveredTime / state.duration) * 100}%`,
                  transform: "translateX(-50%)",
                }}
              >
                {formatTime(hoveredTime)}
              </div>
            )}
          </div>

          {/* Control Buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {/* Play/Pause */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-white hover:bg-white/20"
                      onClick={togglePlay}
                    >
                      {state.playing ? (
                        <Pause className="h-5 w-5" />
                      ) : (
                        <Play className="h-5 w-5" />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>{state.playing ? "Pause (Space)" : "Play (Space)"}</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              {/* Skip Back */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-white hover:bg-white/20"
                      onClick={() => skip(-10)}
                    >
                      <SkipBack className="h-5 w-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Back 10s (← or J)</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              {/* Skip Forward */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-white hover:bg-white/20"
                      onClick={() => skip(10)}
                    >
                      <SkipForward className="h-5 w-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Forward 10s (→ or L)</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              {/* Volume */}
              <div className="flex items-center gap-2">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-white hover:bg-white/20"
                        onClick={toggleMute}
                      >
                        {state.muted || state.volume === 0 ? (
                          <VolumeX className="h-5 w-5" />
                        ) : (
                          <Volume2 className="h-5 w-5" />
                        )}
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Mute (M)</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                <Slider
                  value={[state.muted ? 0 : state.volume]}
                  max={1}
                  step={0.01}
                  onValueChange={setVolume}
                  className="w-20 cursor-pointer"
                />
              </div>

              {/* Time Display */}
              <span className="text-white text-sm font-medium">
                {formatTime(state.currentTime)} / {formatTime(state.duration)}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {/* Playback Speed */}
              <Select
                value={state.playbackRate.toString()}
                onValueChange={setPlaybackRate}
              >
                <SelectTrigger className="w-20 h-8 bg-white/20 text-white border-none hover:bg-white/30">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PLAYBACK_RATES.map((rate) => (
                    <SelectItem key={rate} value={rate.toString()}>
                      {rate}x
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Quality Selector */}
              <Select value={state.quality} onValueChange={(value) => setState((prev) => ({ ...prev, quality: value }))}>
                <SelectTrigger className="w-24 h-8 bg-white/20 text-white border-none hover:bg-white/30">
                  <Settings className="h-4 w-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {QUALITY_OPTIONS.map((quality) => (
                    <SelectItem key={quality} value={quality}>
                      {quality}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Picture-in-Picture */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-white hover:bg-white/20"
                      onClick={togglePiP}
                    >
                      <PictureInPicture className="h-5 w-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Picture-in-Picture</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              {/* Fullscreen */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-white hover:bg-white/20"
                      onClick={toggleFullscreen}
                    >
                      {state.fullscreen ? (
                        <Minimize className="h-5 w-5" />
                      ) : (
                        <Maximize className="h-5 w-5" />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Fullscreen (F)</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
