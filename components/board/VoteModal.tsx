'use client';

import * as React from 'react';
import { CheckCircle, XCircle, AlertCircle, Loader2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { cn } from '@/lib/utils';

interface VoteModalProps {
  isOpen: boolean;
  onClose: () => void;
  application: any;
  onVoteSubmit: (action: 'APPROVE' | 'REJECT', notes: string) => Promise<void>;
}

type VoteAction = 'APPROVE' | 'REJECT' | null;

export function VoteModal({
  isOpen,
  onClose,
  application,
  onVoteSubmit,
}: VoteModalProps) {
  const [selectedAction, setSelectedAction] = React.useState<VoteAction>(null);
  const [notes, setNotes] = React.useState('');
  const [isSubmitting, setIsSubmitting] = React.useState(false);
  const [showConfirmation, setShowConfirmation] = React.useState(false);

  // Reset state when modal closes
  React.useEffect(() => {
    if (!isOpen) {
      setSelectedAction(null);
      setNotes('');
      setIsSubmitting(false);
      setShowConfirmation(false);
    }
  }, [isOpen]);

  const handleActionSelect = (action: VoteAction) => {
    setSelectedAction(action);
    setShowConfirmation(false);
  };

  const handleCancel = () => {
    setSelectedAction(null);
    setNotes('');
    setShowConfirmation(false);
  };

  const handleConfirmClick = () => {
    setShowConfirmation(true);
  };

  const handleFinalSubmit = async () => {
    if (!selectedAction) return;

    try {
      setIsSubmitting(true);
      await onVoteSubmit(selectedAction, notes);
      onClose();
    } catch (error) {
      console.error('Error submitting vote:', error);
      setIsSubmitting(false);
      setShowConfirmation(false);
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const approvalCount = application?.approval_count || 0;
  const requiredApprovals = application?.required_approvals || 2;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold text-gray-900">
            Board Member Vote
          </DialogTitle>
          <DialogDescription className="text-gray-600">
            Review the application and cast your vote. Your decision will be
            recorded and cannot be changed.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Application Details */}
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-3">
            <h3 className="font-semibold text-gray-900 text-lg">
              Application Details
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <p className="text-sm text-gray-600">Applicant Name</p>
                <p className="font-medium text-gray-900">
                  {application?.applicant_name || 'N/A'}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-600">Email</p>
                <p className="font-medium text-gray-900 break-all">
                  {application?.applicant_email || 'N/A'}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-600">Submitted Date</p>
                <p className="font-medium text-gray-900">
                  {formatDate(application?.submitted_at || application?.created_at)}
                </p>
              </div>

              <div>
                <p className="text-sm text-gray-600">Approval Status</p>
                <p className="font-medium text-gray-900">
                  <span className="inline-flex items-center gap-1">
                    <span
                      className={cn(
                        'text-lg font-bold',
                        approvalCount >= requiredApprovals
                          ? 'text-green-600'
                          : 'text-amber-600'
                      )}
                    >
                      {approvalCount}/{requiredApprovals}
                    </span>
                    <span className="text-sm">approvals</span>
                  </span>
                </p>
              </div>
            </div>

            {application?.martial_arts_style && (
              <div>
                <p className="text-sm text-gray-600">Martial Arts Style</p>
                <p className="font-medium text-gray-900">
                  {application.martial_arts_style}
                </p>
              </div>
            )}

            {application?.years_experience && (
              <div>
                <p className="text-sm text-gray-600">Years of Experience</p>
                <p className="font-medium text-gray-900">
                  {application.years_experience} years
                </p>
              </div>
            )}

            {application?.reason_for_joining && (
              <div>
                <p className="text-sm text-gray-600">Reason for Joining</p>
                <p className="font-medium text-gray-900 text-sm">
                  {application.reason_for_joining}
                </p>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          {!selectedAction && (
            <div className="space-y-3">
              <p className="text-sm font-medium text-gray-700">
                Cast your vote:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Button
                  onClick={() => handleActionSelect('APPROVE')}
                  size="lg"
                  className="h-20 bg-green-600 hover:bg-green-700 text-white font-semibold text-lg shadow-md hover:shadow-lg transition-all duration-200"
                >
                  <CheckCircle className="mr-2 h-6 w-6" />
                  Approve Application
                </Button>

                <Button
                  onClick={() => handleActionSelect('REJECT')}
                  size="lg"
                  variant="destructive"
                  className="h-20 bg-red-600 hover:bg-red-700 text-white font-semibold text-lg shadow-md hover:shadow-lg transition-all duration-200"
                >
                  <XCircle className="mr-2 h-6 w-6" />
                  Reject Application
                </Button>
              </div>
            </div>
          )}

          {/* Notes Section (shown after action selection) */}
          {selectedAction && !showConfirmation && (
            <div className="space-y-4 animate-in fade-in-50 duration-300">
              <div
                className={cn(
                  'p-4 rounded-lg border-l-4',
                  selectedAction === 'APPROVE'
                    ? 'bg-green-50 border-green-600'
                    : 'bg-red-50 border-red-600'
                )}
              >
                <p className="font-semibold text-gray-900 flex items-center gap-2">
                  {selectedAction === 'APPROVE' ? (
                    <CheckCircle className="h-5 w-5 text-green-600" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-600" />
                  )}
                  You selected: {selectedAction === 'APPROVE' ? 'Approve' : 'Reject'}
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="notes" className="text-gray-900">
                  Notes {selectedAction === 'REJECT' ? '(Required)' : '(Optional)'}
                </Label>
                <Textarea
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder={
                    selectedAction === 'APPROVE'
                      ? 'Add any comments or observations about this application...'
                      : 'Please provide a reason for rejection. This will help the applicant understand the decision.'
                  }
                  className="min-h-[120px] resize-none"
                  disabled={isSubmitting}
                  required={selectedAction === 'REJECT'}
                />
                {selectedAction === 'REJECT' && !notes.trim() && (
                  <p className="text-sm text-red-600">
                    Notes are required when rejecting an application
                  </p>
                )}
              </div>

              <div className="flex flex-col-reverse sm:flex-row gap-3 pt-2">
                <Button
                  onClick={handleCancel}
                  variant="outline"
                  className="sm:flex-1"
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleConfirmClick}
                  className={cn(
                    'sm:flex-1 font-semibold',
                    selectedAction === 'APPROVE'
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-red-600 hover:bg-red-700'
                  )}
                  disabled={
                    isSubmitting ||
                    (selectedAction === 'REJECT' && !notes.trim())
                  }
                >
                  Confirm Vote
                </Button>
              </div>
            </div>
          )}

          {/* Confirmation Message */}
          {showConfirmation && selectedAction && (
            <div className="space-y-4 animate-in fade-in-50 duration-300">
              <div className="p-4 rounded-lg border border-amber-200 bg-amber-50">
                <div className="flex items-start gap-3">
                  <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                  <div className="space-y-2">
                    <p className="font-semibold text-amber-900">
                      Confirm Your Vote
                    </p>
                    <p className="text-sm text-amber-800">
                      You are about to{' '}
                      <span className="font-bold">
                        {selectedAction === 'APPROVE' ? 'APPROVE' : 'REJECT'}
                      </span>{' '}
                      the application for{' '}
                      <span className="font-semibold">
                        {application?.applicant_name}
                      </span>
                      . This action cannot be undone.
                    </p>
                    {notes.trim() && (
                      <div className="mt-3 pt-3 border-t border-amber-200">
                        <p className="text-sm font-medium text-amber-900">
                          Your notes:
                        </p>
                        <p className="text-sm text-amber-800 mt-1 italic">
                          "{notes}"
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex flex-col-reverse sm:flex-row gap-3">
                <Button
                  onClick={() => setShowConfirmation(false)}
                  variant="outline"
                  className="sm:flex-1"
                  disabled={isSubmitting}
                >
                  Go Back
                </Button>
                <Button
                  onClick={handleFinalSubmit}
                  className={cn(
                    'sm:flex-1 font-semibold',
                    selectedAction === 'APPROVE'
                      ? 'bg-green-600 hover:bg-green-700'
                      : 'bg-red-600 hover:bg-red-700'
                  )}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Submitting...
                    </>
                  ) : (
                    <>
                      Submit {selectedAction === 'APPROVE' ? 'Approval' : 'Rejection'}
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
