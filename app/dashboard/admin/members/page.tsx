"use client";

import { useState, useEffect } from "react";
import { adminApi } from "@/lib/api";
import { User } from "@/lib/types";
import { MemberTable } from "@/components/admin/MemberTable";
import { MemberFilters } from "@/components/admin/MemberFilters";
import { MemberDetailsModal } from "@/components/admin/MemberDetailsModal";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus, Download, CheckCircle2, XCircle, Users } from "lucide-react";
import { useRouter } from "next/navigation";

interface MemberFiltersState {
  search: string;
  role: string;
  is_active: string;
}

export default function AdminMembersPage() {
  const router = useRouter();
  const [members, setMembers] = useState<User[]>([]);
  const [filteredMembers, setFilteredMembers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [selectedMember, setSelectedMember] = useState<User | null>(null);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<"view" | "edit" | "create">("view");

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalMembers, setTotalMembers] = useState(0);
  const [pageSize] = useState(20);

  // Filter state
  const [filters, setFilters] = useState<MemberFiltersState>({
    search: "",
    role: "all",
    is_active: "all",
  });

  // Fetch members on mount and when filters/pagination change
  useEffect(() => {
    fetchMembers();
  }, [currentPage, filters]);

  // Auto-clear success/error messages
  useEffect(() => {
    if (successMessage || error) {
      const timer = setTimeout(() => {
        setSuccessMessage(null);
        setError(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [successMessage, error]);

  const fetchMembers = async () => {
    try {
      setLoading(true);
      setError(null);

      const params: any = {
        limit: pageSize,
        offset: (currentPage - 1) * pageSize,
      };

      if (filters.search) params.search = filters.search;
      if (filters.role !== "all") params.role = filters.role;
      if (filters.is_active !== "all") params.is_active = filters.is_active === "true";

      const response = await adminApi.getMembers(params);

      setMembers(response.members || []);
      setFilteredMembers(response.members || []);
      setTotalMembers(response.total || 0);
    } catch (err: any) {
      setError(err.message || "Failed to load members");
      console.error("Members fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters: MemberFiltersState) => {
    setFilters(newFilters);
    setCurrentPage(1); // Reset to first page when filters change
  };

  const handleCreateMember = () => {
    setSelectedMember(null);
    setModalMode("create");
    setIsDetailsModalOpen(true);
  };

  const handleViewMember = (member: User) => {
    setSelectedMember(member);
    setModalMode("view");
    setIsDetailsModalOpen(true);
  };

  const handleEditMember = (member: User) => {
    setSelectedMember(member);
    setModalMode("edit");
    setIsDetailsModalOpen(true);
  };

  const handleDeleteMember = async (member: User) => {
    if (!confirm(`Are you sure you want to delete ${member.first_name} ${member.last_name}? This action cannot be undone.`)) {
      return;
    }

    try {
      setError(null);
      await adminApi.deleteMember(member.id);
      setSuccessMessage("Member deleted successfully!");
      await fetchMembers();
    } catch (err: any) {
      setError(err.message || "Failed to delete member");
      console.error("Member deletion error:", err);
    }
  };

  const handleMemberSaved = async () => {
    setIsDetailsModalOpen(false);
    setSelectedMember(null);
    setSuccessMessage(modalMode === "create" ? "Member created successfully!" : "Member updated successfully!");
    await fetchMembers();
  };

  const handleExportCSV = () => {
    try {
      // Convert members data to CSV
      const headers = ["ID", "First Name", "Last Name", "Email", "Role", "Status", "Phone", "Created At"];
      const csvRows = [
        headers.join(","),
        ...filteredMembers.map(m => [
          m.id,
          m.first_name || "",
          m.last_name || "",
          m.email,
          m.role,
          m.role === "member" ? "Active" : "Active", // Simplified status
          m.phone || "",
          new Date().toISOString().split('T')[0], // Placeholder for created_at
        ].map(field => `"${field}"`).join(","))
      ].join("\n");

      // Create download
      const blob = new Blob([csvRows], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `members-export-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      setSuccessMessage("Member list exported successfully!");
    } catch (err: any) {
      setError("Failed to export member list");
      console.error("Export error:", err);
    }
  };

  const totalPages = Math.ceil(totalMembers / pageSize);

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

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-display text-3xl font-bold text-dojo-navy">Member Management</h1>
              <p className="text-muted-foreground mt-2">
                Manage all members, update profiles, and view activity
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button variant="outline" onClick={handleExportCSV}>
                <Download className="w-4 h-4 mr-2" />
                Export CSV
              </Button>
              <Button onClick={handleCreateMember}>
                <Plus className="w-4 h-4 mr-2" />
                Add Member
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Members
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline justify-between">
                <div className="text-3xl font-bold text-dojo-navy">
                  {totalMembers}
                </div>
                <Users className="w-5 h-5 text-muted-foreground" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Active Members
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline justify-between">
                <div className="text-3xl font-bold text-dojo-green">
                  {members.filter(m => m.role !== "guest").length}
                </div>
                <CheckCircle2 className="w-5 h-5 text-dojo-green" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Instructors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline justify-between">
                <div className="text-3xl font-bold text-dojo-orange">
                  {members.filter(m => m.role === "instructor").length}
                </div>
                <Users className="w-5 h-5 text-dojo-orange" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Admins
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline justify-between">
                <div className="text-3xl font-bold text-dojo-navy">
                  {members.filter(m => m.role === "admin" || m.role === "superadmin").length}
                </div>
                <Users className="w-5 h-5 text-dojo-navy" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <MemberFilters
          filters={filters}
          onFilterChange={handleFilterChange}
        />

        {/* Members Table */}
        {loading ? (
          <Card className="mt-6">
            <CardContent className="py-12">
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-dojo-navy"></div>
              </div>
            </CardContent>
          </Card>
        ) : filteredMembers.length === 0 ? (
          <Card className="mt-6">
            <CardContent className="py-12">
              <div className="text-center text-muted-foreground">
                <Users className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                <p className="text-lg font-medium">No members found</p>
                <p className="text-sm mt-2">Try adjusting your filters or create a new member</p>
              </div>
            </CardContent>
          </Card>
        ) : (
          <>
            <MemberTable
              members={filteredMembers}
              onViewMember={handleViewMember}
              onEditMember={handleEditMember}
              onDeleteMember={handleDeleteMember}
            />

            {/* Pagination */}
            {totalPages > 1 && (
              <Card className="mt-6">
                <CardContent className="py-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      Showing {((currentPage - 1) * pageSize) + 1} to {Math.min(currentPage * pageSize, totalMembers)} of {totalMembers} members
                    </div>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                      >
                        Previous
                      </Button>
                      <div className="text-sm font-medium">
                        Page {currentPage} of {totalPages}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>

      {/* Member Details/Edit/Create Modal */}
      <MemberDetailsModal
        isOpen={isDetailsModalOpen}
        onClose={() => {
          setIsDetailsModalOpen(false);
          setSelectedMember(null);
        }}
        member={selectedMember}
        mode={modalMode}
        onSave={handleMemberSaved}
      />
    </div>
  );
}
