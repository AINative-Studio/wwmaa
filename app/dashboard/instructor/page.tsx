'use client';

import { useState } from 'react';
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  Calendar,
  BookOpen,
  Plus,
  Search,
  Filter,
  Download,
  Mail,
  FileText,
  Edit,
  Eye,
  ChevronRight,
  Award,
  Bell,
  TrendingUp,
  Clock,
  MapPin,
  MoreVertical,
  CheckCircle2,
  XCircle,
  UserPlus,
  FileDown
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

// Mock data
const instructorData = {
  name: "Sensei Michael Chen",
  credentials: "4th Dan Black Belt, Certified Instructor",
  totalStudents: 48,
  activeClasses: 6,
  upcomingSessions: 12,
  certificationLevel: "Master Instructor"
};

const announcements = [
  { id: 1, title: "Belt Testing Schedule", date: "Oct 15, 2025", urgent: true },
  { id: 2, title: "New Curriculum Guidelines", date: "Oct 10, 2025", urgent: false },
  { id: 3, title: "Instructor Meeting Next Week", date: "Oct 8, 2025", urgent: false }
];

const classes = [
  {
    id: 1,
    name: "Advanced Kata",
    dayTime: "Mon/Wed 6:00 PM",
    location: "Dojo A",
    students: 12,
    level: "Black Belt",
    color: "bg-gradient-to-br from-gray-900 to-gray-700"
  },
  {
    id: 2,
    name: "Intermediate Sparring",
    dayTime: "Tue/Thu 7:00 PM",
    location: "Dojo B",
    students: 15,
    level: "Brown Belt",
    color: "bg-gradient-to-br from-amber-800 to-amber-600"
  },
  {
    id: 3,
    name: "Youth Fundamentals",
    dayTime: "Mon/Wed 4:30 PM",
    location: "Dojo A",
    students: 10,
    level: "White-Yellow",
    color: "bg-gradient-to-br from-yellow-500 to-yellow-400"
  },
  {
    id: 4,
    name: "Competition Team",
    dayTime: "Sat 10:00 AM",
    location: "Dojo A",
    students: 8,
    level: "Mixed",
    color: "bg-gradient-to-br from-purple-600 to-purple-500"
  },
  {
    id: 5,
    name: "Beginner Basics",
    dayTime: "Tue/Thu 5:00 PM",
    location: "Dojo B",
    students: 18,
    level: "White Belt",
    color: "bg-gradient-to-br from-gray-200 to-gray-100"
  },
  {
    id: 6,
    name: "Women's Self Defense",
    dayTime: "Fri 6:00 PM",
    location: "Dojo C",
    students: 14,
    level: "All Levels",
    color: "bg-gradient-to-br from-pink-600 to-pink-500"
  }
];

const students = [
  {
    id: 1,
    name: "Sarah Johnson",
    belt: "Brown Belt",
    beltColor: "amber-700",
    joinDate: "Jan 2023",
    attendance: 95,
    lastSession: "Oct 2, 2025",
    status: "active"
  },
  {
    id: 2,
    name: "David Kim",
    belt: "Black Belt",
    beltColor: "gray-900",
    joinDate: "Mar 2021",
    attendance: 92,
    lastSession: "Oct 2, 2025",
    status: "active"
  },
  {
    id: 3,
    name: "Emma Rodriguez",
    belt: "Blue Belt",
    beltColor: "blue-600",
    joinDate: "Sep 2023",
    attendance: 88,
    lastSession: "Oct 1, 2025",
    status: "active"
  },
  {
    id: 4,
    name: "Michael Lee",
    belt: "Green Belt",
    beltColor: "green-600",
    joinDate: "Jun 2024",
    attendance: 90,
    lastSession: "Oct 2, 2025",
    status: "active"
  },
  {
    id: 5,
    name: "Jessica Taylor",
    belt: "Purple Belt",
    beltColor: "purple-600",
    joinDate: "Feb 2024",
    attendance: 85,
    lastSession: "Sep 30, 2025",
    status: "active"
  },
  {
    id: 6,
    name: "Ryan Chen",
    belt: "White Belt",
    beltColor: "gray-300",
    joinDate: "Aug 2025",
    attendance: 78,
    lastSession: "Oct 1, 2025",
    status: "active"
  },
  {
    id: 7,
    name: "Ashley Brown",
    belt: "Yellow Belt",
    beltColor: "yellow-500",
    joinDate: "May 2025",
    attendance: 82,
    lastSession: "Oct 2, 2025",
    status: "active"
  },
  {
    id: 8,
    name: "James Wilson",
    belt: "Orange Belt",
    beltColor: "orange-500",
    joinDate: "Apr 2025",
    attendance: 87,
    lastSession: "Sep 28, 2025",
    status: "inactive"
  }
];

const upcomingSessions = [
  { id: 1, class: "Advanced Kata", date: "Oct 5, 2025", time: "6:00 PM", location: "Dojo A" },
  { id: 2, class: "Beginner Basics", date: "Oct 5, 2025", time: "5:00 PM", location: "Dojo B" },
  { id: 3, class: "Advanced Kata", date: "Oct 7, 2025", time: "6:00 PM", location: "Dojo A" },
  { id: 4, class: "Intermediate Sparring", date: "Oct 7, 2025", time: "7:00 PM", location: "Dojo B" }
];

const resources = [
  { id: 1, category: "Curriculum", title: "White to Yellow Belt Requirements", type: "PDF" },
  { id: 2, category: "Curriculum", title: "Advanced Kata Forms Guide", type: "PDF" },
  { id: 3, category: "Forms", title: "Student Evaluation Template", type: "DOCX" },
  { id: 4, category: "Forms", title: "Belt Promotion Recommendation", type: "PDF" },
  { id: 5, category: "Teaching", title: "Class Management Best Practices", type: "PDF" },
  { id: 6, category: "Teaching", title: "Injury Prevention Guidelines", type: "PDF" }
];

export default function InstructorDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');

  const filteredStudents = students.filter(student => {
    const matchesSearch = student.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         student.belt.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = selectedFilter === 'all' ||
                         (selectedFilter === 'active' && student.status === 'active') ||
                         (selectedFilter === 'inactive' && student.status === 'inactive');
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-muted">
      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 min-h-screen bg-card border-r border-border sticky top-0">
          <div className="p-6">
            <h2 className="text-xl font-bold text-[var(--dojo-navy)] mb-1">Instructor Portal</h2>
            <p className="text-sm text-gray-500">Teaching Dashboard</p>
          </div>

          <nav className="px-3 space-y-1">
            <button
              onClick={() => setActiveTab('overview')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'overview'
                  ? 'bg-[var(--dojo-navy)] text-white'
                  : 'text-gray-700 hover:bg-muted'
              }`}
            >
              <LayoutDashboard className="w-4 h-4" />
              Overview
            </button>

            <button
              onClick={() => setActiveTab('classes')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'classes'
                  ? 'bg-[var(--dojo-navy)] text-white'
                  : 'text-gray-700 hover:bg-muted'
              }`}
            >
              <GraduationCap className="w-4 h-4" />
              My Classes
            </button>

            <button
              onClick={() => setActiveTab('students')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'students'
                  ? 'bg-[var(--dojo-navy)] text-white'
                  : 'text-gray-700 hover:bg-muted'
              }`}
            >
              <Users className="w-4 h-4" />
              Students
            </button>

            <button
              onClick={() => setActiveTab('schedule')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'schedule'
                  ? 'bg-[var(--dojo-navy)] text-white'
                  : 'text-gray-700 hover:bg-muted'
              }`}
            >
              <Calendar className="w-4 h-4" />
              Schedule
            </button>

            <button
              onClick={() => setActiveTab('resources')}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'resources'
                  ? 'bg-[var(--dojo-navy)] text-white'
                  : 'text-gray-700 hover:bg-muted'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              Resources
            </button>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-8">
              {/* Welcome Banner */}
              <div className="bg-gradient-to-r from-[var(--dojo-navy)] to-[var(--dojo-green)] rounded-2xl p-8 text-white shadow-lg">
                <div className="flex items-start justify-between">
                  <div>
                    <h1 className="text-3xl font-bold mb-2">{instructorData.name}</h1>
                    <p className="text-white/90 flex items-center gap-2">
                      <Award className="w-4 h-4" />
                      {instructorData.credentials}
                    </p>
                  </div>
                  <Badge className="bg-white/20 text-white border-white/30">
                    {instructorData.certificationLevel}
                  </Badge>
                </div>
              </div>

              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <Card className="shadow-hover">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Total Students</p>
                        <p className="text-3xl font-bold text-[var(--dojo-navy)]">{instructorData.totalStudents}</p>
                      </div>
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
                        <Users className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <div className="mt-3 flex items-center gap-1 text-sm text-green-600">
                      <TrendingUp className="w-3 h-3" />
                      <span>+8% from last month</span>
                    </div>
                  </CardContent>
                </Card>

                <Card className="shadow-hover">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Active Classes</p>
                        <p className="text-3xl font-bold text-[var(--dojo-green)]">{instructorData.activeClasses}</p>
                      </div>
                      <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-xl flex items-center justify-center">
                        <GraduationCap className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <div className="mt-3 flex items-center gap-1 text-sm text-gray-500">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>All sessions scheduled</span>
                    </div>
                  </CardContent>
                </Card>

                <Card className="shadow-hover">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Upcoming Sessions</p>
                        <p className="text-3xl font-bold text-[var(--dojo-orange)]">{instructorData.upcomingSessions}</p>
                      </div>
                      <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl flex items-center justify-center">
                        <Calendar className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <div className="mt-3 flex items-center gap-1 text-sm text-gray-500">
                      <Clock className="w-3 h-3" />
                      <span>Next in 2 hours</span>
                    </div>
                  </CardContent>
                </Card>

                <Card className="shadow-hover">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Certification Level</p>
                        <p className="text-xl font-bold text-purple-600">Master</p>
                      </div>
                      <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center">
                        <Award className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <div className="mt-3 flex items-center gap-1 text-sm text-gray-500">
                      <FileText className="w-3 h-3" />
                      <span>Since 2018</span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Announcements & Quick Actions */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Announcements */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="flex items-center gap-2">
                        <Bell className="w-5 h-5" />
                        Announcements
                      </CardTitle>
                      <Button variant="ghost" size="sm">View All</Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {announcements.map(announcement => (
                        <div
                          key={announcement.id}
                          className="p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors cursor-pointer"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <h4 className="font-semibold text-sm">{announcement.title}</h4>
                                {announcement.urgent && (
                                  <Badge variant="destructive" className="text-xs">Urgent</Badge>
                                )}
                              </div>
                              <p className="text-xs text-gray-500">{announcement.date}</p>
                            </div>
                            <ChevronRight className="w-4 h-4 text-gray-400" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Quick Actions */}
                <Card>
                  <CardHeader>
                    <CardTitle>Quick Actions</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-3">
                      <Button className="h-auto py-4 flex-col gap-2 bg-[var(--dojo-navy)] hover:bg-[var(--dojo-navy)]/90">
                        <Plus className="w-5 h-5" />
                        <span className="text-sm">Add Class</span>
                      </Button>
                      <Button variant="outline" className="h-auto py-4 flex-col gap-2">
                        <Eye className="w-5 h-5" />
                        <span className="text-sm">View Roster</span>
                      </Button>
                      <Button variant="outline" className="h-auto py-4 flex-col gap-2">
                        <Award className="w-5 h-5" />
                        <span className="text-sm">Promotion Request</span>
                      </Button>
                      <Button variant="outline" className="h-auto py-4 flex-col gap-2">
                        <FileText className="w-5 h-5" />
                        <span className="text-sm">Session Notes</span>
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {/* My Classes Tab */}
          {activeTab === 'classes' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-[var(--dojo-navy)]">My Classes</h1>
                  <p className="text-gray-500 mt-1">Manage your teaching schedule and class rosters</p>
                </div>
                <Button className="bg-[var(--dojo-navy)] hover:bg-[var(--dojo-navy)]/90">
                  <Plus className="w-4 h-4 mr-2" />
                  Add New Class
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {classes.map(classItem => (
                  <Card key={classItem.id} className="shadow-hover overflow-hidden">
                    <div className={`h-2 ${classItem.color}`} />
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div>
                          <CardTitle className="text-lg">{classItem.name}</CardTitle>
                          <CardDescription className="mt-1">{classItem.level}</CardDescription>
                        </div>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Clock className="w-4 h-4" />
                          {classItem.dayTime}
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <MapPin className="w-4 h-4" />
                          {classItem.location}
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600">
                          <Users className="w-4 h-4" />
                          {classItem.students} students enrolled
                        </div>

                        <div className="pt-3 flex gap-2">
                          <Button variant="outline" size="sm" className="flex-1">
                            <Eye className="w-3 h-3 mr-1" />
                            Roster
                          </Button>
                          <Button variant="outline" size="sm" className="flex-1">
                            <Edit className="w-3 h-3 mr-1" />
                            Edit
                          </Button>
                        </div>
                        <Button variant="ghost" size="sm" className="w-full">
                          <FileText className="w-3 h-3 mr-1" />
                          Add Session Notes
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Students Tab */}
          {activeTab === 'students' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-[var(--dojo-navy)]">Student Roster</h1>
                  <p className="text-gray-500 mt-1">Manage and track student progress</p>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline">
                    <Mail className="w-4 h-4 mr-2" />
                    Send Message
                  </Button>
                  <Button variant="outline">
                    <Download className="w-4 h-4 mr-2" />
                    Export
                  </Button>
                </div>
              </div>

              <Card>
                <CardHeader>
                  <div className="flex flex-col sm:flex-row gap-4">
                    <div className="relative flex-1">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <Input
                        placeholder="Search students by name or belt rank..."
                        className="pl-10"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                      />
                    </div>
                    <div className="flex gap-2">
                      <select
                        className="px-4 py-2 border border-border rounded-md text-sm bg-background"
                        value={selectedFilter}
                        onChange={(e) => setSelectedFilter(e.target.value)}
                      >
                        <option value="all">All Students</option>
                        <option value="active">Active</option>
                        <option value="inactive">Inactive</option>
                      </select>
                      <Button variant="outline" size="icon">
                        <Filter className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Name</TableHead>
                        <TableHead>Belt Rank</TableHead>
                        <TableHead>Join Date</TableHead>
                        <TableHead>Attendance</TableHead>
                        <TableHead>Last Session</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredStudents.map(student => (
                        <TableRow key={student.id}>
                          <TableCell className="font-medium">{student.name}</TableCell>
                          <TableCell>
                            <Badge className={`bg-${student.beltColor} text-white border-0`}>
                              {student.belt}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-gray-500">{student.joinDate}</TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <div className="flex-1 max-w-[100px] h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-[var(--dojo-green)] rounded-full"
                                  style={{ width: `${student.attendance}%` }}
                                />
                              </div>
                              <span className="text-sm font-medium">{student.attendance}%</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-gray-500">{student.lastSession}</TableCell>
                          <TableCell>
                            {student.status === 'active' ? (
                              <Badge className="bg-green-100 text-green-700 border-0">
                                <CheckCircle2 className="w-3 h-3 mr-1" />
                                Active
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-gray-500">
                                <XCircle className="w-3 h-3 mr-1" />
                                Inactive
                              </Badge>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex items-center justify-end gap-2">
                              <Button variant="ghost" size="sm">
                                <Eye className="w-3 h-3 mr-1" />
                                View
                              </Button>
                              <Button variant="ghost" size="sm">
                                <FileText className="w-3 h-3 mr-1" />
                                Notes
                              </Button>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Schedule Tab */}
          {activeTab === 'schedule' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-[var(--dojo-navy)]">Teaching Schedule</h1>
                  <p className="text-gray-500 mt-1">View and manage your upcoming sessions</p>
                </div>
                <Button className="bg-[var(--dojo-navy)] hover:bg-[var(--dojo-navy)]/90">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Session
                </Button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Calendar placeholder */}
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle>Calendar View</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-8 text-center border-2 border-dashed border-gray-300">
                      <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                      <p className="text-gray-500 font-medium">Interactive Calendar</p>
                      <p className="text-sm text-gray-400 mt-1">Visual monthly schedule view would appear here</p>
                    </div>
                  </CardContent>
                </Card>

                {/* Upcoming Sessions */}
                <Card>
                  <CardHeader>
                    <CardTitle>Upcoming Sessions</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {upcomingSessions.map(session => (
                        <div
                          key={session.id}
                          className="p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors"
                        >
                          <h4 className="font-semibold text-sm mb-2">{session.class}</h4>
                          <div className="space-y-1 text-xs text-gray-500">
                            <div className="flex items-center gap-2">
                              <Calendar className="w-3 h-3" />
                              {session.date}
                            </div>
                            <div className="flex items-center gap-2">
                              <Clock className="w-3 h-3" />
                              {session.time}
                            </div>
                            <div className="flex items-center gap-2">
                              <MapPin className="w-3 h-3" />
                              {session.location}
                            </div>
                          </div>
                          <Button variant="ghost" size="sm" className="w-full mt-3">
                            <FileText className="w-3 h-3 mr-1" />
                            Add Notes
                          </Button>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Past Session Notes */}
              <Card>
                <CardHeader>
                  <CardTitle>Recent Session Notes</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="p-4 rounded-lg border border-border">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="font-semibold">Advanced Kata - Oct 2, 2025</h4>
                          <p className="text-sm text-gray-500">6:00 PM - Dojo A</p>
                        </div>
                        <Button variant="ghost" size="sm">
                          <Edit className="w-3 h-3 mr-1" />
                          Edit
                        </Button>
                      </div>
                      <p className="text-sm text-gray-600">
                        Focused on Bassai Dai kata. Students showing good progress with timing and power.
                        Need to work on hip rotation in next session.
                      </p>
                    </div>
                    <div className="p-4 rounded-lg border border-border">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="font-semibold">Beginner Basics - Oct 1, 2025</h4>
                          <p className="text-sm text-gray-500">5:00 PM - Dojo B</p>
                        </div>
                        <Button variant="ghost" size="sm">
                          <Edit className="w-3 h-3 mr-1" />
                          Edit
                        </Button>
                      </div>
                      <p className="text-sm text-gray-600">
                        Introduced basic blocks and stances. New students need extra attention on front stance positioning.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Resources Tab */}
          {activeTab === 'resources' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-3xl font-bold text-[var(--dojo-navy)]">Teaching Resources</h1>
                  <p className="text-gray-500 mt-1">Access curriculum materials and teaching guides</p>
                </div>
                <Button variant="outline">
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Resource
                </Button>
              </div>

              <Tabs defaultValue="all" className="w-full">
                <TabsList>
                  <TabsTrigger value="all">All Resources</TabsTrigger>
                  <TabsTrigger value="curriculum">Curriculum</TabsTrigger>
                  <TabsTrigger value="forms">Forms</TabsTrigger>
                  <TabsTrigger value="teaching">Teaching Materials</TabsTrigger>
                </TabsList>

                <TabsContent value="all" className="mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {resources.map(resource => (
                      <Card key={resource.id} className="shadow-hover">
                        <CardContent className="p-6">
                          <div className="flex items-start gap-4">
                            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                              <FileText className="w-6 h-6 text-white" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <Badge variant="outline" className="mb-2 text-xs">
                                {resource.category}
                              </Badge>
                              <h4 className="font-semibold text-sm mb-1 line-clamp-2">
                                {resource.title}
                              </h4>
                              <p className="text-xs text-gray-500">{resource.type} File</p>
                              <Button variant="ghost" size="sm" className="mt-3 w-full">
                                <FileDown className="w-3 h-3 mr-1" />
                                Download
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="curriculum" className="mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {resources.filter(r => r.category === 'Curriculum').map(resource => (
                      <Card key={resource.id} className="shadow-hover">
                        <CardContent className="p-6">
                          <div className="flex items-start gap-4">
                            <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-green-600 rounded-lg flex items-center justify-center flex-shrink-0">
                              <BookOpen className="w-6 h-6 text-white" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="font-semibold text-sm mb-1 line-clamp-2">
                                {resource.title}
                              </h4>
                              <p className="text-xs text-gray-500">{resource.type} File</p>
                              <Button variant="ghost" size="sm" className="mt-3 w-full">
                                <FileDown className="w-3 h-3 mr-1" />
                                Download
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="forms" className="mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {resources.filter(r => r.category === 'Forms').map(resource => (
                      <Card key={resource.id} className="shadow-hover">
                        <CardContent className="p-6">
                          <div className="flex items-start gap-4">
                            <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg flex items-center justify-center flex-shrink-0">
                              <FileText className="w-6 h-6 text-white" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="font-semibold text-sm mb-1 line-clamp-2">
                                {resource.title}
                              </h4>
                              <p className="text-xs text-gray-500">{resource.type} File</p>
                              <Button variant="ghost" size="sm" className="mt-3 w-full">
                                <FileDown className="w-3 h-3 mr-1" />
                                Download
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="teaching" className="mt-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {resources.filter(r => r.category === 'Teaching').map(resource => (
                      <Card key={resource.id} className="shadow-hover">
                        <CardContent className="p-6">
                          <div className="flex items-start gap-4">
                            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                              <GraduationCap className="w-6 h-6 text-white" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <h4 className="font-semibold text-sm mb-1 line-clamp-2">
                                {resource.title}
                              </h4>
                              <p className="text-xs text-gray-500">{resource.type} File</p>
                              <Button variant="ghost" size="sm" className="mt-3 w-full">
                                <FileDown className="w-3 h-3 mr-1" />
                                Download
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </TabsContent>
              </Tabs>

              {/* Promotion Requirements Quick Reference */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Award className="w-5 h-5" />
                    Belt Promotion Requirements
                  </CardTitle>
                  <CardDescription>Quick reference guide for student evaluations</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-lg border border-border">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-3 h-3 rounded-full bg-yellow-500" />
                        <h4 className="font-semibold">White to Yellow Belt</h4>
                      </div>
                      <ul className="text-sm text-gray-600 space-y-1">
                        <li>• Basic stances (front, back, horse)</li>
                        <li>• Fundamental blocks and strikes</li>
                        <li>• First kata (Taikyoku Shodan)</li>
                        <li>• Minimum 3 months training</li>
                      </ul>
                    </div>
                    <div className="p-4 rounded-lg border border-border">
                      <div className="flex items-center gap-3 mb-3">
                        <div className="w-3 h-3 rounded-full bg-green-600" />
                        <h4 className="font-semibold">Green Belt Requirements</h4>
                      </div>
                      <ul className="text-sm text-gray-600 space-y-1">
                        <li>• Advanced kata (Heian Nidan, Sandan)</li>
                        <li>• Intermediate kumite techniques</li>
                        <li>• Self-defense applications</li>
                        <li>• Minimum 12 months total training</li>
                      </ul>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

// Missing icon import
function Upload({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" x2="12" y1="3" y2="15" />
    </svg>
  );
}
