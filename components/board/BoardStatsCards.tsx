"use client";

import { Vote, CheckCircle, XCircle, Clock } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface BoardStats {
  total_votes: number;
  approved: number;
  rejected: number;
  pending: number;
}

interface BoardStatsCardsProps {
  stats: BoardStats | null;
  loading: boolean;
}

export function BoardStatsCards({ stats, loading }: BoardStatsCardsProps) {
  // Show loading skeleton
  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                <div className="h-4 bg-gray-200 rounded animate-pulse w-24"></div>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-gray-200 rounded animate-pulse w-16 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded animate-pulse w-12"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  // Default to 0 if stats is null
  const totalVotes = stats?.total_votes || 0;
  const approved = stats?.approved || 0;
  const rejected = stats?.rejected || 0;
  const pending = stats?.pending || 0;

  const statsData = [
    {
      label: "Total Votes",
      value: totalVotes,
      icon: Vote,
      color: "text-dojo-navy",
      bgColor: "bg-dojo-navy/10",
      borderColor: "border-dojo-navy/20",
    },
    {
      label: "Approved",
      value: approved,
      icon: CheckCircle,
      color: "text-dojo-green",
      bgColor: "bg-dojo-green/10",
      borderColor: "border-dojo-green/20",
    },
    {
      label: "Rejected",
      value: rejected,
      icon: XCircle,
      color: "text-dojo-red",
      bgColor: "bg-dojo-red/10",
      borderColor: "border-dojo-red/20",
    },
    {
      label: "Pending Review",
      value: pending,
      icon: Clock,
      color: "text-dojo-orange",
      bgColor: "bg-dojo-orange/10",
      borderColor: "border-dojo-orange/20",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
      {statsData.map((stat) => {
        const Icon = stat.icon;
        return (
          <Card
            key={stat.label}
            className={`border-l-4 ${stat.borderColor} hover:shadow-lg transition-shadow`}
          >
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.label}
                </CardTitle>
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`w-4 h-4 ${stat.color}`} />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-baseline justify-between">
                <div className={`text-3xl font-bold ${stat.color}`}>
                  {stat.value}
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
