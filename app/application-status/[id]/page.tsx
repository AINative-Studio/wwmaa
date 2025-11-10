'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  CardFooter,
} from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { StatusBadge } from '@/components/application/status-badge';
import { Timeline } from '@/components/application/timeline';
import { applicationApi } from '@/lib/application-api';
import {
  MembershipApplication,
  ApplicationApproval,
  ApplicationTimeline,
} from '@/lib/types';
import {
  AlertCircle,
  CheckCircle2,
  Download,
  Edit,
  RefreshCw,
  Send,
  Loader2,
} from 'lucide-react';

export default function ApplicationStatusPage() {
  const params = useParams();
  const router = useRouter();
  const applicationId = params.id as string;

  const [application, setApplication] = useState<MembershipApplication | null>(null);
  const [approvals, setApprovals] = useState<ApplicationApproval[]>([]);
  const [timeline, setTimeline] = useState<ApplicationTimeline[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchApplicationData = async () => {
      try {
        setLoading(true);
        setError(null);

        const [appData, approvalsData, timelineData] = await Promise.all([
          applicationApi.getApplicationById(applicationId),
          applicationApi.getApplicationApprovals(applicationId),
          applicationApi.getApplicationTimeline(applicationId),
        ]);

        if (!appData) {
          setError('Application not found');
          return;
        }

        setApplication(appData);
        setApprovals(approvalsData);
        setTimeline(timelineData);
      } catch (err) {
        setError('Failed to load application details');
        console.error('Error loading application:', err);
      } finally {
        setLoading(false);
      }
    };

    if (applicationId) {
      fetchApplicationData();
    }
  }, [applicationId]);

  const getApprovalProgress = () => {
    if (!application) return 0;
    return (application.approval_count / application.required_approvals) * 100;
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Intl.DateTimeFormat('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    }).format(new Date(dateString));
  };

  const canEdit = application?.status === 'DRAFT';
  const canSubmit = application?.status === 'DRAFT';
  const canReapply = application?.status === 'REJECTED' && application?.can_reapply;
  const isApproved = application?.status === 'APPROVED';

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            <span className="ml-3 text-gray-600">Loading application...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error || !application) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
              {error || 'Application not found'}
            </AlertDescription>
          </Alert>
          <div className="mt-6">
            <Button onClick={() => router.push('/application-status')}>
              Back to Status Lookup
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-3xl font-bold text-gray-900">
              Membership Application
            </h1>
            <StatusBadge status={application.status} />
          </div>
          <p className="text-gray-600">
            Application ID: <span className="font-mono font-semibold">{application.id}</span>
          </p>
        </div>

        {/* Rejection Alert */}
        {application.status === 'REJECTED' && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Application Rejected</AlertTitle>
            <AlertDescription>
              {application.rejection_reason || 'Your application was not approved at this time.'}
              {canReapply && application.reapply_after && (
                <p className="mt-2">
                  You may reapply after {formatDate(application.reapply_after)}.
                </p>
              )}
            </AlertDescription>
          </Alert>
        )}

        {/* Approval Alert */}
        {application.status === 'APPROVED' && (
          <Alert className="mb-6 bg-green-50 border-green-200">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertTitle className="text-green-900">Application Approved!</AlertTitle>
            <AlertDescription className="text-green-800">
              Congratulations! Your membership application has been approved. You will receive
              onboarding instructions via email shortly.
            </AlertDescription>
          </Alert>
        )}

        {/* Approval Progress */}
        {(application.status === 'SUBMITTED' || application.status === 'UNDER_REVIEW') && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Approval Progress</CardTitle>
              <CardDescription>
                Your application requires {application.required_approvals} board member approvals
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">
                    {application.approval_count} of {application.required_approvals} approvals
                  </span>
                  <span className="text-gray-500">
                    {Math.round(getApprovalProgress())}%
                  </span>
                </div>
                <Progress value={getApprovalProgress()} className="h-3" />
                {application.approved_by && application.approved_by.length > 0 && (
                  <div className="pt-2">
                    <p className="text-sm font-medium text-gray-700 mb-2">Approved by:</p>
                    <ul className="space-y-1">
                      {application.approved_by.map((name, index) => (
                        <li key={index} className="text-sm text-gray-600 flex items-center gap-2">
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                          {name}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Personal Information */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Personal Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Name</label>
                <p className="text-gray-900">{application.applicant_name}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Email</label>
                <p className="text-gray-900">{application.applicant_email}</p>
              </div>
              {application.applicant_phone && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Phone</label>
                  <p className="text-gray-900">{application.applicant_phone}</p>
                </div>
              )}
              {application.applicant_address && (
                <div className="md:col-span-2">
                  <label className="text-sm font-medium text-gray-700">Address</label>
                  <p className="text-gray-900">{application.applicant_address}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Martial Arts Background */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Martial Arts Background</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Martial Arts Style</label>
                <p className="text-gray-900">{application.martial_arts_style}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700">Years of Experience</label>
                <p className="text-gray-900">{application.years_experience} years</p>
              </div>
              {application.current_rank && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Current Rank</label>
                  <p className="text-gray-900">{application.current_rank}</p>
                </div>
              )}
              {application.instructor_name && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Instructor</label>
                  <p className="text-gray-900">{application.instructor_name}</p>
                </div>
              )}
              {application.school_affiliation && (
                <div className="md:col-span-2">
                  <label className="text-sm font-medium text-gray-700">School Affiliation</label>
                  <p className="text-gray-900">{application.school_affiliation}</p>
                </div>
              )}
            </div>
            <Separator />
            <div>
              <label className="text-sm font-medium text-gray-700">Reason for Joining</label>
              <p className="text-gray-900 mt-1">{application.reason_for_joining}</p>
            </div>
          </CardContent>
        </Card>

        {/* Application Timeline */}
        {timeline.length > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Application Timeline</CardTitle>
              <CardDescription>Track your application progress</CardDescription>
            </CardHeader>
            <CardContent>
              <Timeline events={timeline} />
            </CardContent>
          </Card>
        )}

        {/* Important Dates */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Important Dates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700">Submitted</label>
                <p className="text-gray-900">{formatDate(application.submitted_at)}</p>
              </div>
              {application.first_approval_at && (
                <div>
                  <label className="text-sm font-medium text-gray-700">First Approval</label>
                  <p className="text-gray-900">{formatDate(application.first_approval_at)}</p>
                </div>
              )}
              {application.approved_at && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Approved</label>
                  <p className="text-gray-900">{formatDate(application.approved_at)}</p>
                </div>
              )}
              {application.rejected_at && (
                <div>
                  <label className="text-sm font-medium text-gray-700">Rejected</label>
                  <p className="text-gray-900">{formatDate(application.rejected_at)}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <Card>
          <CardFooter className="flex gap-3 pt-6">
            {canEdit && (
              <Button variant="outline" className="flex items-center gap-2">
                <Edit className="h-4 w-4" />
                Edit Application
              </Button>
            )}
            {canSubmit && (
              <Button className="flex items-center gap-2">
                <Send className="h-4 w-4" />
                Submit Application
              </Button>
            )}
            {canReapply && (
              <Button className="flex items-center gap-2">
                <RefreshCw className="h-4 w-4" />
                Reapply
              </Button>
            )}
            {isApproved && (
              <Button className="flex items-center gap-2">
                <Download className="h-4 w-4" />
                Download Acceptance Letter
              </Button>
            )}
            {!canEdit && !canSubmit && !canReapply && !isApproved && (
              <Button
                variant="outline"
                onClick={() => router.push('/application-status')}
              >
                Back to Status Lookup
              </Button>
            )}
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
