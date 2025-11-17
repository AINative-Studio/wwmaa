"use client";

import { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Search, X } from "lucide-react";

interface MemberFiltersProps {
  filters: {
    search: string;
    role: string;
    is_active: string;
  };
  onFilterChange: (filters: {
    search: string;
    role: string;
    is_active: string;
  }) => void;
}

export function MemberFilters({ filters, onFilterChange }: MemberFiltersProps) {
  const [localSearch, setLocalSearch] = useState(filters.search);

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      if (localSearch !== filters.search) {
        onFilterChange({ ...filters, search: localSearch });
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [localSearch]);

  const handleClearFilters = () => {
    setLocalSearch("");
    onFilterChange({
      search: "",
      role: "all",
      is_active: "all",
    });
  };

  const hasActiveFilters =
    filters.search || filters.role !== "all" || filters.is_active !== "all";

  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex flex-wrap gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[300px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                placeholder="Search by name, email, or phone..."
                value={localSearch}
                onChange={(e) => setLocalSearch(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {/* Role Filter */}
          <Select
            value={filters.role}
            onValueChange={(value) => onFilterChange({ ...filters, role: value })}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by role" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Roles</SelectItem>
              <SelectItem value="member">Member</SelectItem>
              <SelectItem value="instructor">Instructor</SelectItem>
              <SelectItem value="board_member">Board Member</SelectItem>
              <SelectItem value="admin">Admin</SelectItem>
              <SelectItem value="superadmin">Super Admin</SelectItem>
            </SelectContent>
          </Select>

          {/* Status Filter */}
          <Select
            value={filters.is_active}
            onValueChange={(value) => onFilterChange({ ...filters, is_active: value })}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="true">Active</SelectItem>
              <SelectItem value="false">Inactive</SelectItem>
            </SelectContent>
          </Select>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <Button
              variant="outline"
              size="icon"
              onClick={handleClearFilters}
              title="Clear all filters"
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>

        {/* Active Filters Display */}
        {hasActiveFilters && (
          <div className="mt-4 flex items-center gap-2 flex-wrap">
            <span className="text-sm text-muted-foreground">Active filters:</span>
            {filters.search && (
              <div className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-md">
                <Search className="w-3 h-3" />
                {filters.search}
              </div>
            )}
            {filters.role !== "all" && (
              <div className="inline-flex items-center gap-1 px-2 py-1 bg-purple-50 text-purple-700 text-xs rounded-md">
                Role: {filters.role}
              </div>
            )}
            {filters.is_active !== "all" && (
              <div className="inline-flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 text-xs rounded-md">
                Status: {filters.is_active === "true" ? "Active" : "Inactive"}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
