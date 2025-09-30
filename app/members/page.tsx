"use client";

import { useState, useMemo } from "react";

interface Member {
  id: string;
  name: string;
  avatar?: string;
  beltRank: string;
  beltColor: string;
  location: string;
  memberSince: string;
  dojo: string;
  specializations: string[];
  email: string;
  role: "Member" | "Instructor" | "Admin";
}

const mockMembers: Member[] = [
  {
    id: "1",
    name: "Alex Kim",
    beltRank: "Brown",
    beltColor: "#92400E",
    location: "New York, USA",
    memberSince: "2023-01-15",
    dojo: "Seaside Dojo",
    specializations: ["Karate", "Ju-Jitsu"],
    email: "alex@example.com",
    role: "Member"
  },
  {
    id: "2",
    name: "Sarah Chen",
    beltRank: "Black",
    beltColor: "#000000",
    location: "Los Angeles, USA",
    memberSince: "2020-03-22",
    dojo: "Mountain Peak Martial Arts",
    specializations: ["Taekwondo", "Kendo"],
    email: "sarah@example.com",
    role: "Instructor"
  },
  {
    id: "3",
    name: "Michael Rodriguez",
    beltRank: "Purple",
    beltColor: "#A855F7",
    location: "Miami, USA",
    memberSince: "2022-07-10",
    dojo: "Ocean Wave Dojo",
    specializations: ["Ju-Jitsu", "Aikido"],
    email: "michael@example.com",
    role: "Member"
  },
  {
    id: "4",
    name: "Yuki Tanaka",
    beltRank: "Black",
    beltColor: "#000000",
    location: "Tokyo, Japan",
    memberSince: "2019-11-05",
    dojo: "Rising Sun Academy",
    specializations: ["Karate", "Kobudo"],
    email: "yuki@example.com",
    role: "Instructor"
  },
  {
    id: "5",
    name: "Emma Wilson",
    beltRank: "Blue",
    beltColor: "#3B82F6",
    location: "London, UK",
    memberSince: "2023-05-18",
    dojo: "Thames Valley Martial Arts",
    specializations: ["Karate", "Self-Defense"],
    email: "emma@example.com",
    role: "Member"
  },
  {
    id: "6",
    name: "Carlos Silva",
    beltRank: "Green",
    beltColor: "#10B981",
    location: "São Paulo, Brazil",
    memberSince: "2023-09-01",
    dojo: "Brazilian Warriors",
    specializations: ["Capoeira", "Ju-Jitsu"],
    email: "carlos@example.com",
    role: "Member"
  },
  {
    id: "7",
    name: "Dr. James Park",
    beltRank: "Black",
    beltColor: "#000000",
    location: "Seoul, South Korea",
    memberSince: "2018-02-14",
    dojo: "Seoul Elite Taekwondo",
    specializations: ["Taekwondo", "Hapkido"],
    email: "james@example.com",
    role: "Instructor"
  },
  {
    id: "8",
    name: "Nina Patel",
    beltRank: "Brown",
    beltColor: "#92400E",
    location: "Mumbai, India",
    memberSince: "2021-12-03",
    dojo: "Gateway Martial Arts",
    specializations: ["Karate", "Krav Maga"],
    email: "nina@example.com",
    role: "Member"
  },
  {
    id: "9",
    name: "Thomas Anderson",
    beltRank: "Orange",
    beltColor: "#F97316",
    location: "Sydney, Australia",
    memberSince: "2024-01-20",
    dojo: "Southern Cross Dojo",
    specializations: ["Karate"],
    email: "thomas@example.com",
    role: "Member"
  },
  {
    id: "10",
    name: "Lisa Müller",
    beltRank: "Purple",
    beltColor: "#A855F7",
    location: "Berlin, Germany",
    memberSince: "2022-04-15",
    dojo: "Berlin Combat Academy",
    specializations: ["Ju-Jitsu", "Judo"],
    email: "lisa@example.com",
    role: "Member"
  },
  {
    id: "11",
    name: "Sensei Hiroshi Yamamoto",
    beltRank: "Red & White",
    beltColor: "#DC2626",
    location: "Kyoto, Japan",
    memberSince: "2017-06-01",
    dojo: "Ancient Ways Dojo",
    specializations: ["Karate", "Iaido", "Kendo"],
    email: "hiroshi@example.com",
    role: "Instructor"
  },
  {
    id: "12",
    name: "Maya Johnson",
    beltRank: "Yellow",
    beltColor: "#FCD34D",
    location: "Chicago, USA",
    memberSince: "2024-03-10",
    dojo: "Windy City Warriors",
    specializations: ["Karate"],
    email: "maya@example.com",
    role: "Member"
  }
];

export default function MembersPage() {
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedBelt, setSelectedBelt] = useState<string>("all");
  const [selectedRole, setSelectedRole] = useState<string>("all");
  const [selectedLocation, setSelectedLocation] = useState<string>("all");
  const [selectedMember, setSelectedMember] = useState<Member | null>(null);

  // Extract unique values for filters
  const belts = useMemo(() => {
    const uniqueBelts = Array.from(new Set(mockMembers.map(m => m.beltRank)));
    return ["all", ...uniqueBelts];
  }, []);

  const locations = useMemo(() => {
    const uniqueLocations = Array.from(new Set(mockMembers.map(m => m.location.split(",")[1]?.trim() || m.location)));
    return ["all", ...uniqueLocations.sort()];
  }, []);

  // Filter members
  const filteredMembers = useMemo(() => {
    return mockMembers.filter(member => {
      const matchesSearch =
        member.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        member.dojo.toLowerCase().includes(searchQuery.toLowerCase()) ||
        member.specializations.some(s => s.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesBelt = selectedBelt === "all" || member.beltRank === selectedBelt;
      const matchesRole = selectedRole === "all" || member.role === selectedRole;
      const matchesLocation = selectedLocation === "all" || member.location.includes(selectedLocation);

      return matchesSearch && matchesBelt && matchesRole && matchesLocation;
    });
  }, [searchQuery, selectedBelt, selectedRole, selectedLocation]);

  const getInitials = (name: string) => {
    return name.split(" ").map(n => n[0]).join("");
  };

  const formatMemberSince = (date: string) => {
    return new Date(date).toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-white py-12 px-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="font-display text-4xl font-bold text-dojo-navy mb-3">
            Member Directory
          </h1>
          <p className="text-lg text-gray-600">
            Connect with martial artists from around the world
          </p>
        </div>

        {/* Search and Filters */}
        <div className="bg-white rounded-2xl shadow-card p-6 mb-8">
          <div className="grid md:grid-cols-5 gap-4 mb-4">
            {/* Search */}
            <div className="md:col-span-2">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search by name, dojo, or specialization..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
                />
                <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* Belt Filter */}
            <div>
              <select
                value={selectedBelt}
                onChange={(e) => setSelectedBelt(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
              >
                <option value="all">All Belts</option>
                {belts.filter(b => b !== "all").map(belt => (
                  <option key={belt} value={belt}>{belt} Belt</option>
                ))}
              </select>
            </div>

            {/* Role Filter */}
            <div>
              <select
                value={selectedRole}
                onChange={(e) => setSelectedRole(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
              >
                <option value="all">All Roles</option>
                <option value="Member">Members</option>
                <option value="Instructor">Instructors</option>
                <option value="Admin">Admins</option>
              </select>
            </div>

            {/* Location Filter */}
            <div>
              <select
                value={selectedLocation}
                onChange={(e) => setSelectedLocation(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
              >
                <option value="all">All Locations</option>
                {locations.filter(l => l !== "all").map(location => (
                  <option key={location} value={location}>{location}</option>
                ))}
              </select>
            </div>
          </div>

          {/* View Toggle and Results Count */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-200">
            <p className="text-sm text-gray-600">
              Showing <span className="font-semibold text-dojo-navy">{filteredMembers.length}</span> member{filteredMembers.length !== 1 ? 's' : ''}
            </p>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setViewMode("grid")}
                className={`p-2 rounded-lg transition-all ${
                  viewMode === "grid"
                    ? "bg-dojo-navy text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              </button>
              <button
                onClick={() => setViewMode("list")}
                className={`p-2 rounded-lg transition-all ${
                  viewMode === "list"
                    ? "bg-dojo-navy text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Members Display */}
        {viewMode === "grid" ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredMembers.map(member => (
              <button
                key={member.id}
                onClick={() => setSelectedMember(member)}
                className="bg-white rounded-2xl shadow-card p-6 hover:shadow-xl transition-all text-left group"
              >
                <div className="flex flex-col items-center text-center">
                  {/* Avatar */}
                  <div className="w-20 h-20 rounded-full gradient-navy flex items-center justify-center text-white text-2xl font-bold mb-4 group-hover:scale-110 transition-transform">
                    {getInitials(member.name)}
                  </div>

                  {/* Name */}
                  <h3 className="font-display text-lg font-bold text-dojo-navy mb-1">
                    {member.name}
                  </h3>

                  {/* Belt Rank Badge */}
                  <div
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold mb-3"
                    style={{
                      backgroundColor: member.beltColor,
                      color: member.beltRank === "Yellow" ? "#000000" : "#FFFFFF"
                    }}
                  >
                    <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                    </svg>
                    {member.beltRank}
                  </div>

                  {/* Role Badge */}
                  {member.role === "Instructor" && (
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-accent/10 text-accent rounded-full text-xs font-semibold mb-3">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                      </svg>
                      Instructor
                    </span>
                  )}

                  {/* Location */}
                  <p className="text-sm text-gray-600 flex items-center gap-1 mb-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    {member.location}
                  </p>

                  {/* Member Since */}
                  <p className="text-xs text-gray-500">
                    Member since {formatMemberSince(member.memberSince)}
                  </p>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredMembers.map(member => (
              <button
                key={member.id}
                onClick={() => setSelectedMember(member)}
                className="w-full bg-white rounded-2xl shadow-card p-6 hover:shadow-xl transition-all text-left group"
              >
                <div className="flex items-center gap-6">
                  {/* Avatar */}
                  <div className="w-16 h-16 rounded-full gradient-navy flex items-center justify-center text-white text-xl font-bold group-hover:scale-110 transition-transform flex-shrink-0">
                    {getInitials(member.name)}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-display text-xl font-bold text-dojo-navy">
                        {member.name}
                      </h3>
                      <div
                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold"
                        style={{
                          backgroundColor: member.beltColor,
                          color: member.beltRank === "Yellow" ? "#000000" : "#FFFFFF"
                        }}
                      >
                        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                        </svg>
                        {member.beltRank}
                      </div>
                      {member.role === "Instructor" && (
                        <span className="inline-flex items-center gap-1 px-2 py-1 bg-accent/10 text-accent rounded-full text-xs font-semibold">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                          </svg>
                          Instructor
                        </span>
                      )}
                    </div>
                    <div className="grid sm:grid-cols-3 gap-4 text-sm">
                      <div className="flex items-center gap-2 text-gray-600">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                        {member.dojo}
                      </div>
                      <div className="flex items-center gap-2 text-gray-600">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        {member.location}
                      </div>
                      <div className="flex items-center gap-2 text-gray-600">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        Since {formatMemberSince(member.memberSince)}
                      </div>
                    </div>
                  </div>

                  {/* Arrow */}
                  <svg className="w-6 h-6 text-gray-400 group-hover:text-primary group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>
            ))}
          </div>
        )}

        {/* Empty State */}
        {filteredMembers.length === 0 && (
          <div className="text-center py-16">
            <svg className="w-20 h-20 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <h3 className="font-display text-2xl font-bold text-gray-600 mb-2">No members found</h3>
            <p className="text-gray-500">Try adjusting your search or filters</p>
          </div>
        )}
      </div>

      {/* Member Detail Modal */}
      {selectedMember && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-6" onClick={() => setSelectedMember(null)}>
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            {/* Header */}
            <div className="gradient-navy p-8 text-white relative">
              <button
                onClick={() => setSelectedMember(null)}
                className="absolute top-4 right-4 w-10 h-10 bg-white/20 hover:bg-white/30 rounded-full flex items-center justify-center transition-all"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <div className="flex items-center gap-6">
                <div className="w-24 h-24 rounded-full bg-white/20 flex items-center justify-center text-white text-3xl font-bold">
                  {getInitials(selectedMember.name)}
                </div>
                <div>
                  <h2 className="font-display text-3xl font-bold mb-2">{selectedMember.name}</h2>
                  <div className="flex items-center gap-2">
                    <div
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-semibold"
                      style={{
                        backgroundColor: selectedMember.beltColor,
                        color: selectedMember.beltRank === "Yellow" ? "#000000" : "#FFFFFF"
                      }}
                    >
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                      </svg>
                      {selectedMember.beltRank} Belt
                    </div>
                    {selectedMember.role === "Instructor" && (
                      <span className="inline-flex items-center gap-1 px-3 py-1.5 bg-accent rounded-full text-white text-sm font-semibold">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                        </svg>
                        Instructor
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-8">
              <div className="space-y-6">
                {/* Basic Info */}
                <div>
                  <h3 className="font-display text-xl font-bold text-dojo-navy mb-4">Information</h3>
                  <div className="grid sm:grid-cols-2 gap-4">
                    <div className="flex items-start gap-3">
                      <svg className="w-5 h-5 text-primary mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                      <div>
                        <p className="text-sm text-gray-600">Dojo</p>
                        <p className="font-semibold text-gray-900">{selectedMember.dojo}</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <svg className="w-5 h-5 text-primary mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <div>
                        <p className="text-sm text-gray-600">Location</p>
                        <p className="font-semibold text-gray-900">{selectedMember.location}</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <svg className="w-5 h-5 text-primary mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <div>
                        <p className="text-sm text-gray-600">Member Since</p>
                        <p className="font-semibold text-gray-900">{formatMemberSince(selectedMember.memberSince)}</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <svg className="w-5 h-5 text-primary mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      <div>
                        <p className="text-sm text-gray-600">Email</p>
                        <p className="font-semibold text-gray-900">{selectedMember.email}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Specializations */}
                <div>
                  <h3 className="font-display text-xl font-bold text-dojo-navy mb-4">Specializations</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedMember.specializations.map((spec, idx) => (
                      <span
                        key={idx}
                        className="px-4 py-2 bg-gradient-accent border border-primary/20 rounded-full text-sm font-semibold text-dojo-navy"
                      >
                        {spec}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-3 pt-4">
                  <button className="flex-1 px-6 py-3 gradient-navy text-white rounded-xl font-semibold hover:shadow-lg transition-all">
                    Send Message
                  </button>
                  <button className="flex-1 px-6 py-3 border-2 border-dojo-navy text-dojo-navy rounded-xl font-semibold hover:bg-dojo-navy hover:text-white transition-all">
                    View Full Profile
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
