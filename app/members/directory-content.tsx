"use client";

import { useState } from "react";
import { directoryMembers, states, memberTypes, type DirectoryMember } from "@/lib/directory-data";
import { MapPin, Award, Users, School } from "lucide-react";

export function DirectoryContent() {
  const [selectedState, setSelectedState] = useState("All States");
  const [selectedType, setSelectedType] = useState("all");

  const filteredMembers = directoryMembers.filter((member) => {
    const stateMatch = selectedState === "All States" || member.state === selectedState;
    const typeMatch = selectedType === "all" || member.type === selectedType;
    return stateMatch && typeMatch;
  });

  const getMemberIcon = (type: string) => {
    switch (type) {
      case "student":
        return <Users className="w-5 h-5" />;
      case "instructor":
        return <Award className="w-5 h-5" />;
      case "dojo":
        return <School className="w-5 h-5" />;
      default:
        return null;
    }
  };

  const getMemberTypeLabel = (type: string) => {
    switch (type) {
      case "student":
        return "Student Member";
      case "instructor":
        return "Certified Instructor";
      case "dojo":
        return "WWMAA Dojo";
      default:
        return "";
    }
  };

  const getMemberTypeBadge = (type: string) => {
    switch (type) {
      case "student":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "instructor":
        return "bg-purple-100 text-purple-700 border-purple-200";
      case "dojo":
        return "bg-green-100 text-green-700 border-green-200";
      default:
        return "bg-gray-100 text-gray-700 border-gray-200";
    }
  };

  return (
    <div className="py-24">
      <div className="mx-auto max-w-7xl px-6">
        {/* Filters */}
        <div className="bg-white rounded-2xl shadow-card p-8 mb-12 border border-gray-100">
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="state-filter" className="block text-sm font-semibold text-gray-700 mb-2">
                Filter by State
              </label>
              <select
                id="state-filter"
                value={selectedState}
                onChange={(e) => setSelectedState(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-dojo-navy focus:border-transparent outline-none transition-all"
              >
                {states.map((state) => (
                  <option key={state} value={state}>
                    {state}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="type-filter" className="block text-sm font-semibold text-gray-700 mb-2">
                Filter by Type
              </label>
              <select
                id="type-filter"
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-dojo-navy focus:border-transparent outline-none transition-all"
              >
                {memberTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-6 flex items-center justify-between">
            <p className="text-gray-600">
              Showing <span className="font-bold text-dojo-navy">{filteredMembers.length}</span> member{filteredMembers.length !== 1 ? 's' : ''}
            </p>
            <button
              onClick={() => {
                setSelectedState("All States");
                setSelectedType("all");
              }}
              className="text-dojo-green hover:text-dojo-navy font-semibold transition-colors"
            >
              Reset Filters
            </button>
          </div>
        </div>

        {/* Members Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredMembers.map((member) => (
            <div
              key={member.id}
              className="bg-white rounded-2xl shadow-card hover:shadow-glow transition-all p-6 border border-gray-100"
            >
              {/* Avatar and Type Badge */}
              <div className="flex items-start justify-between mb-4">
                <img
                  src={member.avatar}
                  alt={`${member.name} avatar`}
                  className="w-16 h-16 rounded-full border-2 border-gray-200"
                />
                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border text-xs font-semibold ${getMemberTypeBadge(member.type)}`}>
                  {getMemberIcon(member.type)}
                  {getMemberTypeLabel(member.type)}
                </div>
              </div>

              {/* Name and Rank */}
              <h3 className="font-display text-xl font-bold text-dojo-navy mb-1">
                {member.name}
              </h3>
              {member.beltRank && (
                <p className="text-dojo-orange font-semibold mb-3">
                  {member.beltRank}
                </p>
              )}

              {/* Location */}
              <div className="flex items-center gap-2 text-gray-600 mb-3">
                <MapPin className="w-4 h-4 text-gray-400" />
                <span className="text-sm">
                  {member.city}, {member.state}
                </span>
              </div>

              {/* Disciplines */}
              <div className="flex flex-wrap gap-2 mb-4">
                {member.disciplines.map((discipline) => (
                  <span
                    key={discipline}
                    className="px-3 py-1 bg-gradient-to-r from-dojo-navy/5 to-dojo-green/5 text-dojo-navy text-xs font-semibold rounded-full border border-dojo-navy/10"
                  >
                    {discipline}
                  </span>
                ))}
              </div>

              {/* Dojo Name (for students) */}
              {member.dojoName && (
                <p className="text-sm text-gray-600 mb-3">
                  <span className="font-semibold">Training at:</span> {member.dojoName}
                </p>
              )}

              {/* Specialties (for instructors) */}
              {member.specialties && member.specialties.length > 0 && (
                <div className="mb-3">
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                    Specialties
                  </p>
                  <p className="text-sm text-gray-700">
                    {member.specialties.join(", ")}
                  </p>
                </div>
              )}

              {/* Years of Experience */}
              {member.yearsExperience && (
                <p className="text-sm text-gray-600 mb-3">
                  <span className="font-semibold">{member.yearsExperience} years</span> of experience
                </p>
              )}

              {/* Bio */}
              {member.bio && (
                <p className="text-sm text-gray-600 italic border-t border-gray-100 pt-3">
                  "{member.bio}"
                </p>
              )}
            </div>
          ))}
        </div>

        {/* No Results */}
        {filteredMembers.length === 0 && (
          <div className="text-center py-16">
            <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gray-100 mb-6">
              <Users className="w-10 h-10 text-gray-400" />
            </div>
            <h3 className="font-display text-2xl font-bold text-gray-900 mb-2">
              No members found
            </h3>
            <p className="text-gray-600 mb-6">
              Try adjusting your filters to see more members
            </p>
            <button
              onClick={() => {
                setSelectedState("All States");
                setSelectedType("all");
              }}
              className="inline-flex items-center justify-center px-6 py-3 rounded-xl bg-dojo-navy text-white font-semibold hover:bg-dojo-green transition-colors"
            >
              Reset Filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
