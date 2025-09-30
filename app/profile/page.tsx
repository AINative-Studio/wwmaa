"use client";

import { useState } from "react";

const beltRanks = [
  { name: "White", color: "#FFFFFF", textColor: "#000000" },
  { name: "Yellow", color: "#FCD34D", textColor: "#000000" },
  { name: "Orange", color: "#F97316", textColor: "#FFFFFF" },
  { name: "Green", color: "#10B981", textColor: "#FFFFFF" },
  { name: "Blue", color: "#3B82F6", textColor: "#FFFFFF" },
  { name: "Purple", color: "#A855F7", textColor: "#FFFFFF" },
  { name: "Brown", color: "#92400E", textColor: "#FFFFFF" },
  { name: "Black", color: "#000000", textColor: "#FFFFFF" },
  { name: "Red & White", color: "linear-gradient(90deg, #DC2626 50%, #FFFFFF 50%)", textColor: "#000000" }
];

interface UserProfile {
  fullName: string;
  email: string;
  phone: string;
  dateOfBirth: string;
  address: string;
  beltRank: string;
  dojoName: string;
  trainingSince: string;
  specializations: string;
  emergencyContactName: string;
  emergencyContactPhone: string;
  emergencyContactRelation: string;
  membershipTier: string;
  joinDate: string;
  renewalDate: string;
  emailNotifications: boolean;
  eventReminders: boolean;
  newsletter: boolean;
  profileVisibility: string;
}

export default function ProfilePage() {
  const [isEditing, setIsEditing] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [profile, setProfile] = useState<UserProfile>({
    fullName: "Alex Kim",
    email: "alex@example.com",
    phone: "+1 (555) 123-4567",
    dateOfBirth: "1990-05-15",
    address: "123 Main Street, New York, NY 10001",
    beltRank: "Brown",
    dojoName: "Seaside Dojo",
    trainingSince: "2018-03-01",
    specializations: "Karate, Ju-Jitsu, Weapons Training",
    emergencyContactName: "Jane Kim",
    emergencyContactPhone: "+1 (555) 987-6543",
    emergencyContactRelation: "Spouse",
    membershipTier: "Premium",
    joinDate: "2023-01-15",
    renewalDate: "2026-01-15",
    emailNotifications: true,
    eventReminders: true,
    newsletter: false,
    profileVisibility: "members"
  });

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handleInputChange = (field: keyof UserProfile, value: string | boolean) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = () => {
    setIsEditing(false);
    // Here you would typically send the updated profile to your API
    console.log("Saving profile:", profile);
  };

  const handlePasswordChange = () => {
    if (newPassword !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }
    // Here you would typically send the password update to your API
    console.log("Changing password");
    setShowPasswordModal(false);
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
  };

  const getBeltColor = (rank: string) => {
    return beltRanks.find(b => b.name === rank);
  };

  const beltColor = getBeltColor(profile.beltRank);

  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-white py-12 px-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="font-display text-4xl font-bold text-dojo-navy mb-3">
            My Profile
          </h1>
          <p className="text-lg text-gray-600">
            Manage your personal information and account settings
          </p>
        </div>

        {/* Profile Photo Section */}
        <div className="bg-white rounded-2xl shadow-card p-8 mb-6">
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="relative">
              <div className="w-32 h-32 rounded-full gradient-navy flex items-center justify-center text-white text-5xl font-bold shadow-lg">
                {profile.fullName.split(" ").map(n => n[0]).join("")}
              </div>
              <button className="absolute bottom-0 right-0 w-10 h-10 bg-accent rounded-full flex items-center justify-center text-white shadow-lg hover:scale-110 transition-transform">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                </svg>
              </button>
            </div>
            <div className="text-center md:text-left flex-1">
              <h2 className="font-display text-2xl font-bold text-dojo-navy mb-1">
                {profile.fullName}
              </h2>
              <p className="text-gray-600 mb-3">{profile.email}</p>
              {beltColor && (
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border-2" style={{
                  background: beltColor.color,
                  color: beltColor.textColor,
                  borderColor: beltColor.name === "White" ? "#E5E7EB" : "transparent"
                }}>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2L2 7v10c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V7l-10-5z"/>
                  </svg>
                  <span className="font-semibold">{beltColor.name} Belt</span>
                </div>
              )}
            </div>
            <button
              onClick={() => isEditing ? handleSave() : setIsEditing(true)}
              className={`px-6 py-3 rounded-xl font-semibold transition-all ${
                isEditing
                  ? "gradient-green text-white shadow-lg"
                  : "bg-dojo-navy text-white hover:bg-dojo-navy/90"
              }`}
            >
              {isEditing ? (
                <span className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  Save Changes
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                  Edit Profile
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Personal Information */}
        <div className="bg-white rounded-2xl shadow-card p-8 mb-6">
          <h2 className="font-display text-2xl font-bold text-dojo-navy mb-6 flex items-center gap-3">
            <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            Personal Information
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Full Name</label>
              <input
                type="text"
                value={profile.fullName}
                onChange={(e) => handleInputChange("fullName", e.target.value)}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all disabled:bg-gray-50 disabled:text-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Email</label>
              <input
                type="email"
                value={profile.email}
                onChange={(e) => handleInputChange("email", e.target.value)}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all disabled:bg-gray-50 disabled:text-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Phone Number</label>
              <input
                type="tel"
                value={profile.phone}
                onChange={(e) => handleInputChange("phone", e.target.value)}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all disabled:bg-gray-50 disabled:text-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Date of Birth</label>
              <input
                type="date"
                value={profile.dateOfBirth}
                onChange={(e) => handleInputChange("dateOfBirth", e.target.value)}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all disabled:bg-gray-50 disabled:text-gray-600"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Address</label>
              <input
                type="text"
                value={profile.address}
                onChange={(e) => handleInputChange("address", e.target.value)}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all disabled:bg-gray-50 disabled:text-gray-600"
              />
            </div>
          </div>
        </div>

        {/* Martial Arts Information */}
        <div className="bg-white rounded-2xl shadow-card p-8 mb-6">
          <h2 className="font-display text-2xl font-bold text-dojo-navy mb-6 flex items-center gap-3">
            <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Martial Arts Information
          </h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Belt Rank</label>
              <select
                value={profile.beltRank}
                onChange={(e) => handleInputChange("beltRank", e.target.value)}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all disabled:bg-gray-50 disabled:text-gray-600"
              >
                {beltRanks.map(belt => (
                  <option key={belt.name} value={belt.name}>{belt.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Dojo/School Name</label>
              <input
                type="text"
                value={profile.dojoName}
                onChange={(e) => handleInputChange("dojoName", e.target.value)}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all disabled:bg-gray-50 disabled:text-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Training Since</label>
              <input
                type="date"
                value={profile.trainingSince}
                onChange={(e) => handleInputChange("trainingSince", e.target.value)}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all disabled:bg-gray-50 disabled:text-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Specializations/Styles</label>
              <input
                type="text"
                value={profile.specializations}
                onChange={(e) => handleInputChange("specializations", e.target.value)}
                disabled={!isEditing}
                placeholder="e.g., Karate, Ju-Jitsu, Kendo"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all disabled:bg-gray-50 disabled:text-gray-600"
              />
            </div>
          </div>
        </div>

        {/* Emergency Contact */}
        <div className="bg-white rounded-2xl shadow-card p-8 mb-6">
          <h2 className="font-display text-2xl font-bold text-dojo-navy mb-6 flex items-center gap-3">
            <svg className="w-6 h-6 text-danger" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Emergency Contact
          </h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Contact Name</label>
              <input
                type="text"
                value={profile.emergencyContactName}
                onChange={(e) => handleInputChange("emergencyContactName", e.target.value)}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all disabled:bg-gray-50 disabled:text-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Contact Phone</label>
              <input
                type="tel"
                value={profile.emergencyContactPhone}
                onChange={(e) => handleInputChange("emergencyContactPhone", e.target.value)}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all disabled:bg-gray-50 disabled:text-gray-600"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Relationship</label>
              <input
                type="text"
                value={profile.emergencyContactRelation}
                onChange={(e) => handleInputChange("emergencyContactRelation", e.target.value)}
                disabled={!isEditing}
                placeholder="e.g., Spouse, Parent"
                className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all disabled:bg-gray-50 disabled:text-gray-600"
              />
            </div>
          </div>
        </div>

        {/* Membership Information */}
        <div className="bg-gradient-accent rounded-2xl shadow-card p-8 mb-6 border border-primary/20">
          <h2 className="font-display text-2xl font-bold text-dojo-navy mb-6 flex items-center gap-3">
            <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
            </svg>
            Membership Information
          </h2>
          <div className="grid md:grid-cols-2 gap-6 mb-6">
            <div className="bg-white rounded-xl p-4">
              <p className="text-sm text-gray-600 mb-1">Current Tier</p>
              <p className="text-2xl font-bold text-dojo-navy">{profile.membershipTier}</p>
            </div>
            <div className="bg-white rounded-xl p-4">
              <p className="text-sm text-gray-600 mb-1">Member Since</p>
              <p className="text-2xl font-bold text-dojo-navy">
                {new Date(profile.joinDate).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
              </p>
            </div>
            <div className="bg-white rounded-xl p-4 md:col-span-2">
              <p className="text-sm text-gray-600 mb-1">Next Renewal Date</p>
              <p className="text-2xl font-bold text-dojo-navy">
                {new Date(profile.renewalDate).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <a
              href="/membership"
              className="inline-flex items-center gap-2 px-6 py-3 bg-dojo-navy text-white rounded-xl font-semibold hover:bg-dojo-navy/90 transition-all"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
              </svg>
              Change Membership
            </a>
            <button className="inline-flex items-center gap-2 px-6 py-3 border-2 border-dojo-navy text-dojo-navy rounded-xl font-semibold hover:bg-dojo-navy hover:text-white transition-all">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              View Invoice History
            </button>
          </div>
        </div>

        {/* Account Settings */}
        <div className="bg-white rounded-2xl shadow-card p-8">
          <h2 className="font-display text-2xl font-bold text-dojo-navy mb-6 flex items-center gap-3">
            <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Account Settings
          </h2>

          {/* Password Section */}
          <div className="mb-8 pb-8 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-4">Security</h3>
            <button
              onClick={() => setShowPasswordModal(true)}
              className="inline-flex items-center gap-2 px-6 py-3 bg-gray-100 text-gray-900 rounded-xl font-semibold hover:bg-gray-200 transition-all"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Change Password
            </button>
          </div>

          {/* Email Preferences */}
          <div className="mb-8 pb-8 border-b border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-4">Email Preferences</h3>
            <div className="space-y-4">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.emailNotifications}
                  onChange={(e) => handleInputChange("emailNotifications", e.target.checked)}
                  className="w-5 h-5 text-primary rounded focus:ring-2 focus:ring-primary"
                />
                <div>
                  <p className="font-semibold text-gray-900">Email Notifications</p>
                  <p className="text-sm text-gray-600">Receive updates about your account and activities</p>
                </div>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.eventReminders}
                  onChange={(e) => handleInputChange("eventReminders", e.target.checked)}
                  className="w-5 h-5 text-primary rounded focus:ring-2 focus:ring-primary"
                />
                <div>
                  <p className="font-semibold text-gray-900">Event Reminders</p>
                  <p className="text-sm text-gray-600">Get reminded about upcoming events and trainings</p>
                </div>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={profile.newsletter}
                  onChange={(e) => handleInputChange("newsletter", e.target.checked)}
                  className="w-5 h-5 text-primary rounded focus:ring-2 focus:ring-primary"
                />
                <div>
                  <p className="font-semibold text-gray-900">Newsletter</p>
                  <p className="text-sm text-gray-600">Receive our weekly newsletter with martial arts content</p>
                </div>
              </label>
            </div>
          </div>

          {/* Privacy Settings */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Privacy Settings</h3>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Profile Visibility</label>
              <select
                value={profile.profileVisibility}
                onChange={(e) => handleInputChange("profileVisibility", e.target.value)}
                className="w-full md:w-auto px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all"
              >
                <option value="public">Public - Visible to everyone</option>
                <option value="members">Members Only - Visible to WWMAA members</option>
                <option value="instructors">Instructors Only - Visible to instructors and admins</option>
                <option value="private">Private - Only visible to you</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Password Change Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-6">
          <div className="bg-white rounded-2xl shadow-2xl p-8 max-w-md w-full">
            <h2 className="font-display text-2xl font-bold text-dojo-navy mb-6">Change Password</h2>
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Current Password</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">New Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Confirm New Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent outline-none"
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={handlePasswordChange}
                className="flex-1 px-6 py-3 gradient-navy text-white rounded-xl font-semibold hover:shadow-lg transition-all"
              >
                Update Password
              </button>
              <button
                onClick={() => setShowPasswordModal(false)}
                className="flex-1 px-6 py-3 bg-gray-100 text-gray-900 rounded-xl font-semibold hover:bg-gray-200 transition-all"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
