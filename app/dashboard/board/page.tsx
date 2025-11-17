"use client";

import { useState, useEffect } from "react";
import { boardApi } from "@/lib/api";
import type { MembershipApplication } from "@/lib/types";
import {
  CheckCircle2,
  XCircle,
  Clock,
  TrendingUp,
  UserCheck,
  Users,
  FileText,
  History,
} from "lucide-react";
import { VoteModal } from "@/components/board/VoteModal";
import { VoteHistoryModal } from "@/components/board/VoteHistoryModal";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface BoardStats {
  board_member_id: string;
  total_votes: number;
  approved: number;
  rejected: number;
  pending: number;
}

export default function BoardMemberDashboard() {
  const [pendingApplications, setPendingApplications] = useState<MembershipApplication[]>([]);
  const [stats, setStats] = useState<BoardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [selectedApplication, setSelectedApplication] = useState<MembershipApplication | null>(null);
  const [isVoteModalOpen, setIsVoteModalOpen] = useState(false);
  const [isHistoryModalOpen, setIsHistoryModalOpen] = useState(false);
  const [historyApplicationId, setHistoryApplicationId] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  useEffect(() => {
    if (successMessage || error) {
      const timer = setTimeout(() => {
        setSuccessMessage(null);
        setError(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage, error]);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [applications, boardStats] = await Promise.all([
        boardApi.getPendingApplications(),
        boardApi.getBoardStats(),
      ]);

      setPendingApplications(applications);
      setStats(boardStats);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
      console.error("Dashboard data fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleVoteClick = (application: MembershipApplication) => {
    setSelectedApplication(application);
    setIsVoteModalOpen(true);
  };

  const handleViewHistory = (applicationId: string) => {
    setHistoryApplicationId(applicationId);
    setIsHistoryModalOpen(true);
  };

  const handleVoteSubmit = async (action: 'APPROVE' | 'REJECT', notes: string) => {
    if (!selectedApplication) return;

    try {
      const result = await boardApi.castVote(selectedApplication.id, action, notes);
      setSuccessMessage(result.message);
      setIsVoteModalOpen(false);
      setSelectedApplication(null);

      // Refresh dashboard data
      await fetchDashboardData();
    } catch (err: any) {
      setError(err.message || 'Failed to cast vote');
      throw err; // Re-throw so modal can handle loading state
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return 'default';
      case 'REJECTED':
        return 'destructive';
      case 'UNDER_REVIEW':
        return 'secondary';
      default:
        return 'outline';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-white">
      {/* Success/Error Notifications */}
      {successMessage && (
        <div className="fixed top-4 right-4 z-50 bg-green-50 border border-green-200 text-green-800 px-6 py-3 rounded-lg shadow-lg flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-green-600" />
          <span className="font-medium">{successMessage}</span>
        </div>
      )}
      {error && (
        <div className="fixed top-4 right-4 z-50 bg-red-50 border border-red-200 text-red-800 px-6 py-3 rounded-lg shadow-lg flex items-center gap-3">
          <XCircle className="w-5 h-5 text-red-600" />
          <span className="font-medium">{error}</span>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-display text-3xl font-bold text-dojo-navy">
            Board Member Dashboard
          </h1>
          <p className="text-muted-foreground mt-2">
            Review and vote on pending membership applications
          </p>
        </div>

        {/* Loading State */}
        {loading && !stats ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-dojo-navy"></div>
          </div>
        ) : (
          <>
            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <TrendingUp className="w-4 h-4" />
                    Total Votes Cast
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-dojo-navy">
                    {stats?.total_votes || 0}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    All-time voting activity
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4" />
                    Applications Approved
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-dojo-green">
                    {stats?.approved || 0}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Successfully approved
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <XCircle className="w-4 h-4" />
                    Applications Rejected
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-dojo-orange">
                    {stats?.rejected || 0}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Denied applications
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    Pending Applications
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-dojo-navy">
                    {stats?.pending || 0}
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">
                    Awaiting your review
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Pending Applications Table */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Pending Applications
                </CardTitle>
                <CardDescription>
                  Applications requiring board member approval
                </CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {pendingApplications.length === 0 ? (
                  <div className="p-8 text-center text-muted-foreground">
                    <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p className="text-lg font-medium">No pending applications</p>
                    <p className="text-sm mt-1">
                      All applications have been reviewed or there are no new submissions
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Applicant Name</TableHead>
                          <TableHead>Email</TableHead>
                          <TableHead>Submitted Date</TableHead>
                          <TableHead>Approval Progress</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {pendingApplications.map((application) => (
                          <TableRow key={application.id}>
                            <TableCell className="font-medium">
                              {application.applicant_name}
                            </TableCell>
                            <TableCell>{application.applicant_email}</TableCell>
                            <TableCell>
                              {formatDate(application.submitted_at || application.created_at)}
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-medium">
                                  {application.approval_count} / {application.required_approvals}
                                </span>
                                <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                                  <div
                                    className="h-full bg-dojo-green transition-all"
                                    style={{
                                      width: `${(application.approval_count / application.required_approvals) * 100}%`
                                    }}
                                  />
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <Badge variant={getStatusBadgeVariant(application.status)}>
                                {application.status.replace('_', ' ')}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex items-center justify-end gap-2">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleViewHistory(application.id)}
                                >
                                  <History className="w-4 h-4 mr-2" />
                                  History
                                </Button>
                                <Button
                                  size="sm"
                                  onClick={() => handleVoteClick(application)}
                                  className="bg-dojo-navy hover:bg-dojo-navy/90"
                                >
                                  <UserCheck className="w-4 h-4 mr-2" />
                                  Vote
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Vote Modal */}
      {selectedApplication && (
        <VoteModal
          isOpen={isVoteModalOpen}
          onClose={() => {
            setIsVoteModalOpen(false);
            setSelectedApplication(null);
          }}
          application={selectedApplication}
          onVoteSubmit={handleVoteSubmit}
        />
      )}

      {/* Vote History Modal */}
      {historyApplicationId && (
        <VoteHistoryModal
          isOpen={isHistoryModalOpen}
          onClose={() => {
            setIsHistoryModalOpen(false);
            setHistoryApplicationId(null);
          }}
          applicationId={historyApplicationId}
        />
      )}
    </div>
  );
}
