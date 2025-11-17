"use client";

import { useState, useEffect } from "react";
import { adminApi } from "@/lib/api";
import type { EventItem } from "@/lib/types";
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  Calendar,
  TrendingUp,
  Settings,
  FileText,
  Search,
  Bell,
  Plus,
  Mail,
  Download,
  Filter,
  MoreVertical,
  Edit,
  Trash2,
  UserX,
  CheckCircle2,
  XCircle,
  Clock,
  DollarSign,
  ArrowUpRight,
  ArrowDownRight,
  Target,
  Activity,
  MapPin,
  ChevronRight,
  UserPlus,
  Send
} from "lucide-react";
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Checkbox } from "@/components/ui/checkbox";
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// Mock data for the dashboard
const memberGrowthData = [
  { month: "Jan", members: 120 },
  { month: "Feb", members: 145 },
  { month: "Mar", members: 168 },
  { month: "Apr", members: 192 },
  { month: "May", members: 215 },
  { month: "Jun", members: 248 },
];

const tierDistributionData = [
  { name: "Basic", value: 145, color: "#023E73" },
  { name: "Premium", value: 78, color: "#025951" },
  { name: "Instructor", value: 25, color: "#F25D07" },
];

const revenueData = [
  { month: "Jan", revenue: 24500 },
  { month: "Feb", revenue: 28900 },
  { month: "Mar", revenue: 31200 },
  { month: "Apr", revenue: 35800 },
  { month: "May", revenue: 38500 },
  { month: "Jun", revenue: 42300 },
];

const geographicData = [
  { country: "United States", members: 98 },
  { country: "United Kingdom", members: 45 },
  { country: "Canada", members: 32 },
  { country: "Australia", members: 28 },
  { country: "Germany", members: 21 },
];

const mockMembers = [
  {
    id: "1",
    name: "John Smith",
    email: "john.smith@example.com",
    tier: "Premium",
    beltRank: "Black Belt",
    joinDate: "2024-01-15",
    status: "Active",
    paymentStatus: "Paid",
  },
  {
    id: "2",
    name: "Sarah Johnson",
    email: "sarah.j@example.com",
    tier: "Basic",
    beltRank: "Brown Belt",
    joinDate: "2024-02-20",
    status: "Active",
    paymentStatus: "Paid",
  },
  {
    id: "3",
    name: "Michael Chen",
    email: "m.chen@example.com",
    tier: "Instructor",
    beltRank: "Black Belt",
    joinDate: "2023-11-10",
    status: "Active",
    paymentStatus: "Paid",
  },
  {
    id: "4",
    name: "Emma Wilson",
    email: "emma.w@example.com",
    tier: "Premium",
    beltRank: "Purple Belt",
    joinDate: "2024-03-05",
    status: "Active",
    paymentStatus: "Overdue",
  },
  {
    id: "5",
    name: "David Martinez",
    email: "d.martinez@example.com",
    tier: "Basic",
    beltRank: "Blue Belt",
    joinDate: "2024-04-12",
    status: "Suspended",
    paymentStatus: "Unpaid",
  },
];

const mockInstructors = [
  {
    id: "1",
    name: "Sensei Takeshi",
    credentials: "8th Dan Black Belt",
    classesTaught: 24,
    students: 45,
    rating: 4.9,
  },
  {
    id: "2",
    name: "Master Lee",
    credentials: "7th Dan Black Belt",
    classesTaught: 18,
    students: 38,
    rating: 4.8,
  },
  {
    id: "3",
    name: "Coach Maria",
    credentials: "5th Dan Black Belt",
    classesTaught: 15,
    students: 32,
    rating: 4.7,
  },
];

const mockEvents = [
  {
    id: "1",
    title: "Summer Training Camp",
    date: "2025-07-15",
    type: "Training",
    registrations: 45,
    capacity: 50,
    status: "Upcoming",
  },
  {
    id: "2",
    title: "International Seminar",
    date: "2025-08-20",
    type: "Seminar",
    registrations: 78,
    capacity: 100,
    status: "Upcoming",
  },
  {
    id: "3",
    title: "Regional Tournament",
    date: "2025-09-10",
    type: "Tournament",
    registrations: 120,
    capacity: 150,
    status: "Upcoming",
  },
];

const recentActivities = [
  { id: 1, user: "John Smith", action: "Upgraded to Premium", time: "2 hours ago" },
  { id: 2, user: "Sarah Johnson", action: "Registered for event", time: "4 hours ago" },
  { id: 3, user: "Michael Chen", action: "Payment received", time: "6 hours ago" },
  { id: 4, user: "Emma Wilson", action: "Profile updated", time: "8 hours ago" },
  { id: 5, user: "David Martinez", action: "New member joined", time: "1 day ago" },
];

const pendingActions = [
  { id: 1, type: "approval", item: "3 membership applications", count: 3 },
  { id: 2, type: "promotion", item: "2 belt promotion requests", count: 2 },
  { id: 3, type: "registration", item: "15 event registrations", count: 15 },
];

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState("overview");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedMembers, setSelectedMembers] = useState<string[]>([]);
  const [isAddMemberOpen, setIsAddMemberOpen] = useState(false);
  const [isEditMemberOpen, setIsEditMemberOpen] = useState(false);
  const [isDeleteMemberOpen, setIsDeleteMemberOpen] = useState(false);
  const [isAddInstructorOpen, setIsAddInstructorOpen] = useState(false);
  const [isAddEventOpen, setIsAddEventOpen] = useState(false);
  const [isEditTierOpen, setIsEditTierOpen] = useState(false);
  const [filterTier, setFilterTier] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");

  // State for real data
  const [events, setEvents] = useState<EventItem[]>([]);
  const [members, setMembers] = useState<any[]>([]);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Member being edited or deleted
  const [currentMember, setCurrentMember] = useState<any | null>(null);
  const [memberActionLoading, setMemberActionLoading] = useState(false);

  // Form state for creating events
  const [eventFormData, setEventFormData] = useState({
    title: "",
    description: "",
    event_type: "seminar" as const,
    start_date: "",
    end_date: "",
    location: "",
    is_online: false,
    capacity: "",
    price: "",
  });

  // Form state for member add/edit
  const [memberFormData, setMemberFormData] = useState({
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    role: "member",
    is_active: true,
    phone: "",
  });

  // Fetch data on mount
  useEffect(() => {
    fetchDashboardData();
  }, []);

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

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [eventsData, metricsData, membersData] = await Promise.all([
        adminApi.getEvents(),
        adminApi.getMetrics(),
        adminApi.getMembers({ limit: 100 }),
      ]);

      setEvents(eventsData);
      setMetrics(metricsData);
      setMembers(membersData.members || []);
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
      console.error("Dashboard data fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Member CRUD handlers
  const handleAddMember = async () => {
    try {
      setError(null);
      setMemberActionLoading(true);

      // Validate required fields
      if (!memberFormData.email || !memberFormData.first_name || !memberFormData.last_name || !memberFormData.password) {
        setError("Please fill in all required fields");
        setMemberActionLoading(false);
        return;
      }

      const newMember = await adminApi.createMember(memberFormData);
      setMembers(prev => [newMember, ...prev]);
      setSuccessMessage("Member created successfully!");
      setIsAddMemberOpen(false);

      // Reset form
      setMemberFormData({
        email: "",
        first_name: "",
        last_name: "",
        password: "",
        role: "member",
        is_active: true,
        phone: "",
      });

      // Refresh members list
      await fetchDashboardData();
    } catch (err: any) {
      setError(err.message || "Failed to create member");
      console.error("Member creation error:", err);
    } finally {
      setMemberActionLoading(false);
    }
  };

  const handleEditMember = async () => {
    try {
      setError(null);
      setMemberActionLoading(true);

      if (!currentMember) {
        setError("No member selected");
        setMemberActionLoading(false);
        return;
      }

      // Only send changed fields
      const updateData: any = {};
      if (memberFormData.email !== currentMember.email) updateData.email = memberFormData.email;
      if (memberFormData.first_name !== currentMember.first_name) updateData.first_name = memberFormData.first_name;
      if (memberFormData.last_name !== currentMember.last_name) updateData.last_name = memberFormData.last_name;
      if (memberFormData.role !== currentMember.role) updateData.role = memberFormData.role;
      if (memberFormData.is_active !== currentMember.is_active) updateData.is_active = memberFormData.is_active;
      if (memberFormData.phone !== currentMember.phone) updateData.phone = memberFormData.phone;
      if (memberFormData.password) updateData.password = memberFormData.password;

      const updatedMember = await adminApi.updateMember(currentMember.id, updateData);
      setMembers(prev => prev.map(m => m.id === currentMember.id ? updatedMember : m));
      setSuccessMessage("Member updated successfully!");
      setIsEditMemberOpen(false);
      setCurrentMember(null);

      // Reset form
      setMemberFormData({
        email: "",
        first_name: "",
        last_name: "",
        password: "",
        role: "member",
        is_active: true,
        phone: "",
      });

      // Refresh members list
      await fetchDashboardData();
    } catch (err: any) {
      setError(err.message || "Failed to update member");
      console.error("Member update error:", err);
    } finally {
      setMemberActionLoading(false);
    }
  };

  const handleDeleteMember = async () => {
    try {
      setError(null);
      setMemberActionLoading(true);

      if (!currentMember) {
        setError("No member selected");
        setMemberActionLoading(false);
        return;
      }

      await adminApi.deleteMember(currentMember.id);
      setMembers(prev => prev.filter(m => m.id !== currentMember.id));
      setSuccessMessage("Member deleted successfully!");
      setIsDeleteMemberOpen(false);
      setCurrentMember(null);

      // Refresh members list
      await fetchDashboardData();
    } catch (err: any) {
      setError(err.message || "Failed to delete member");
      console.error("Member deletion error:", err);
    } finally {
      setMemberActionLoading(false);
    }
  };

  const openEditMemberModal = (member: any) => {
    setCurrentMember(member);
    setMemberFormData({
      email: member.email || "",
      first_name: member.first_name || "",
      last_name: member.last_name || "",
      password: "",
      role: member.role || "member",
      is_active: member.is_active !== undefined ? member.is_active : true,
      phone: member.phone || "",
    });
    setIsEditMemberOpen(true);
  };

  const openDeleteMemberModal = (member: any) => {
    setCurrentMember(member);
    setIsDeleteMemberOpen(true);
  };

  const toggleMemberSelection = (memberId: string) => {
    setSelectedMembers(prev =>
      prev.includes(memberId)
        ? prev.filter(id => id !== memberId)
        : [...prev, memberId]
    );
  };

  const toggleSelectAll = () => {
    if (selectedMembers.length === mockMembers.length) {
      setSelectedMembers([]);
    } else {
      setSelectedMembers(mockMembers.map(m => m.id));
    }
  };

  const filteredMembers = (members.length > 0 ? members : mockMembers).filter(member => {
    const matchesSearch = member.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         member.email?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesTier = filterTier === "all" || member.tier === filterTier;
    const matchesStatus = filterStatus === "all" || member.status === filterStatus;
    return matchesSearch && matchesTier && matchesStatus;
  });

  // Event creation handler
  const handleCreateEvent = async () => {
    try {
      setError(null);
      setLoading(true);

      // Validate required fields
      if (!eventFormData.title || !eventFormData.start_date || !eventFormData.end_date) {
        setError("Please fill in all required fields");
        setLoading(false);
        return;
      }

      const eventData = {
        title: eventFormData.title,
        description: eventFormData.description || undefined,
        event_type: eventFormData.event_type,
        start_date: new Date(eventFormData.start_date).toISOString(),
        end_date: new Date(eventFormData.end_date).toISOString(),
        location: eventFormData.location || (eventFormData.is_online ? "Online" : "TBD"),
        is_online: eventFormData.is_online,
        capacity: eventFormData.capacity ? parseInt(eventFormData.capacity) : undefined,
        price: eventFormData.price ? parseFloat(eventFormData.price) : undefined,
        visibility: "public" as const,
      };

      const newEvent = await adminApi.createEvent(eventData);
      setEvents(prev => [newEvent, ...prev]);
      setSuccessMessage("Event created successfully!");
      setIsAddEventOpen(false);

      // Reset form
      setEventFormData({
        title: "",
        description: "",
        event_type: "seminar",
        start_date: "",
        end_date: "",
        location: "",
        is_online: false,
        capacity: "",
        price: "",
      });
    } catch (err: any) {
      setError(err.message || "Failed to create event");
      console.error("Event creation error:", err);
    } finally {
      setLoading(false);
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

      <div className="flex">
        {/* Sidebar */}
        <div className="w-64 bg-card border-r border-border min-h-screen sticky top-0">
          <div className="p-6">
            <h2 className="font-display text-xl font-bold text-dojo-navy">Admin Panel</h2>
            <p className="text-sm text-muted-foreground mt-1">Management Dashboard</p>
          </div>

          <ScrollArea className="h-[calc(100vh-120px)]">
            <nav className="space-y-1 px-3">
              {[
                { id: "overview", icon: LayoutDashboard, label: "Overview", route: null },
                { id: "members", icon: Users, label: "Members", route: "/dashboard/admin/members" },
                { id: "instructors", icon: GraduationCap, label: "Instructors", route: null },
                { id: "events", icon: Calendar, label: "Events", route: null },
                { id: "analytics", icon: TrendingUp, label: "Analytics", route: null },
                { id: "content", icon: FileText, label: "Content Management", route: null },
                { id: "settings", icon: Settings, label: "Settings", route: null },
              ].map((item) => (
                <button
                  key={item.id}
                  onClick={() => {
                    if (item.route) {
                      window.location.href = item.route;
                    } else {
                      setActiveTab(item.id);
                    }
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    activeTab === item.id
                      ? "bg-dojo-navy text-white"
                      : "text-gray-700 hover:bg-gray-100"
                  }`}
                >
                  <item.icon className="w-4 h-4" />
                  {item.label}
                </button>
              ))}
            </nav>
          </ScrollArea>
        </div>

        {/* Main Content */}
        <div className="flex-1">
          {/* Header */}
          <header className="bg-card border-b border-border sticky top-0 z-10">
            <div className="flex items-center justify-between px-8 py-4">
              <div>
                <h1 className="font-display text-2xl font-bold text-dojo-navy">
                  {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                  {activeTab === "overview" && "Complete dashboard overview"}
                  {activeTab === "members" && "Manage all members"}
                  {activeTab === "instructors" && "Manage instructors"}
                  {activeTab === "events" && "Event management"}
                  {activeTab === "analytics" && "Detailed analytics"}
                  {activeTab === "content" && "Content & resources"}
                  {activeTab === "settings" && "System settings"}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Button variant="outline" size="icon">
                  <Bell className="w-4 h-4" />
                </Button>
                <div className="w-8 h-8 rounded-full bg-gradient-navy flex items-center justify-center text-white text-sm font-semibold">
                  AD
                </div>
              </div>
            </div>
          </header>

          {/* Content Area */}
          <div className="p-8">
            {/* Overview Section */}
            {activeTab === "overview" && (
              <div className="space-y-6">
                {/* Key Metrics */}
                {loading && !metrics ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-dojo-navy"></div>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          Total Members
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-baseline justify-between">
                          <div className="text-3xl font-bold text-dojo-navy">
                            {metrics?.total_members || 0}
                          </div>
                          <div className="flex items-center gap-1 text-success text-sm font-medium">
                            <ArrowUpRight className="w-4 h-4" />
                            12.5%
                          </div>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                          +28 this month
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          Revenue (Monthly)
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-baseline justify-between">
                          <div className="text-3xl font-bold text-dojo-navy">
                            ${((metrics?.revenue_monthly || 0) / 1000).toFixed(1)}K
                          </div>
                          <div className="flex items-center gap-1 text-success text-sm font-medium">
                            <ArrowUpRight className="w-4 h-4" />
                            8.2%
                          </div>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                          +$3.8K from last month
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          Active Events
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-baseline justify-between">
                          <div className="text-3xl font-bold text-dojo-navy">
                            {metrics?.active_events || events.length}
                          </div>
                          <Badge variant="outline" className="text-dojo-green border-dojo-green">
                            Live
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                          {events.length} total events
                        </p>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-sm font-medium text-muted-foreground">
                          Retention Rate
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-baseline justify-between">
                          <div className="text-3xl font-bold text-dojo-navy">
                            {metrics?.retention_rate ? `${Math.round(metrics.retention_rate * 100)}%` : '94%'}
                          </div>
                          <div className="flex items-center gap-1 text-success text-sm font-medium">
                            <ArrowUpRight className="w-4 h-4" />
                            2.1%
                          </div>
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                          Excellent performance
                        </p>
                      </CardContent>
                    </Card>
                  </div>
                )}

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <Card className="lg:col-span-2">
                    <CardHeader>
                      <CardTitle>Member Growth</CardTitle>
                      <CardDescription>Total members over the last 6 months</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={memberGrowthData}>
                          <defs>
                            <linearGradient id="colorMembers" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#023E73" stopOpacity={0.8}/>
                              <stop offset="95%" stopColor="#023E73" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                          <XAxis dataKey="month" stroke="#6B7280" />
                          <YAxis stroke="#6B7280" />
                          <Tooltip />
                          <Area
                            type="monotone"
                            dataKey="members"
                            stroke="#023E73"
                            fillOpacity={1}
                            fill="url(#colorMembers)"
                          />
                        </AreaChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Membership Tiers</CardTitle>
                      <CardDescription>Active memberships by tier</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                          <Pie
                            data={tierDistributionData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {tierDistributionData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                </div>

                {/* Activities and Actions */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Recent Activities</CardTitle>
                      <CardDescription>Latest member activities</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {recentActivities.map((activity) => (
                          <div key={activity.id} className="flex items-start gap-3">
                            <div className="w-2 h-2 rounded-full bg-dojo-green mt-2" />
                            <div className="flex-1">
                              <p className="text-sm font-medium text-gray-900">
                                {activity.user}
                              </p>
                              <p className="text-sm text-muted-foreground">
                                {activity.action}
                              </p>
                            </div>
                            <span className="text-xs text-muted-foreground">
                              {activity.time}
                            </span>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Pending Actions</CardTitle>
                      <CardDescription>Items requiring attention</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {pendingActions.map((action) => (
                        <div
                          key={action.id}
                          className="flex items-center justify-between p-3 rounded-lg bg-orange-50 border border-orange-200"
                        >
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-dojo-orange flex items-center justify-center text-white text-sm font-bold">
                              {action.count}
                            </div>
                            <span className="text-sm font-medium text-gray-900">
                              {action.item}
                            </span>
                          </div>
                          <Button size="sm" variant="outline">
                            Review
                          </Button>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </div>

                {/* Quick Actions */}
                <Card>
                  <CardHeader>
                    <CardTitle>Quick Actions</CardTitle>
                    <CardDescription>Common administrative tasks</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <Button
                        onClick={() => setIsAddMemberOpen(true)}
                        className="h-auto py-4 flex-col gap-2"
                        variant="outline"
                      >
                        <UserPlus className="w-5 h-5" />
                        Add New Member
                      </Button>
                      <Button
                        onClick={() => setIsAddEventOpen(true)}
                        className="h-auto py-4 flex-col gap-2"
                        variant="outline"
                      >
                        <Plus className="w-5 h-5" />
                        Create Event
                      </Button>
                      <Button
                        className="h-auto py-4 flex-col gap-2"
                        variant="outline"
                      >
                        <Send className="w-5 h-5" />
                        Send Announcement
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Members Section */}
            {activeTab === "members" && (
              <div className="space-y-6">
                {/* Filters and Search */}
                <Card>
                  <CardContent className="pt-6">
                    <div className="flex flex-wrap gap-4">
                      <div className="flex-1 min-w-[300px]">
                        <div className="relative">
                          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                          <Input
                            placeholder="Search by name or email..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-10"
                          />
                        </div>
                      </div>
                      <Select value={filterTier} onValueChange={setFilterTier}>
                        <SelectTrigger className="w-[150px]">
                          <SelectValue placeholder="Tier" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Tiers</SelectItem>
                          <SelectItem value="Basic">Basic</SelectItem>
                          <SelectItem value="Premium">Premium</SelectItem>
                          <SelectItem value="Instructor">Instructor</SelectItem>
                        </SelectContent>
                      </Select>
                      <Select value={filterStatus} onValueChange={setFilterStatus}>
                        <SelectTrigger className="w-[150px]">
                          <SelectValue placeholder="Status" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Status</SelectItem>
                          <SelectItem value="Active">Active</SelectItem>
                          <SelectItem value="Suspended">Suspended</SelectItem>
                        </SelectContent>
                      </Select>
                      <Button variant="outline">
                        <Filter className="w-4 h-4 mr-2" />
                        More Filters
                      </Button>
                      <Button onClick={() => setIsAddMemberOpen(true)}>
                        <Plus className="w-4 h-4 mr-2" />
                        Add Member
                      </Button>
                    </div>

                    {selectedMembers.length > 0 && (
                      <div className="mt-4 flex items-center gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                        <span className="text-sm font-medium text-blue-900">
                          {selectedMembers.length} selected
                        </span>
                        <Separator orientation="vertical" className="h-6" />
                        <Button size="sm" variant="outline">
                          <Mail className="w-4 h-4 mr-2" />
                          Send Email
                        </Button>
                        <Button size="sm" variant="outline">
                          Update Tier
                        </Button>
                        <Button size="sm" variant="outline">
                          <Download className="w-4 h-4 mr-2" />
                          Export
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Members Table */}
                <Card>
                  <CardContent className="p-0">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-12">
                            <Checkbox
                              checked={selectedMembers.length === mockMembers.length}
                              onCheckedChange={toggleSelectAll}
                            />
                          </TableHead>
                          <TableHead>Name</TableHead>
                          <TableHead>Email</TableHead>
                          <TableHead>Tier</TableHead>
                          <TableHead>Belt Rank</TableHead>
                          <TableHead>Join Date</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead>Payment</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredMembers.map((member) => (
                          <TableRow key={member.id}>
                            <TableCell>
                              <Checkbox
                                checked={selectedMembers.includes(member.id)}
                                onCheckedChange={() => toggleMemberSelection(member.id)}
                              />
                            </TableCell>
                            <TableCell className="font-medium">{member.name}</TableCell>
                            <TableCell>{member.email}</TableCell>
                            <TableCell>
                              <Badge
                                variant="outline"
                                className={
                                  member.tier === "Instructor"
                                    ? "border-dojo-orange text-dojo-orange"
                                    : member.tier === "Premium"
                                    ? "border-dojo-green text-dojo-green"
                                    : "border-dojo-navy text-dojo-navy"
                                }
                              >
                                {member.tier}
                              </Badge>
                            </TableCell>
                            <TableCell>{member.beltRank}</TableCell>
                            <TableCell>{member.joinDate}</TableCell>
                            <TableCell>
                              <Badge
                                variant={member.status === "Active" ? "default" : "destructive"}
                              >
                                {member.status}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge
                                variant={
                                  member.paymentStatus === "Paid"
                                    ? "default"
                                    : member.paymentStatus === "Overdue"
                                    ? "secondary"
                                    : "destructive"
                                }
                              >
                                {member.paymentStatus}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-right">
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon">
                                    <MoreVertical className="w-4 h-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                  <DropdownMenuItem onClick={() => openEditMemberModal(member)}>
                                    <Edit className="w-4 h-4 mr-2" />
                                    Edit
                                  </DropdownMenuItem>
                                  <DropdownMenuItem>
                                    <Mail className="w-4 h-4 mr-2" />
                                    Send Email
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem>
                                    <UserX className="w-4 h-4 mr-2" />
                                    Suspend
                                  </DropdownMenuItem>
                                  <DropdownMenuItem
                                    className="text-red-600"
                                    onClick={() => openDeleteMemberModal(member)}
                                  >
                                    <Trash2 className="w-4 h-4 mr-2" />
                                    Delete
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Instructors Section */}
            {activeTab === "instructors" && (
              <div className="space-y-6">
                <div className="flex justify-end">
                  <Button onClick={() => setIsAddInstructorOpen(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Instructor
                  </Button>
                </div>

                <Card>
                  <CardContent className="p-0">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Name</TableHead>
                          <TableHead>Credentials</TableHead>
                          <TableHead>Classes Taught</TableHead>
                          <TableHead>Students</TableHead>
                          <TableHead>Rating</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {mockInstructors.map((instructor) => (
                          <TableRow key={instructor.id}>
                            <TableCell className="font-medium">{instructor.name}</TableCell>
                            <TableCell>{instructor.credentials}</TableCell>
                            <TableCell>{instructor.classesTaught}</TableCell>
                            <TableCell>{instructor.students}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-1">
                                <span className="font-semibold">{instructor.rating}</span>
                                <span className="text-yellow-500">★</span>
                              </div>
                            </TableCell>
                            <TableCell className="text-right">
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon">
                                    <MoreVertical className="w-4 h-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem>
                                    <Edit className="w-4 h-4 mr-2" />
                                    Edit Details
                                  </DropdownMenuItem>
                                  <DropdownMenuItem>
                                    <Activity className="w-4 h-4 mr-2" />
                                    View Performance
                                  </DropdownMenuItem>
                                  <DropdownMenuItem>
                                    <Calendar className="w-4 h-4 mr-2" />
                                    Assign Classes
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem className="text-red-600">
                                    <Trash2 className="w-4 h-4 mr-2" />
                                    Remove
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Events Section */}
            {activeTab === "events" && (
              <div className="space-y-6">
                <div className="flex justify-end">
                  <Button onClick={() => setIsAddEventOpen(true)}>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Event
                  </Button>
                </div>

                {loading && events.length === 0 ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-dojo-navy"></div>
                  </div>
                ) : (
                  <Card>
                    <CardContent className="p-0">
                      {events.length === 0 ? (
                        <div className="p-8 text-center text-muted-foreground">
                          No events found. Create your first event to get started!
                        </div>
                      ) : (
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>Event Title</TableHead>
                              <TableHead>Start Date</TableHead>
                              <TableHead>Type</TableHead>
                              <TableHead>Location</TableHead>
                              <TableHead>Capacity</TableHead>
                              <TableHead>Status</TableHead>
                              <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {events.map((event) => (
                              <TableRow key={event.id}>
                                <TableCell className="font-medium">{event.title}</TableCell>
                                <TableCell>
                                  {new Date(event.start).toLocaleDateString()}
                                </TableCell>
                                <TableCell>
                                  <Badge variant="outline">{event.type}</Badge>
                                </TableCell>
                                <TableCell>
                                  {event.location_type === 'online' ? 'Online' : event.location}
                                </TableCell>
                                <TableCell>
                                  {event.max_participants || 'Unlimited'}
                                </TableCell>
                                <TableCell>
                                  <Badge variant={event.status === 'published' ? "default" : "secondary"}>
                                    {event.status}
                                  </Badge>
                                </TableCell>
                                <TableCell className="text-right">
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button variant="ghost" size="icon">
                                    <MoreVertical className="w-4 h-4" />
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuItem>
                                    <Edit className="w-4 h-4 mr-2" />
                                    Edit Event
                                  </DropdownMenuItem>
                                  <DropdownMenuItem>
                                    <Users className="w-4 h-4 mr-2" />
                                    View Registrations
                                  </DropdownMenuItem>
                                  <DropdownMenuItem>
                                    <CheckCircle2 className="w-4 h-4 mr-2" />
                                    Track Attendance
                                  </DropdownMenuItem>
                                  <DropdownMenuItem>
                                    <Download className="w-4 h-4 mr-2" />
                                    Export Attendees
                                  </DropdownMenuItem>
                                  <DropdownMenuSeparator />
                                  <DropdownMenuItem
                                    className="text-red-600"
                                    onClick={async () => {
                                      try {
                                        await adminApi.deleteEvent(event.id);
                                        setEvents(prev => prev.filter(e => e.id !== event.id));
                                        setSuccessMessage("Event deleted successfully!");
                                      } catch (err: any) {
                                        setError(err.message || "Failed to delete event");
                                      }
                                    }}
                                  >
                                    <Trash2 className="w-4 h-4 mr-2" />
                                    Delete Event
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                      )}
                    </CardContent>
                  </Card>
                )}
              </div>
            )}

            {/* Analytics Section */}
            {activeTab === "analytics" && (
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Revenue Analytics</CardTitle>
                    <CardDescription>Monthly revenue trends over 6 months</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={350}>
                      <BarChart data={revenueData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                        <XAxis dataKey="month" stroke="#6B7280" />
                        <YAxis stroke="#6B7280" />
                        <Tooltip />
                        <Bar dataKey="revenue" fill="#023E73" radius={[8, 8, 0, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle>Geographic Distribution</CardTitle>
                      <CardDescription>Members by country</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {geographicData.map((item, index) => (
                          <div key={index} className="space-y-2">
                            <div className="flex items-center justify-between text-sm">
                              <span className="font-medium">{item.country}</span>
                              <span className="text-muted-foreground">{item.members} members</span>
                            </div>
                            <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-dojo-navy rounded-full"
                                style={{ width: `${(item.members / 98) * 100}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Retention Metrics</CardTitle>
                      <CardDescription>Member retention over time</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-6">
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">Overall Retention</span>
                            <span className="text-2xl font-bold text-dojo-navy">94%</span>
                          </div>
                          <div className="w-full h-4 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-green rounded-full" style={{ width: "94%" }} />
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">3-Month Retention</span>
                            <span className="text-2xl font-bold text-dojo-navy">89%</span>
                          </div>
                          <div className="w-full h-4 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-dojo-green rounded-full" style={{ width: "89%" }} />
                          </div>
                        </div>
                        <div>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-medium">6-Month Retention</span>
                            <span className="text-2xl font-bold text-dojo-navy">82%</span>
                          </div>
                          <div className="w-full h-4 bg-gray-100 rounded-full overflow-hidden">
                            <div className="h-full bg-dojo-green/80 rounded-full" style={{ width: "82%" }} />
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}

            {/* Content Management Section */}
            {activeTab === "content" && (
              <div className="space-y-6">
                <Tabs defaultValue="resources" className="w-full">
                  <TabsList>
                    <TabsTrigger value="resources">Resources</TabsTrigger>
                    <TabsTrigger value="articles">Articles</TabsTrigger>
                    <TabsTrigger value="videos">Videos</TabsTrigger>
                  </TabsList>
                  <TabsContent value="resources" className="space-y-6 mt-6">
                    <Card>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle>Training Resources</CardTitle>
                            <CardDescription>Manage training materials and documents</CardDescription>
                          </div>
                          <Button>
                            <Plus className="w-4 h-4 mr-2" />
                            Add Resource
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-muted-foreground">Resource management interface would go here</p>
                      </CardContent>
                    </Card>
                  </TabsContent>
                  <TabsContent value="articles" className="space-y-6 mt-6">
                    <Card>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle>Blog Articles</CardTitle>
                            <CardDescription>Manage blog posts and announcements</CardDescription>
                          </div>
                          <Button>
                            <Plus className="w-4 h-4 mr-2" />
                            New Article
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-muted-foreground">Article management interface would go here</p>
                      </CardContent>
                    </Card>
                  </TabsContent>
                  <TabsContent value="videos" className="space-y-6 mt-6">
                    <Card>
                      <CardHeader>
                        <div className="flex items-center justify-between">
                          <div>
                            <CardTitle>Video Library</CardTitle>
                            <CardDescription>Manage training videos and recordings</CardDescription>
                          </div>
                          <Button>
                            <Plus className="w-4 h-4 mr-2" />
                            Upload Video
                          </Button>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-muted-foreground">Video management interface would go here</p>
                      </CardContent>
                    </Card>
                  </TabsContent>
                </Tabs>
              </div>
            )}

            {/* Settings Section */}
            {activeTab === "settings" && (
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Organization Settings</CardTitle>
                    <CardDescription>Update your organization information</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="org-name">Organization Name</Label>
                      <Input id="org-name" defaultValue="World Wide Martial Arts Association" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="org-email">Contact Email</Label>
                      <Input id="org-email" type="email" defaultValue="contact@wwmaa.org" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="org-phone">Phone Number</Label>
                      <Input id="org-phone" defaultValue="+1 (555) 123-4567" />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="org-address">Address</Label>
                      <Textarea id="org-address" defaultValue="123 Martial Arts Way, Training City, TC 12345" />
                    </div>
                    <Button>Save Changes</Button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Membership Tier Management</CardTitle>
                    <CardDescription>Configure membership tiers and pricing</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {tierDistributionData.map((tier) => (
                        <div
                          key={tier.name}
                          className="flex items-center justify-between p-4 border rounded-lg"
                        >
                          <div>
                            <h4 className="font-semibold">{tier.name}</h4>
                            <p className="text-sm text-muted-foreground">
                              {tier.value} active members
                            </p>
                          </div>
                          <Button variant="outline" onClick={() => setIsEditTierOpen(true)}>
                            <Edit className="w-4 h-4 mr-2" />
                            Edit
                          </Button>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Email Templates</CardTitle>
                    <CardDescription>Customize email templates for notifications</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <span className="text-sm font-medium">Welcome Email</span>
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4 mr-2" />
                        Edit
                      </Button>
                    </div>
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <span className="text-sm font-medium">Payment Receipt</span>
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4 mr-2" />
                        Edit
                      </Button>
                    </div>
                    <div className="flex items-center justify-between p-3 border rounded-lg">
                      <span className="text-sm font-medium">Event Registration</span>
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4 mr-2" />
                        Edit
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Payment Gateway Settings</CardTitle>
                    <CardDescription>Configure payment processing (Mockup)</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Stripe Integration</p>
                        <p className="text-sm text-muted-foreground">Accept credit card payments</p>
                      </div>
                      <Switch defaultChecked />
                    </div>
                    <Separator />
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">PayPal Integration</p>
                        <p className="text-sm text-muted-foreground">Accept PayPal payments</p>
                      </div>
                      <Switch />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>User Roles & Permissions</CardTitle>
                    <CardDescription>Manage administrative access levels</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {["Super Admin", "Admin", "Board Member", "Instructor", "Member"].map((role) => (
                        <div key={role} className="flex items-center justify-between p-3 border rounded-lg">
                          <span className="text-sm font-medium">{role}</span>
                          <Button variant="outline" size="sm">
                            Configure
                          </Button>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Member Dialog */}
      <Dialog open={isAddMemberOpen} onOpenChange={setIsAddMemberOpen}>
        <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Add New Member</DialogTitle>
            <DialogDescription>
              Create a new member account with user credentials
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="add-first-name">First Name *</Label>
                <Input
                  id="add-first-name"
                  placeholder="John"
                  value={memberFormData.first_name}
                  onChange={(e) => setMemberFormData(prev => ({ ...prev, first_name: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="add-last-name">Last Name *</Label>
                <Input
                  id="add-last-name"
                  placeholder="Smith"
                  value={memberFormData.last_name}
                  onChange={(e) => setMemberFormData(prev => ({ ...prev, last_name: e.target.value }))}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="add-email">Email *</Label>
              <Input
                id="add-email"
                type="email"
                placeholder="john.smith@example.com"
                value={memberFormData.email}
                onChange={(e) => setMemberFormData(prev => ({ ...prev, email: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="add-password">Password *</Label>
              <Input
                id="add-password"
                type="password"
                placeholder="Min. 8 characters"
                value={memberFormData.password}
                onChange={(e) => setMemberFormData(prev => ({ ...prev, password: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="add-phone">Phone</Label>
              <Input
                id="add-phone"
                type="tel"
                placeholder="+1 (555) 123-4567"
                value={memberFormData.phone}
                onChange={(e) => setMemberFormData(prev => ({ ...prev, phone: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="add-role">Role</Label>
              <Select
                value={memberFormData.role}
                onValueChange={(value) => setMemberFormData(prev => ({ ...prev, role: value }))}
              >
                <SelectTrigger id="add-role">
                  <SelectValue placeholder="Select role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="member">Member</SelectItem>
                  <SelectItem value="instructor">Instructor</SelectItem>
                  <SelectItem value="board_member">Board Member</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                id="add-is-active"
                checked={memberFormData.is_active}
                onCheckedChange={(checked) => setMemberFormData(prev => ({ ...prev, is_active: checked }))}
              />
              <Label htmlFor="add-is-active">Active Account</Label>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsAddMemberOpen(false);
                setMemberFormData({
                  email: "",
                  first_name: "",
                  last_name: "",
                  password: "",
                  role: "member",
                  is_active: true,
                  phone: "",
                });
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleAddMember} disabled={memberActionLoading}>
              {memberActionLoading ? "Creating..." : "Create Member"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Member Dialog */}
      <Dialog open={isEditMemberOpen} onOpenChange={setIsEditMemberOpen}>
        <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Member</DialogTitle>
            <DialogDescription>
              Update member information and account settings
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="edit-first-name">First Name</Label>
                <Input
                  id="edit-first-name"
                  placeholder="John"
                  value={memberFormData.first_name}
                  onChange={(e) => setMemberFormData(prev => ({ ...prev, first_name: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-last-name">Last Name</Label>
                <Input
                  id="edit-last-name"
                  placeholder="Smith"
                  value={memberFormData.last_name}
                  onChange={(e) => setMemberFormData(prev => ({ ...prev, last_name: e.target.value }))}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-email">Email</Label>
              <Input
                id="edit-email"
                type="email"
                placeholder="john.smith@example.com"
                value={memberFormData.email}
                onChange={(e) => setMemberFormData(prev => ({ ...prev, email: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-password">New Password (optional)</Label>
              <Input
                id="edit-password"
                type="password"
                placeholder="Leave blank to keep current password"
                value={memberFormData.password}
                onChange={(e) => setMemberFormData(prev => ({ ...prev, password: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-phone">Phone</Label>
              <Input
                id="edit-phone"
                type="tel"
                placeholder="+1 (555) 123-4567"
                value={memberFormData.phone}
                onChange={(e) => setMemberFormData(prev => ({ ...prev, phone: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit-role">Role</Label>
              <Select
                value={memberFormData.role}
                onValueChange={(value) => setMemberFormData(prev => ({ ...prev, role: value }))}
              >
                <SelectTrigger id="edit-role">
                  <SelectValue placeholder="Select role" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="member">Member</SelectItem>
                  <SelectItem value="instructor">Instructor</SelectItem>
                  <SelectItem value="board_member">Board Member</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Switch
                id="edit-is-active"
                checked={memberFormData.is_active}
                onCheckedChange={(checked) => setMemberFormData(prev => ({ ...prev, is_active: checked }))}
              />
              <Label htmlFor="edit-is-active">Active Account</Label>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsEditMemberOpen(false);
                setCurrentMember(null);
                setMemberFormData({
                  email: "",
                  first_name: "",
                  last_name: "",
                  password: "",
                  role: "member",
                  is_active: true,
                  phone: "",
                });
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleEditMember} disabled={memberActionLoading}>
              {memberActionLoading ? "Updating..." : "Update Member"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Member Confirmation Dialog */}
      <Dialog open={isDeleteMemberOpen} onOpenChange={setIsDeleteMemberOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Delete Member</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this member? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          {currentMember && (
            <div className="py-4">
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-500">Name:</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {currentMember.first_name} {currentMember.last_name}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-500">Email:</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {currentMember.email}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-500">Role:</span>
                  <span className="text-sm font-semibold text-gray-900 capitalize">
                    {currentMember.role}
                  </span>
                </div>
              </div>
              <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-800 font-medium">
                  Warning: This will permanently delete the member account and all associated data.
                </p>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsDeleteMemberOpen(false);
                setCurrentMember(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteMember}
              disabled={memberActionLoading}
            >
              {memberActionLoading ? "Deleting..." : "Delete Member"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Instructor Dialog */}
      <Dialog open={isAddInstructorOpen} onOpenChange={setIsAddInstructorOpen}>
        <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Add New Instructor</DialogTitle>
            <DialogDescription>
              Add a new instructor to your team
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="instructor-name">Full Name</Label>
              <Input id="instructor-name" placeholder="Sensei Name" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="credentials">Credentials</Label>
              <Input id="credentials" placeholder="5th Dan Black Belt" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="bio">Bio</Label>
              <Textarea id="bio" placeholder="Instructor biography..." />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddInstructorOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => setIsAddInstructorOpen(false)}>
              Add Instructor
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Event Dialog */}
      <Dialog open={isAddEventOpen} onOpenChange={setIsAddEventOpen}>
        <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Event</DialogTitle>
            <DialogDescription>
              Add a new event or training session
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="event-title">Event Title *</Label>
              <Input
                id="event-title"
                placeholder="Summer Training Camp"
                value={eventFormData.title}
                onChange={(e) => setEventFormData(prev => ({ ...prev, title: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="event-description">Description</Label>
              <Textarea
                id="event-description"
                placeholder="Event description..."
                value={eventFormData.description}
                onChange={(e) => setEventFormData(prev => ({ ...prev, description: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="event-type">Event Type *</Label>
              <Select
                value={eventFormData.event_type}
                onValueChange={(value) => setEventFormData(prev => ({ ...prev, event_type: value as any }))}
              >
                <SelectTrigger id="event-type">
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="live_training">Live Training</SelectItem>
                  <SelectItem value="seminar">Seminar</SelectItem>
                  <SelectItem value="tournament">Tournament</SelectItem>
                  <SelectItem value="certification">Certification</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="start-date">Start Date *</Label>
                <Input
                  id="start-date"
                  type="datetime-local"
                  value={eventFormData.start_date}
                  onChange={(e) => setEventFormData(prev => ({ ...prev, start_date: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="end-date">End Date *</Label>
                <Input
                  id="end-date"
                  type="datetime-local"
                  value={eventFormData.end_date}
                  onChange={(e) => setEventFormData(prev => ({ ...prev, end_date: e.target.value }))}
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="location">Location</Label>
              <Input
                id="location"
                placeholder="123 Main St or Online"
                value={eventFormData.location}
                onChange={(e) => setEventFormData(prev => ({ ...prev, location: e.target.value }))}
              />
            </div>
            <div className="flex items-center gap-2">
              <Switch
                id="is-online"
                checked={eventFormData.is_online}
                onCheckedChange={(checked) => setEventFormData(prev => ({ ...prev, is_online: checked }))}
              />
              <Label htmlFor="is-online">Online Event</Label>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="capacity">Capacity</Label>
                <Input
                  id="capacity"
                  type="number"
                  placeholder="50"
                  value={eventFormData.capacity}
                  onChange={(e) => setEventFormData(prev => ({ ...prev, capacity: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="price">Price ($)</Label>
                <Input
                  id="price"
                  type="number"
                  placeholder="0.00"
                  step="0.01"
                  value={eventFormData.price}
                  onChange={(e) => setEventFormData(prev => ({ ...prev, price: e.target.value }))}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setIsAddEventOpen(false);
                setEventFormData({
                  title: "",
                  description: "",
                  event_type: "seminar",
                  start_date: "",
                  end_date: "",
                  location: "",
                  is_online: false,
                  capacity: "",
                  price: "",
                });
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleCreateEvent} disabled={loading}>
              {loading ? "Creating..." : "Create Event"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Tier Dialog */}
      <Dialog open={isEditTierOpen} onOpenChange={setIsEditTierOpen}>
        <DialogContent className="sm:max-w-[500px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Membership Tier</DialogTitle>
            <DialogDescription>
              Update pricing and benefits
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="tier-name">Tier Name</Label>
              <Input id="tier-name" defaultValue="Premium" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tier-price">Monthly Price (USD)</Label>
              <Input id="tier-price" type="number" defaultValue="29.99" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tier-benefits">Benefits (one per line)</Label>
              <Textarea
                id="tier-benefits"
                defaultValue="Access to all training videos&#10;Monthly live sessions&#10;Priority event registration"
                rows={5}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsEditTierOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => setIsEditTierOpen(false)}>
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
