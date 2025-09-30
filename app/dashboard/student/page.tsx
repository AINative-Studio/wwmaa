'use client';

import { useState } from 'react';
import {
  User,
  Calendar,
  CreditCard,
  BookOpen,
  LayoutDashboard,
  Menu,
  X,
  Award,
  Clock,
  CheckCircle2,
  XCircle,
  Download,
  Edit2,
  Save,
  Camera,
  Bell,
  MapPin,
  Phone,
  Mail,
  Shield,
  TrendingUp,
  Users,
  Trophy,
  GraduationCap,
  Filter,
  Search,
  ChevronRight,
  AlertCircle,
} from 'lucide-react';

type NavSection = 'overview' | 'profile' | 'events' | 'payments' | 'resources';
type EventTab = 'upcoming' | 'past' | 'all';
type EventFilter = 'all' | 'tournament' | 'seminar' | 'camp';

interface Event {
  id: string;
  title: string;
  type: 'tournament' | 'seminar' | 'camp';
  date: string;
  location: string;
  rsvpStatus: 'registered' | 'pending' | 'cancelled' | null;
}

interface Payment {
  id: string;
  date: string;
  description: string;
  amount: number;
  status: 'completed' | 'pending' | 'failed';
}

interface Activity {
  id: string;
  type: 'event' | 'payment' | 'profile';
  message: string;
  timestamp: string;
}

export default function StudentDashboard() {
  const [activeSection, setActiveSection] = useState<NavSection>('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [eventTab, setEventTab] = useState<EventTab>('upcoming');
  const [eventFilter, setEventFilter] = useState<EventFilter>('all');

  // Mock student data
  const student = {
    name: 'John Anderson',
    email: 'john.anderson@email.com',
    membershipTier: 'Gold Member',
    beltRank: '2nd Dan Black Belt',
    dojo: 'Tiger Dojo',
    phone: '+1 (555) 123-4567',
    membershipExpiry: '2025-12-31',
    emergencyContact: {
      name: 'Jane Anderson',
      relationship: 'Spouse',
      phone: '+1 (555) 987-6543',
    },
  };

  // Mock data
  const stats = {
    upcomingEvents: 3,
    paymentStatus: 'Active',
    membershipExpiry: 'Dec 31, 2025',
  };

  const activities: Activity[] = [
    {
      id: '1',
      type: 'event',
      message: 'Registered for Spring Championship 2025',
      timestamp: '2 hours ago',
    },
    {
      id: '2',
      type: 'payment',
      message: 'Membership payment processed successfully',
      timestamp: '1 day ago',
    },
    {
      id: '3',
      type: 'profile',
      message: 'Profile updated - Belt rank changed',
      timestamp: '3 days ago',
    },
  ];

  const upcomingEvents: Event[] = [
    {
      id: '1',
      title: 'Spring Championship 2025',
      type: 'tournament',
      date: '2025-10-15',
      location: 'Central Dojo, New York',
      rsvpStatus: 'registered',
    },
    {
      id: '2',
      title: 'Advanced Kata Seminar',
      type: 'seminar',
      date: '2025-10-22',
      location: 'Master Dojo, Boston',
      rsvpStatus: null,
    },
    {
      id: '3',
      title: 'Summer Training Camp',
      type: 'camp',
      date: '2025-11-05',
      location: 'Mountain Resort, Vermont',
      rsvpStatus: 'pending',
    },
  ];

  const pastEvents: Event[] = [
    {
      id: '4',
      title: 'Winter Tournament 2024',
      type: 'tournament',
      date: '2024-12-10',
      location: 'Regional Center',
      rsvpStatus: 'registered',
    },
  ];

  const payments: Payment[] = [
    {
      id: '1',
      date: '2025-09-01',
      description: 'Annual Membership - Gold Tier',
      amount: 299.99,
      status: 'completed',
    },
    {
      id: '2',
      date: '2025-08-15',
      description: 'Spring Championship Registration',
      amount: 75.00,
      status: 'completed',
    },
    {
      id: '3',
      date: '2025-07-01',
      description: 'Belt Promotion Test Fee',
      amount: 50.00,
      status: 'completed',
    },
  ];

  const navigation = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'profile', label: 'My Profile', icon: User },
    { id: 'events', label: 'Events', icon: Calendar },
    { id: 'payments', label: 'Payments', icon: CreditCard },
    { id: 'resources', label: 'Resources', icon: BookOpen },
  ];

  const filteredEvents = () => {
    let events = eventTab === 'upcoming' ? upcomingEvents : eventTab === 'past' ? pastEvents : [...upcomingEvents, ...pastEvents];
    if (eventFilter !== 'all') {
      events = events.filter((e) => e.type === eventFilter);
    }
    return events;
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      registered: 'bg-success/10 text-success border-success/20',
      pending: 'bg-accent/10 text-accent border-accent/20',
      cancelled: 'bg-danger/10 text-danger border-danger/20',
      completed: 'bg-success/10 text-success border-success/20',
      failed: 'bg-danger/10 text-danger border-danger/20',
      Active: 'bg-success/10 text-success border-success/20',
    };
    return styles[status as keyof typeof styles] || 'bg-muted text-fg border-border';
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'tournament':
        return Trophy;
      case 'seminar':
        return GraduationCap;
      case 'camp':
        return Users;
      default:
        return Calendar;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-bg via-white to-dojo-light/20">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-card border-b border-border shadow-sm">
        <div className="flex items-center justify-between px-4 py-4">
          <h1 className="font-display text-xl font-bold text-dojo-navy">Student Dashboard</h1>
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-2 rounded-lg hover:bg-muted transition-colors"
            aria-label="Toggle menu"
          >
            {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 h-full w-72 bg-card border-r border-border shadow-lg z-40 transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-full gradient-navy flex items-center justify-center text-white font-bold text-lg">
              {student.name.split(' ').map((n) => n[0]).join('')}
            </div>
            <div>
              <h2 className="font-display font-bold text-dojo-navy">{student.name}</h2>
              <p className="text-sm text-muted-foreground">{student.membershipTier}</p>
            </div>
          </div>
        </div>

        <nav className="p-4 space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveSection(item.id as NavSection);
                  setSidebarOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  isActive
                    ? 'bg-primary text-primary-fg shadow-md'
                    : 'hover:bg-muted text-fg'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
                {isActive && <ChevronRight className="w-4 h-4 ml-auto" />}
              </button>
            );
          })}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border bg-muted/30">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Bell className="w-4 h-4" />
            <span>3 new notifications</span>
          </div>
        </div>
      </aside>

      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <main className="lg:ml-72 pt-20 lg:pt-0 min-h-screen">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Overview Section */}
          {activeSection === 'overview' && (
            <div className="space-y-8">
              {/* Welcome Banner */}
              <div className="gradient-hero rounded-2xl shadow-glow p-8 text-white">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <div>
                    <h1 className="font-display text-3xl md:text-4xl font-bold mb-2">
                      Welcome back, {student.name.split(' ')[0]}!
                    </h1>
                    <p className="text-white/90 text-lg">
                      {student.beltRank} - {student.dojo}
                    </p>
                  </div>
                  <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm px-6 py-3 rounded-full border border-white/30">
                    <Award className="w-5 h-5" />
                    <span className="font-semibold">{student.membershipTier}</span>
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-card rounded-xl shadow-card p-6 border border-border hover:shadow-glow transition-shadow">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 rounded-lg gradient-navy flex items-center justify-center">
                      <Calendar className="w-6 h-6 text-white" />
                    </div>
                    <TrendingUp className="w-5 h-5 text-success" />
                  </div>
                  <div className="text-3xl font-bold text-dojo-navy mb-1">{stats.upcomingEvents}</div>
                  <div className="text-sm text-muted-foreground">Upcoming Events</div>
                </div>

                <div className="bg-card rounded-xl shadow-card p-6 border border-border hover:shadow-glow transition-shadow">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 rounded-lg gradient-green flex items-center justify-center">
                      <CheckCircle2 className="w-6 h-6 text-white" />
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(stats.paymentStatus)}`}>
                      {stats.paymentStatus}
                    </span>
                  </div>
                  <div className="text-3xl font-bold text-dojo-green mb-1">Active</div>
                  <div className="text-sm text-muted-foreground">Payment Status</div>
                </div>

                <div className="bg-card rounded-xl shadow-card p-6 border border-border hover:shadow-glow transition-shadow">
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 rounded-lg gradient-orange flex items-center justify-center">
                      <Clock className="w-6 h-6 text-white" />
                    </div>
                  </div>
                  <div className="text-2xl font-bold text-dojo-orange mb-1">{stats.membershipExpiry}</div>
                  <div className="text-sm text-muted-foreground">Membership Expiry</div>
                </div>
              </div>

              {/* Content Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Recent Activity */}
                <div className="lg:col-span-2 bg-card rounded-xl shadow-card p-6 border border-border">
                  <h2 className="font-display text-xl font-bold text-dojo-navy mb-6 flex items-center gap-2">
                    <Bell className="w-5 h-5" />
                    Recent Activity
                  </h2>
                  <div className="space-y-4">
                    {activities.map((activity) => (
                      <div
                        key={activity.id}
                        className="flex items-start gap-4 p-4 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                      >
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          activity.type === 'event' ? 'bg-primary/10 text-primary' :
                          activity.type === 'payment' ? 'bg-success/10 text-success' :
                          'bg-accent/10 text-accent'
                        }`}>
                          {activity.type === 'event' && <Calendar className="w-5 h-5" />}
                          {activity.type === 'payment' && <CreditCard className="w-5 h-5" />}
                          {activity.type === 'profile' && <User className="w-5 h-5" />}
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-fg">{activity.message}</p>
                          <p className="text-xs text-muted-foreground mt-1">{activity.timestamp}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="bg-card rounded-xl shadow-card p-6 border border-border">
                  <h2 className="font-display text-xl font-bold text-dojo-navy mb-6">Quick Actions</h2>
                  <div className="space-y-3">
                    <button
                      onClick={() => setActiveSection('profile')}
                      className="w-full flex items-center gap-3 p-3 rounded-lg bg-primary text-primary-fg hover:bg-primary/90 transition-colors"
                    >
                      <User className="w-5 h-5" />
                      <span className="font-medium">Update Profile</span>
                    </button>
                    <button
                      onClick={() => setActiveSection('payments')}
                      className="w-full flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-muted transition-colors"
                    >
                      <CreditCard className="w-5 h-5" />
                      <span className="font-medium">View Payments</span>
                    </button>
                    <button
                      onClick={() => setActiveSection('events')}
                      className="w-full flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-muted transition-colors"
                    >
                      <Calendar className="w-5 h-5" />
                      <span className="font-medium">Register for Event</span>
                    </button>
                    <button
                      onClick={() => setActiveSection('resources')}
                      className="w-full flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-muted transition-colors"
                    >
                      <BookOpen className="w-5 h-5" />
                      <span className="font-medium">Browse Resources</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Upcoming Events Preview */}
              <div className="bg-card rounded-xl shadow-card p-6 border border-border">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="font-display text-xl font-bold text-dojo-navy flex items-center gap-2">
                    <Calendar className="w-5 h-5" />
                    Upcoming Events
                  </h2>
                  <button
                    onClick={() => setActiveSection('events')}
                    className="text-sm text-primary hover:text-primary/80 font-medium flex items-center gap-1"
                  >
                    View All
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {upcomingEvents.map((event) => {
                    const EventIcon = getEventIcon(event.type);
                    return (
                      <div
                        key={event.id}
                        className="p-4 rounded-lg border border-border hover:border-primary hover:shadow-md transition-all"
                      >
                        <div className="flex items-start gap-3 mb-3">
                          <div className="w-10 h-10 rounded-lg gradient-navy flex items-center justify-center">
                            <EventIcon className="w-5 h-5 text-white" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-semibold text-dojo-navy truncate">{event.title}</h3>
                            <p className="text-xs text-muted-foreground capitalize">{event.type}</p>
                          </div>
                        </div>
                        <div className="space-y-2 text-sm mb-3">
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <Clock className="w-4 h-4" />
                            <span>{new Date(event.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                          </div>
                          <div className="flex items-center gap-2 text-muted-foreground">
                            <MapPin className="w-4 h-4" />
                            <span className="truncate">{event.location}</span>
                          </div>
                        </div>
                        {event.rsvpStatus ? (
                          <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(event.rsvpStatus)}`}>
                            {event.rsvpStatus === 'registered' && <CheckCircle2 className="w-3 h-3" />}
                            {event.rsvpStatus === 'cancelled' && <XCircle className="w-3 h-3" />}
                            {event.rsvpStatus === 'pending' && <Clock className="w-3 h-3" />}
                            {event.rsvpStatus}
                          </span>
                        ) : (
                          <button className="w-full px-3 py-2 rounded-lg bg-primary text-primary-fg text-sm font-medium hover:bg-primary/90 transition-colors">
                            Register
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {/* Profile Section */}
          {activeSection === 'profile' && (
            <div className="space-y-8">
              <div className="flex items-center justify-between">
                <h1 className="font-display text-3xl font-bold text-dojo-navy">My Profile</h1>
                <button
                  onClick={() => setIsEditingProfile(!isEditingProfile)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                    isEditingProfile
                      ? 'bg-success text-white hover:bg-success/90'
                      : 'bg-primary text-primary-fg hover:bg-primary/90'
                  }`}
                >
                  {isEditingProfile ? (
                    <>
                      <Save className="w-4 h-4" />
                      Save Changes
                    </>
                  ) : (
                    <>
                      <Edit2 className="w-4 h-4" />
                      Edit Profile
                    </>
                  )}
                </button>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Profile Photo */}
                <div className="lg:col-span-1">
                  <div className="bg-card rounded-xl shadow-card p-6 border border-border">
                    <h2 className="font-semibold text-dojo-navy mb-4">Profile Photo</h2>
                    <div className="flex flex-col items-center">
                      <div className="relative">
                        <div className="w-32 h-32 rounded-full gradient-navy flex items-center justify-center text-white font-bold text-4xl">
                          {student.name.split(' ').map((n) => n[0]).join('')}
                        </div>
                        {isEditingProfile && (
                          <button className="absolute bottom-0 right-0 w-10 h-10 rounded-full bg-accent text-white flex items-center justify-center shadow-lg hover:bg-accent/90 transition-colors">
                            <Camera className="w-5 h-5" />
                          </button>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mt-4 text-center">
                        {isEditingProfile ? 'Click to upload new photo' : 'Profile Photo'}
                      </p>
                    </div>
                  </div>

                  {/* Membership Badge */}
                  <div className="bg-card rounded-xl shadow-card p-6 border border-border mt-6">
                    <h2 className="font-semibold text-dojo-navy mb-4">Membership</h2>
                    <div className="text-center">
                      <div className="w-16 h-16 mx-auto rounded-full gradient-orange flex items-center justify-center mb-3">
                        <Award className="w-8 h-8 text-white" />
                      </div>
                      <div className="text-xl font-bold text-dojo-navy mb-1">{student.membershipTier}</div>
                      <div className="text-sm text-muted-foreground">
                        Expires: {new Date(student.membershipExpiry).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Profile Information */}
                <div className="lg:col-span-2 space-y-6">
                  <div className="bg-card rounded-xl shadow-card p-6 border border-border">
                    <h2 className="font-semibold text-dojo-navy mb-6 flex items-center gap-2">
                      <User className="w-5 h-5" />
                      Personal Information
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">Full Name</label>
                        {isEditingProfile ? (
                          <input
                            type="text"
                            defaultValue={student.name}
                            className="w-full px-4 py-2 rounded-lg border border-border bg-bg focus:outline-none focus:ring-2 focus:ring-ring"
                          />
                        ) : (
                          <div className="text-fg font-medium">{student.name}</div>
                        )}
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">Email Address</label>
                        {isEditingProfile ? (
                          <input
                            type="email"
                            defaultValue={student.email}
                            className="w-full px-4 py-2 rounded-lg border border-border bg-bg focus:outline-none focus:ring-2 focus:ring-ring"
                          />
                        ) : (
                          <div className="text-fg font-medium flex items-center gap-2">
                            <Mail className="w-4 h-4 text-muted-foreground" />
                            {student.email}
                          </div>
                        )}
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">Phone Number</label>
                        {isEditingProfile ? (
                          <input
                            type="tel"
                            defaultValue={student.phone}
                            className="w-full px-4 py-2 rounded-lg border border-border bg-bg focus:outline-none focus:ring-2 focus:ring-ring"
                          />
                        ) : (
                          <div className="text-fg font-medium flex items-center gap-2">
                            <Phone className="w-4 h-4 text-muted-foreground" />
                            {student.phone}
                          </div>
                        )}
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">Belt Rank</label>
                        {isEditingProfile ? (
                          <select className="w-full px-4 py-2 rounded-lg border border-border bg-bg focus:outline-none focus:ring-2 focus:ring-ring">
                            <option>2nd Dan Black Belt</option>
                            <option>3rd Dan Black Belt</option>
                            <option>4th Dan Black Belt</option>
                          </select>
                        ) : (
                          <div className="text-fg font-medium">{student.beltRank}</div>
                        )}
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">Dojo/School</label>
                        {isEditingProfile ? (
                          <input
                            type="text"
                            defaultValue={student.dojo}
                            className="w-full px-4 py-2 rounded-lg border border-border bg-bg focus:outline-none focus:ring-2 focus:ring-ring"
                          />
                        ) : (
                          <div className="text-fg font-medium">{student.dojo}</div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Emergency Contact */}
                  <div className="bg-card rounded-xl shadow-card p-6 border border-border">
                    <h2 className="font-semibold text-dojo-navy mb-6 flex items-center gap-2">
                      <Shield className="w-5 h-5" />
                      Emergency Contact
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">Name</label>
                        {isEditingProfile ? (
                          <input
                            type="text"
                            defaultValue={student.emergencyContact.name}
                            className="w-full px-4 py-2 rounded-lg border border-border bg-bg focus:outline-none focus:ring-2 focus:ring-ring"
                          />
                        ) : (
                          <div className="text-fg font-medium">{student.emergencyContact.name}</div>
                        )}
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">Relationship</label>
                        {isEditingProfile ? (
                          <input
                            type="text"
                            defaultValue={student.emergencyContact.relationship}
                            className="w-full px-4 py-2 rounded-lg border border-border bg-bg focus:outline-none focus:ring-2 focus:ring-ring"
                          />
                        ) : (
                          <div className="text-fg font-medium">{student.emergencyContact.relationship}</div>
                        )}
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-muted-foreground mb-2">Phone Number</label>
                        {isEditingProfile ? (
                          <input
                            type="tel"
                            defaultValue={student.emergencyContact.phone}
                            className="w-full px-4 py-2 rounded-lg border border-border bg-bg focus:outline-none focus:ring-2 focus:ring-ring"
                          />
                        ) : (
                          <div className="text-fg font-medium">{student.emergencyContact.phone}</div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Events Section */}
          {activeSection === 'events' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <h1 className="font-display text-3xl font-bold text-dojo-navy">Events</h1>
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <input
                      type="text"
                      placeholder="Search events..."
                      className="pl-10 pr-4 py-2 rounded-lg border border-border bg-card focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <div className="bg-card rounded-xl shadow-card border border-border overflow-hidden">
                <div className="border-b border-border">
                  <div className="flex flex-wrap">
                    {(['upcoming', 'past', 'all'] as EventTab[]).map((tab) => (
                      <button
                        key={tab}
                        onClick={() => setEventTab(tab)}
                        className={`px-6 py-3 font-medium capitalize transition-colors ${
                          eventTab === tab
                            ? 'text-primary border-b-2 border-primary bg-primary/5'
                            : 'text-muted-foreground hover:text-fg hover:bg-muted'
                        }`}
                      >
                        {tab} Events
                      </button>
                    ))}
                  </div>
                </div>

                {/* Filters */}
                <div className="p-4 border-b border-border bg-muted/30">
                  <div className="flex items-center gap-2 flex-wrap">
                    <Filter className="w-4 h-4 text-muted-foreground" />
                    <span className="text-sm font-medium text-muted-foreground">Filter by:</span>
                    {(['all', 'tournament', 'seminar', 'camp'] as EventFilter[]).map((filter) => (
                      <button
                        key={filter}
                        onClick={() => setEventFilter(filter)}
                        className={`px-3 py-1 rounded-full text-sm font-medium capitalize transition-colors ${
                          eventFilter === filter
                            ? 'bg-primary text-primary-fg'
                            : 'bg-card border border-border hover:bg-muted'
                        }`}
                      >
                        {filter}s
                      </button>
                    ))}
                  </div>
                </div>

                {/* Event List */}
                <div className="p-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {filteredEvents().map((event) => {
                      const EventIcon = getEventIcon(event.type);
                      const isPast = new Date(event.date) < new Date();
                      return (
                        <div
                          key={event.id}
                          className={`p-6 rounded-xl border border-border hover:border-primary hover:shadow-lg transition-all ${
                            isPast ? 'bg-muted/50' : 'bg-card'
                          }`}
                        >
                          <div className="flex items-start justify-between mb-4">
                            <div className="w-12 h-12 rounded-lg gradient-navy flex items-center justify-center">
                              <EventIcon className="w-6 h-6 text-white" />
                            </div>
                            <span className="px-2 py-1 rounded-full text-xs font-semibold bg-muted text-muted-foreground capitalize">
                              {event.type}
                            </span>
                          </div>
                          <h3 className="font-bold text-lg text-dojo-navy mb-3">{event.title}</h3>
                          <div className="space-y-2 mb-4">
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <Clock className="w-4 h-4" />
                              <span>{new Date(event.date).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                              <MapPin className="w-4 h-4" />
                              <span>{event.location}</span>
                            </div>
                          </div>
                          {event.rsvpStatus ? (
                            <div className="flex items-center gap-2">
                              <span className={`flex-1 inline-flex items-center justify-center gap-1 px-3 py-2 rounded-lg text-sm font-semibold border ${getStatusBadge(event.rsvpStatus)}`}>
                                {event.rsvpStatus === 'registered' && <CheckCircle2 className="w-4 h-4" />}
                                {event.rsvpStatus === 'cancelled' && <XCircle className="w-4 h-4" />}
                                {event.rsvpStatus === 'pending' && <Clock className="w-4 h-4" />}
                                {event.rsvpStatus}
                              </span>
                              {event.rsvpStatus === 'registered' && !isPast && (
                                <button className="px-3 py-2 rounded-lg border border-danger text-danger hover:bg-danger hover:text-white text-sm font-medium transition-colors">
                                  Cancel
                                </button>
                              )}
                            </div>
                          ) : (
                            !isPast && (
                              <button className="w-full px-4 py-2 rounded-lg bg-primary text-primary-fg font-medium hover:bg-primary/90 transition-colors">
                                Register Now
                              </button>
                            )
                          )}
                        </div>
                      );
                    })}
                  </div>
                  {filteredEvents().length === 0 && (
                    <div className="text-center py-12">
                      <Calendar className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                      <p className="text-muted-foreground">No events found</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Payments Section */}
          {activeSection === 'payments' && (
            <div className="space-y-8">
              <h1 className="font-display text-3xl font-bold text-dojo-navy">Payments</h1>

              {/* Membership Status Card */}
              <div className="bg-gradient-to-br from-success/10 via-card to-card rounded-xl shadow-glow p-8 border border-success/20">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                  <div>
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-success/20 text-success border border-success/30 mb-4">
                      <CheckCircle2 className="w-5 h-5" />
                      <span className="font-semibold">Active Membership</span>
                    </div>
                    <h2 className="font-display text-2xl font-bold text-dojo-navy mb-2">{student.membershipTier}</h2>
                    <p className="text-muted-foreground">
                      Valid until {new Date(student.membershipExpiry).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                    </p>
                  </div>
                  <button className="px-6 py-3 rounded-lg bg-primary text-primary-fg font-medium hover:bg-primary/90 transition-colors">
                    Renew Membership
                  </button>
                </div>
              </div>

              {/* Upcoming Payments */}
              <div className="bg-card rounded-xl shadow-card p-6 border border-border">
                <h2 className="font-semibold text-dojo-navy mb-4 flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  Upcoming Payments
                </h2>
                <div className="bg-accent/5 border border-accent/20 rounded-lg p-4 flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-accent flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-medium text-fg">Membership Renewal Due</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Your {student.membershipTier} membership will expire on {new Date(student.membershipExpiry).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
                    </p>
                  </div>
                </div>
              </div>

              {/* Payment History */}
              <div className="bg-card rounded-xl shadow-card border border-border overflow-hidden">
                <div className="p-6 border-b border-border">
                  <h2 className="font-semibold text-dojo-navy flex items-center gap-2">
                    <CreditCard className="w-5 h-5" />
                    Payment History
                  </h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-muted/50">
                      <tr>
                        <th className="text-left px-6 py-4 text-sm font-semibold text-muted-foreground">Date</th>
                        <th className="text-left px-6 py-4 text-sm font-semibold text-muted-foreground">Description</th>
                        <th className="text-right px-6 py-4 text-sm font-semibold text-muted-foreground">Amount</th>
                        <th className="text-center px-6 py-4 text-sm font-semibold text-muted-foreground">Status</th>
                        <th className="text-center px-6 py-4 text-sm font-semibold text-muted-foreground">Receipt</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {payments.map((payment) => (
                        <tr key={payment.id} className="hover:bg-muted/30 transition-colors">
                          <td className="px-6 py-4 text-sm text-fg">
                            {new Date(payment.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                          </td>
                          <td className="px-6 py-4 text-sm font-medium text-fg">{payment.description}</td>
                          <td className="px-6 py-4 text-sm font-bold text-dojo-navy text-right">
                            ${payment.amount.toFixed(2)}
                          </td>
                          <td className="px-6 py-4 text-center">
                            <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold border ${getStatusBadge(payment.status)}`}>
                              {payment.status === 'completed' && <CheckCircle2 className="w-3 h-3" />}
                              {payment.status === 'pending' && <Clock className="w-3 h-3" />}
                              {payment.status === 'failed' && <XCircle className="w-3 h-3" />}
                              {payment.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-center">
                            {payment.status === 'completed' && (
                              <button className="inline-flex items-center gap-1 text-primary hover:text-primary/80 font-medium text-sm transition-colors">
                                <Download className="w-4 h-4" />
                                Download
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Resources Section */}
          {activeSection === 'resources' && (
            <div className="space-y-6">
              <h1 className="font-display text-3xl font-bold text-dojo-navy">Resources</h1>
              <div className="bg-card rounded-xl shadow-card p-12 border border-border text-center">
                <BookOpen className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <h2 className="font-display text-2xl font-bold text-dojo-navy mb-2">Resources Coming Soon</h2>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Training materials, documents, and other resources will be available here soon.
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
