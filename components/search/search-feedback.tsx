'use client';

import { useState } from 'react';
import { ThumbsUp, ThumbsDown, Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';

interface SearchFeedbackProps {
  resultId: string;
}

export function SearchFeedback({ resultId }: SearchFeedbackProps) {
  const [feedback, setFeedback] = useState<boolean | null>(null);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [hasSubmitted, setHasSubmitted] = useState(false);
  const { toast } = useToast();

  const handleFeedback = async (helpful: boolean) => {
    setFeedback(helpful);

    // If the user clicked the same feedback again, remove it
    if (feedback === helpful) {
      setFeedback(null);
      return;
    }
  };

  const handleSubmit = async () => {
    if (feedback === null) {
      toast({
        title: 'Please select feedback',
        description: 'Let us know if this answer was helpful',
        variant: 'destructive',
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/search/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resultId,
          helpful: feedback,
          comment: comment.trim() || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to submit feedback');
      }

      setHasSubmitted(true);
      toast({
        title: 'Thank you for your feedback!',
        description: 'Your feedback helps us improve our search results.',
      });
    } catch (error) {
      console.error('Feedback submission error:', error);
      toast({
        title: 'Failed to submit feedback',
        description: 'Please try again later.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (hasSubmitted) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4">
              <ThumbsUp className="h-8 w-8 text-primary" />
            </div>
            <p className="text-lg font-semibold mb-2">Thank you for your feedback!</p>
            <p className="text-sm text-muted-foreground">
              Your input helps us improve our search results.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Was this helpful?</CardTitle>
        <CardDescription>
          Your feedback helps us improve search results
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Feedback Buttons */}
          <div className="flex gap-4">
            <Button
              variant={feedback === true ? 'default' : 'outline'}
              size="lg"
              onClick={() => handleFeedback(true)}
              className={cn(
                'flex-1',
                feedback === true && 'bg-green-600 hover:bg-green-700'
              )}
            >
              <ThumbsUp className="h-5 w-5 mr-2" />
              Yes, helpful
            </Button>
            <Button
              variant={feedback === false ? 'default' : 'outline'}
              size="lg"
              onClick={() => handleFeedback(false)}
              className={cn(
                'flex-1',
                feedback === false && 'bg-red-600 hover:bg-red-700'
              )}
            >
              <ThumbsDown className="h-5 w-5 mr-2" />
              No, not helpful
            </Button>
          </div>

          {/* Optional Comment */}
          {feedback !== null && (
            <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
              <label htmlFor="feedback-comment" className="text-sm font-medium">
                Additional feedback (optional)
              </label>
              <Textarea
                id="feedback-comment"
                placeholder="Tell us more about your experience..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={3}
                className="resize-none"
              />
            </div>
          )}

          {/* Submit Button */}
          {feedback !== null && (
            <Button
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="w-full"
            >
              {isSubmitting ? (
                <>
                  <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
                  Submitting...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Submit Feedback
                </>
              )}
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
