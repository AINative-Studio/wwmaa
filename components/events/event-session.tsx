"use client";

import { useState, useEffect } from "react";
import { Video, Clock, Lock, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";

interface EventSessionProps {
  eventId: string;
  sessionId: string;
  sessionTitle: string;
  startDatetime: string;
  endDatetime: string;
  isVirtual: boolean;
  requiresPayment: boolean;
  registrationFee?: number;
  currentUserStatus: {
    isAuthenticated: boolean;
    hasPaid: boolean;
    hasAcceptedTerms: boolean;
  };
}

export function EventSession({
  eventId,
  sessionId,
  sessionTitle,
  startDatetime,
  endDatetime,
  isVirtual,
  requiresPayment,
  registrationFee,
  currentUserStatus,
}: EventSessionProps) {
  const [timeUntilStart, setTimeUntilStart] = useState<number>(0);
  const [isJoinEnabled, setIsJoinEnabled] = useState(false);
  const [showTermsDialog, setShowTermsDialog] = useState(false);
  const [hasAcceptedTerms, setHasAcceptedTerms] = useState(
    currentUserStatus.hasAcceptedTerms
  );
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const calculateTimeUntilStart = () => {
      const now = new Date().getTime();
      const start = new Date(startDatetime).getTime();
      const diff = start - now;
      setTimeUntilStart(diff);

      // Enable join button 10 minutes before start (10 * 60 * 1000 ms)
      const tenMinutes = 10 * 60 * 1000;
      setIsJoinEnabled(diff <= tenMinutes && diff > 0);
    };

    calculateTimeUntilStart();
    const interval = setInterval(calculateTimeUntilStart, 1000);

    return () => clearInterval(interval);
  }, [startDatetime]);

  const formatCountdown = (ms: number): string => {
    if (ms <= 0) return "Session Started";

    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) {
      return `${days}d ${hours % 24}h ${minutes % 60}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    } else {
      return `${seconds}s`;
    }
  };

  const handleJoinClick = () => {
    // Check authentication
    if (!currentUserStatus.isAuthenticated) {
      window.location.href = `/login?redirect=/training/${sessionId}/live`;
      return;
    }

    // Check payment
    if (requiresPayment && !currentUserStatus.hasPaid) {
      window.location.href = `/checkout?eventId=${eventId}`;
      return;
    }

    // Check terms acceptance
    if (!hasAcceptedTerms) {
      setShowTermsDialog(true);
      return;
    }

    // All checks passed, join session
    window.location.href = `/training/${sessionId}/live`;
  };

  const handleAcceptTerms = async () => {
    setIsLoading(true);
    try {
      // Call API to save terms acceptance
      const response = await fetch(`/api/training/${sessionId}/accept-terms`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to accept terms");
      }

      setHasAcceptedTerms(true);
      setShowTermsDialog(false);
      // Now join the session
      window.location.href = `/training/${sessionId}/live`;
    } catch (error) {
      console.error("Error accepting terms:", error);
      alert("Failed to accept terms. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const canJoin =
    isJoinEnabled &&
    currentUserStatus.isAuthenticated &&
    (!requiresPayment || currentUserStatus.hasPaid);

  return (
    <>
      <Card className="border-dojo-green/20 bg-gradient-to-br from-dojo-green/5 to-transparent">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Video className="h-5 w-5 text-dojo-green" />
            Live Training Session
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h3 className="font-semibold text-lg">{sessionTitle}</h3>
            <p className="text-sm text-gray-600">
              {new Date(startDatetime).toLocaleString("en-US", {
                weekday: "long",
                month: "long",
                day: "numeric",
                hour: "numeric",
                minute: "2-digit",
                timeZoneName: "short",
              })}
            </p>
          </div>

          {/* Countdown Timer */}
          {timeUntilStart > 0 && (
            <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
              <Clock className="h-5 w-5 text-gray-600" />
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {isJoinEnabled ? "Joining Available" : "Starts in"}
                </p>
                <p className="text-lg font-bold text-dojo-green">
                  {formatCountdown(timeUntilStart)}
                </p>
              </div>
            </div>
          )}

          {/* Status Indicators */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              {currentUserStatus.isAuthenticated ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <Lock className="h-4 w-4 text-gray-400" />
              )}
              <span className="text-sm text-gray-700">
                {currentUserStatus.isAuthenticated
                  ? "Authenticated"
                  : "Login Required"}
              </span>
            </div>

            {requiresPayment && (
              <div className="flex items-center gap-2">
                {currentUserStatus.hasPaid ? (
                  <CheckCircle className="h-4 w-4 text-green-600" />
                ) : (
                  <Lock className="h-4 w-4 text-gray-400" />
                )}
                <span className="text-sm text-gray-700">
                  {currentUserStatus.hasPaid
                    ? `Payment Confirmed ($${registrationFee?.toFixed(2)})`
                    : `Payment Required ($${registrationFee?.toFixed(2)})`}
                </span>
              </div>
            )}

            <div className="flex items-center gap-2">
              {hasAcceptedTerms ? (
                <CheckCircle className="h-4 w-4 text-green-600" />
              ) : (
                <Lock className="h-4 w-4 text-gray-400" />
              )}
              <span className="text-sm text-gray-700">
                {hasAcceptedTerms ? "Terms Accepted" : "Terms Acceptance Required"}
              </span>
            </div>
          </div>

          {/* Join Button */}
          <Button
            onClick={handleJoinClick}
            disabled={!canJoin && timeUntilStart > 0}
            className="w-full"
            size="lg"
          >
            <Video className="h-4 w-4 mr-2" />
            {!currentUserStatus.isAuthenticated
              ? "Login to Join"
              : requiresPayment && !currentUserStatus.hasPaid
              ? "Complete Payment"
              : !isJoinEnabled && timeUntilStart > 0
              ? `Available in ${formatCountdown(timeUntilStart)}`
              : "Join Session"}
          </Button>

          {isJoinEnabled && (
            <p className="text-xs text-center text-gray-600">
              Session joining is now available. Click above to enter the live training.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Terms Acceptance Dialog */}
      <Dialog open={showTermsDialog} onOpenChange={setShowTermsDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Terms and Conditions</DialogTitle>
            <DialogDescription>
              Please review and accept the terms before joining the live session.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="max-h-64 overflow-y-auto border rounded-lg p-4 text-sm">
              <h4 className="font-semibold mb-2">Live Session Participation Terms</h4>
              <ul className="space-y-2 list-disc pl-5">
                <li>
                  You agree to participate respectfully and follow instructor
                  guidance.
                </li>
                <li>
                  Sessions may be recorded for educational purposes. By joining,
                  you consent to being recorded.
                </li>
                <li>
                  Keep your microphone muted unless speaking to minimize
                  background noise.
                </li>
                <li>
                  Use the chat feature appropriately and respectfully.
                </li>
                <li>
                  Do not share session links or access credentials with others.
                </li>
                <li>
                  The organization reserves the right to remove disruptive
                  participants.
                </li>
                <li>
                  Technical issues should be reported via the chat or support
                  channels.
                </li>
                <li>
                  You are responsible for having a stable internet connection and
                  proper equipment.
                </li>
              </ul>
            </div>

            <div className="flex items-start gap-2">
              <Checkbox
                id="accept-terms"
                checked={hasAcceptedTerms}
                onCheckedChange={(checked) =>
                  setHasAcceptedTerms(checked as boolean)
                }
              />
              <label
                htmlFor="accept-terms"
                className="text-sm text-gray-700 cursor-pointer"
              >
                I have read and accept the terms and conditions for participating
                in this live training session.
              </label>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowTermsDialog(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAcceptTerms}
              disabled={!hasAcceptedTerms || isLoading}
            >
              {isLoading ? "Accepting..." : "Accept & Join Session"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
