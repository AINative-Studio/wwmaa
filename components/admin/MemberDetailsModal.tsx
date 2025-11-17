"use client";

import { useState, useEffect } from "react";
import { User } from "@/lib/types";
import { adminApi } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  User as UserIcon,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Shield,
  Activity,
  AlertCircle,
} from "lucide-react";

interface MemberDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  member: User | null;
  mode: "view" | "edit" | "create";
  onSave: () => void;
}

export function MemberDetailsModal({
  isOpen,
  onClose,
  member,
  mode,
  onSave,
}: MemberDetailsModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    email: "",
    first_name: "",
    last_name: "",
    password: "",
    role: "member",
    is_active: true,
    phone: "",
  });

  // Initialize form data when member changes
  useEffect(() => {
    if (member && (mode === "edit" || mode === "view")) {
      setFormData({
        email: member.email || "",
        first_name: member.first_name || "",
        last_name: member.last_name || "",
        password: "",
        role: member.role || "member",
        is_active: true, // Backend will need to provide this
        phone: member.phone || "",
      });
    } else if (mode === "create") {
      setFormData({
        email: "",
        first_name: "",
        last_name: "",
        password: "",
        role: "member",
        is_active: true,
        phone: "",
      });
    }
    setError(null);
  }, [member, mode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (mode === "create") {
      if (!formData.email || !formData.first_name || !formData.last_name || !formData.password) {
        setError("Please fill in all required fields");
        return;
      }
      if (formData.password.length < 8) {
        setError("Password must be at least 8 characters");
        return;
      }
    }

    try {
      setLoading(true);

      if (mode === "create") {
        await adminApi.createMember(formData);
      } else if (mode === "edit" && member) {
        // Only send changed fields
        const updateData: any = {};
        if (formData.email !== member.email) updateData.email = formData.email;
        if (formData.first_name !== member.first_name) updateData.first_name = formData.first_name;
        if (formData.last_name !== member.last_name) updateData.last_name = formData.last_name;
        if (formData.role !== member.role) updateData.role = formData.role;
        if (formData.phone !== member.phone) updateData.phone = formData.phone;
        if (formData.password) updateData.password = formData.password;

        await adminApi.updateMember(member.id, updateData);
      }

      onSave();
    } catch (err: any) {
      setError(err.message || "Failed to save member");
      console.error("Member save error:", err);
    } finally {
      setLoading(false);
    }
  };

  const formatRole = (role: string) => {
    return role
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(" ");
  };

  const formatDate = (dateString: string | undefined) => {
    if (!dateString) return "N/A";
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "N/A";
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {mode === "create" && "Add New Member"}
            {mode === "edit" && "Edit Member"}
            {mode === "view" && "Member Details"}
          </DialogTitle>
          <DialogDescription>
            {mode === "create" && "Create a new member account with user credentials"}
            {mode === "edit" && "Update member information and account settings"}
            {mode === "view" && "View member profile and activity information"}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {mode === "view" && member ? (
          <Tabs defaultValue="profile" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="profile">Profile</TabsTrigger>
              <TabsTrigger value="activity">Activity</TabsTrigger>
            </TabsList>

            <TabsContent value="profile" className="space-y-4 mt-4">
              {/* Profile View */}
              <div className="space-y-4">
                <div className="flex items-start gap-4">
                  {member.avatar_url ? (
                    <img
                      src={member.avatar_url}
                      alt={member.name}
                      className="w-20 h-20 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-20 h-20 rounded-full bg-gradient-navy flex items-center justify-center text-white text-2xl font-semibold">
                      {(member.first_name?.[0] || member.name?.[0] || "?").toUpperCase()}
                      {(member.last_name?.[0] || member.name?.[1] || "").toUpperCase()}
                    </div>
                  )}
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-gray-900">
                      {member.first_name && member.last_name
                        ? `${member.first_name} ${member.last_name}`
                        : member.display_name || member.name}
                    </h3>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-xs">
                        {formatRole(member.role)}
                      </Badge>
                      <Badge variant="default" className="text-xs bg-green-100 text-green-800 border-green-200">
                        Active
                      </Badge>
                    </div>
                  </div>
                </div>

                <Separator />

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Mail className="w-4 h-4" />
                      Email
                    </div>
                    <div className="text-sm font-medium">{member.email}</div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Phone className="w-4 h-4" />
                      Phone
                    </div>
                    <div className="text-sm font-medium">{member.phone || "—"}</div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <MapPin className="w-4 h-4" />
                      Location
                    </div>
                    <div className="text-sm font-medium">
                      {member.city && member.state
                        ? `${member.city}, ${member.state}`
                        : member.country || "—"}
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Shield className="w-4 h-4" />
                      Belt Rank
                    </div>
                    <div className="text-sm font-medium">{member.belt_rank || "—"}</div>
                  </div>
                </div>

                {member.bio && (
                  <>
                    <Separator />
                    <div className="space-y-2">
                      <div className="text-sm font-medium text-gray-700">Bio</div>
                      <p className="text-sm text-gray-600">{member.bio}</p>
                    </div>
                  </>
                )}
              </div>
            </TabsContent>

            <TabsContent value="activity" className="space-y-4 mt-4">
              {/* Activity View - Placeholder */}
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="w-12 h-12 mx-auto mb-4 text-muted-foreground/50" />
                <p className="text-sm">Activity tracking coming soon</p>
                <p className="text-xs mt-2">View member login history, events attended, and more</p>
              </div>
            </TabsContent>
          </Tabs>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              {/* Name Fields */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="first_name">
                    First Name {mode === "create" && <span className="text-red-500">*</span>}
                  </Label>
                  <Input
                    id="first_name"
                    placeholder="John"
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    disabled={mode === "view"}
                    required={mode === "create"}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="last_name">
                    Last Name {mode === "create" && <span className="text-red-500">*</span>}
                  </Label>
                  <Input
                    id="last_name"
                    placeholder="Smith"
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    disabled={mode === "view"}
                    required={mode === "create"}
                  />
                </div>
              </div>

              {/* Email */}
              <div className="space-y-2">
                <Label htmlFor="email">
                  Email {mode === "create" && <span className="text-red-500">*</span>}
                </Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="john.smith@example.com"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  disabled={mode === "view"}
                  required={mode === "create"}
                />
              </div>

              {/* Password */}
              {mode !== "view" && (
                <div className="space-y-2">
                  <Label htmlFor="password">
                    Password {mode === "create" && <span className="text-red-500">*</span>}
                  </Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder={mode === "edit" ? "Leave blank to keep current password" : "Min. 8 characters"}
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    required={mode === "create"}
                  />
                  {mode === "create" && (
                    <p className="text-xs text-muted-foreground">
                      Must be at least 8 characters with uppercase, lowercase, and numbers
                    </p>
                  )}
                </div>
              )}

              {/* Phone */}
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="+1 (555) 123-4567"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  disabled={mode === "view"}
                />
              </div>

              {/* Role */}
              <div className="space-y-2">
                <Label htmlFor="role">Role</Label>
                <Select
                  value={formData.role}
                  onValueChange={(value) => setFormData({ ...formData, role: value })}
                  disabled={mode === "view"}
                >
                  <SelectTrigger id="role">
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

              {/* Active Status */}
              {mode !== "view" && (
                <div className="flex items-center gap-2">
                  <Switch
                    id="is_active"
                    checked={formData.is_active}
                    onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
                  />
                  <Label htmlFor="is_active">Active Account</Label>
                </div>
              )}
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={loading}
              >
                Cancel
              </Button>
              {mode !== "view" && (
                <Button type="submit" disabled={loading}>
                  {loading ? "Saving..." : mode === "create" ? "Create Member" : "Update Member"}
                </Button>
              )}
            </DialogFooter>
          </form>
        )}

        {mode === "view" && (
          <DialogFooter>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  );
}
