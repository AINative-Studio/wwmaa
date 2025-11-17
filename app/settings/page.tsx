"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Settings,
  Bell,
  Lock,
  Eye,
  Mail,
  Globe,
  Shield,
  Smartphone,
  CheckCircle2,
  XCircle,
} from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuth();
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");

  // Settings state
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [eventReminders, setEventReminders] = useState(true);
  const [newsletter, setNewsletter] = useState(false);
  const [marketingEmails, setMarketingEmails] = useState(false);
  const [profileVisibility, setProfileVisibility] = useState("members");
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);
  const [sessionTimeout, setSessionTimeout] = useState("30");

  // Password change state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const handlePasswordChange = () => {
    if (newPassword !== confirmPassword) {
      alert("Passwords do not match!");
      return;
    }
    if (newPassword.length < 8) {
      alert("Password must be at least 8 characters long!");
      return;
    }
    // Here you would typically call an API to update the password
    console.log("Changing password");
    setShowPasswordModal(false);
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setSuccessMessage("Password updated successfully!");
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 3000);
  };

  const handleSaveSettings = () => {
    // Here you would typically call an API to save settings
    console.log("Saving settings:", {
      emailNotifications,
      eventReminders,
      newsletter,
      marketingEmails,
      profileVisibility,
      twoFactorEnabled,
      sessionTimeout,
    });
    setSuccessMessage("Settings saved successfully!");
    setShowSuccess(true);
    setTimeout(() => setShowSuccess(false), 3000);
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-bg to-white flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Please log in to access settings.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-bg to-white py-12 px-6">
      {/* Success Message */}
      {showSuccess && (
        <div className="fixed top-4 right-4 z-50 bg-green-50 border border-green-200 text-green-800 px-6 py-3 rounded-lg shadow-lg flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-green-600" />
          <span className="font-medium">{successMessage}</span>
        </div>
      )}

      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="font-display text-4xl font-bold text-dojo-navy mb-3 flex items-center gap-3">
            <Settings className="w-10 h-10" />
            Settings
          </h1>
          <p className="text-lg text-gray-600">
            Manage your account preferences and security settings
          </p>
        </div>

        {/* Notifications Settings */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Notifications
            </CardTitle>
            <CardDescription>
              Configure how and when you receive notifications
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="email-notifications" className="text-base font-semibold">
                  Email Notifications
                </Label>
                <p className="text-sm text-gray-500">
                  Receive updates about your account and activities
                </p>
              </div>
              <Switch
                id="email-notifications"
                checked={emailNotifications}
                onCheckedChange={setEmailNotifications}
              />
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="event-reminders" className="text-base font-semibold">
                  Event Reminders
                </Label>
                <p className="text-sm text-gray-500">
                  Get reminded about upcoming events and training sessions
                </p>
              </div>
              <Switch
                id="event-reminders"
                checked={eventReminders}
                onCheckedChange={setEventReminders}
              />
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="newsletter" className="text-base font-semibold">
                  Newsletter
                </Label>
                <p className="text-sm text-gray-500">
                  Receive our weekly newsletter with martial arts content
                </p>
              </div>
              <Switch
                id="newsletter"
                checked={newsletter}
                onCheckedChange={setNewsletter}
              />
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="marketing" className="text-base font-semibold">
                  Marketing Emails
                </Label>
                <p className="text-sm text-gray-500">
                  Receive information about promotions and special offers
                </p>
              </div>
              <Switch
                id="marketing"
                checked={marketingEmails}
                onCheckedChange={setMarketingEmails}
              />
            </div>
          </CardContent>
        </Card>

        {/* Privacy Settings */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Eye className="w-5 h-5" />
              Privacy
            </CardTitle>
            <CardDescription>
              Control who can see your profile and information
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Label htmlFor="visibility" className="text-base font-semibold">
                  Profile Visibility
                </Label>
                <p className="text-sm text-gray-500 mb-3">
                  Choose who can view your profile information
                </p>
                <Select value={profileVisibility} onValueChange={setProfileVisibility}>
                  <SelectTrigger id="visibility" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="public">
                      <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4" />
                        Public - Visible to everyone
                      </div>
                    </SelectItem>
                    <SelectItem value="members">
                      <div className="flex items-center gap-2">
                        <Shield className="w-4 h-4" />
                        Members Only - Visible to WWMAA members
                      </div>
                    </SelectItem>
                    <SelectItem value="instructors">
                      <div className="flex items-center gap-2">
                        <Shield className="w-4 h-4" />
                        Instructors Only - Visible to instructors and admins
                      </div>
                    </SelectItem>
                    <SelectItem value="private">
                      <div className="flex items-center gap-2">
                        <Lock className="w-4 h-4" />
                        Private - Only visible to you
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Security Settings */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lock className="w-5 h-5" />
              Security
            </CardTitle>
            <CardDescription>
              Manage your password and security preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <Label className="text-base font-semibold">Password</Label>
              <p className="text-sm text-gray-500 mb-3">
                Change your password to keep your account secure
              </p>
              <Button
                onClick={() => setShowPasswordModal(true)}
                variant="outline"
                className="w-full sm:w-auto"
              >
                <Lock className="w-4 h-4 mr-2" />
                Change Password
              </Button>
            </div>

            <Separator />

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="2fa" className="text-base font-semibold">
                  Two-Factor Authentication
                </Label>
                <p className="text-sm text-gray-500">
                  Add an extra layer of security to your account
                </p>
              </div>
              <Switch
                id="2fa"
                checked={twoFactorEnabled}
                onCheckedChange={setTwoFactorEnabled}
              />
            </div>

            <Separator />

            <div>
              <Label htmlFor="session-timeout" className="text-base font-semibold">
                Session Timeout
              </Label>
              <p className="text-sm text-gray-500 mb-3">
                Automatically log out after period of inactivity
              </p>
              <Select value={sessionTimeout} onValueChange={setSessionTimeout}>
                <SelectTrigger id="session-timeout" className="w-full sm:w-64">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="15">15 minutes</SelectItem>
                  <SelectItem value="30">30 minutes</SelectItem>
                  <SelectItem value="60">1 hour</SelectItem>
                  <SelectItem value="120">2 hours</SelectItem>
                  <SelectItem value="never">Never</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Account Information */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="w-5 h-5" />
              Account Information
            </CardTitle>
            <CardDescription>
              View your account details
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <Label className="text-sm text-gray-500">Name</Label>
                <p className="font-semibold">{user.name}</p>
              </div>
              <div>
                <Label className="text-sm text-gray-500">Email</Label>
                <p className="font-semibold">{user.email}</p>
              </div>
              <div>
                <Label className="text-sm text-gray-500">Role</Label>
                <p className="font-semibold capitalize">{user.role}</p>
              </div>
              {user.beltRank && (
                <div>
                  <Label className="text-sm text-gray-500">Belt Rank</Label>
                  <p className="font-semibold">{user.beltRank}</p>
                </div>
              )}
            </div>
            <Separator />
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Smartphone className="w-4 h-4" />
              <span>To update your personal information, visit your Profile page</span>
            </div>
          </CardContent>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={() => window.location.reload()}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSaveSettings}
            className="bg-dojo-navy hover:bg-dojo-navy/90"
          >
            <CheckCircle2 className="w-4 h-4 mr-2" />
            Save Settings
          </Button>
        </div>
      </div>

      {/* Password Change Modal */}
      <Dialog open={showPasswordModal} onOpenChange={setShowPasswordModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Change Password</DialogTitle>
            <DialogDescription>
              Enter your current password and choose a new one. Your password must be at least 8 characters long.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="current-password">Current Password</Label>
              <Input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter current password"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-password">New Password</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm New Password</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowPasswordModal(false);
                setCurrentPassword("");
                setNewPassword("");
                setConfirmPassword("");
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handlePasswordChange}
              className="bg-dojo-navy hover:bg-dojo-navy/90"
            >
              Update Password
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
