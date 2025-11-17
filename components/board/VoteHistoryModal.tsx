'use client';

import * as React from 'react';
import { boardApi } from '@/lib/api';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Clock, CheckCircle, XCircle, FileText, User, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VoteHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  applicationId: string;
}

interface Vote {
  id: string;
  approver_id: string;
  action: string;
  status: string;
  vote_cast_at: string;
  sequence: number;
  notes?: string;
}

interface VoteHistory {
  application_id: string;
  votes: Vote[];
  total_votes: number;
}

export function VoteHistoryModal({ isOpen, onClose, applicationId }: VoteHistoryModalProps) {
  const [voteHistory, setVoteHistory] = React.useState<VoteHistory | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (isOpen && applicationId) {
      fetchVoteHistory();
    }
  }, [isOpen, applicationId]);

  const fetchVoteHistory = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await boardApi.getVoteHistory(applicationId);
      setVoteHistory(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load vote history');
      console.error('Error fetching vote history:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string): string => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      // Relative time for recent votes
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
      if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
      if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

      // Absolute date for older votes
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  const getVoteBadge = (action: string) => {
    const isApproved = action === 'APPROVED' || action === 'APPROVE';

    return (
      <Badge
        className={cn(
          'font-semibold',
          isApproved
            ? 'bg-green-100 text-green-800 border-green-200 hover:bg-green-100'
            : 'bg-red-100 text-red-800 border-red-200 hover:bg-red-100'
        )}
      >
        {isApproved ? (
          <CheckCircle className="w-3 h-3 mr-1" />
        ) : (
          <XCircle className="w-3 h-3 mr-1" />
        )}
        {isApproved ? 'APPROVED' : 'REJECTED'}
      </Badge>
    );
  };

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <div className="w-12 h-12 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin" />
          <p className="text-sm text-gray-500">Loading vote history...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
            <AlertCircle className="w-6 h-6 text-red-600" />
          </div>
          <div className="text-center space-y-2">
            <p className="text-sm font-medium text-gray-900">Failed to load vote history</p>
            <p className="text-xs text-gray-500">{error}</p>
          </div>
          <button
            onClick={fetchVoteHistory}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      );
    }

    if (!voteHistory || voteHistory.votes.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center py-12 space-y-4">
          <div className="w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center">
            <FileText className="w-6 h-6 text-gray-400" />
          </div>
          <div className="text-center space-y-1">
            <p className="text-sm font-medium text-gray-900">No votes yet</p>
            <p className="text-xs text-gray-500">This application has not received any board votes.</p>
          </div>
        </div>
      );
    }

    // Sort votes chronologically (oldest first)
    const sortedVotes = [...voteHistory.votes].sort((a, b) => a.sequence - b.sequence);

    return (
      <ScrollArea className="h-[400px] pr-4">
        <div className="space-y-6">
          {sortedVotes.map((vote, index) => (
            <div key={vote.id} className="relative">
              {/* Timeline connector line */}
              {index < sortedVotes.length - 1 && (
                <div className="absolute left-5 top-12 w-0.5 h-[calc(100%+0.5rem)] bg-gray-200" />
              )}

              <div className="flex gap-4">
                {/* Timeline dot */}
                <div className="relative flex-shrink-0">
                  <div className={cn(
                    "w-10 h-10 rounded-full flex items-center justify-center border-2 bg-white z-10",
                    vote.action === 'APPROVED' || vote.action === 'APPROVE'
                      ? "border-green-500"
                      : "border-red-500"
                  )}>
                    <span className="text-sm font-semibold text-gray-700">
                      {vote.sequence}
                    </span>
                  </div>
                </div>

                {/* Vote content */}
                <div className="flex-1 min-w-0 pb-6">
                  <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
                    {/* Vote header */}
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div className="flex items-center gap-2 min-w-0">
                        <User className="w-4 h-4 text-gray-400 flex-shrink-0" />
                        <span className="text-sm font-medium text-gray-900 truncate">
                          Board Member {vote.approver_id.slice(0, 8)}
                        </span>
                      </div>
                      {getVoteBadge(vote.action)}
                    </div>

                    {/* Vote timestamp */}
                    <div className="flex items-center gap-2 text-xs text-gray-500 mb-3">
                      <Clock className="w-3 h-3" />
                      <time dateTime={vote.vote_cast_at}>
                        {formatDate(vote.vote_cast_at)}
                      </time>
                    </div>

                    {/* Vote notes */}
                    {vote.notes && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <div className="flex items-start gap-2">
                          <FileText className="w-3 h-3 text-gray-400 mt-0.5 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium text-gray-700 mb-1">Notes:</p>
                            <p className="text-sm text-gray-600 break-words whitespace-pre-wrap">
                              {vote.notes}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Vote status indicator (if different from action) */}
                    {vote.status && vote.status !== vote.action && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <span className="text-xs text-gray-500">
                          Status: <span className="font-medium">{vote.status}</span>
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle>Vote History</DialogTitle>
          <DialogDescription>
            {voteHistory && voteHistory.total_votes > 0
              ? `${voteHistory.total_votes} vote${voteHistory.total_votes > 1 ? 's' : ''} recorded for this application`
              : 'View all board member votes for this application'}
          </DialogDescription>
        </DialogHeader>

        <div className="mt-4">
          {renderContent()}
        </div>
      </DialogContent>
    </Dialog>
  );
}
