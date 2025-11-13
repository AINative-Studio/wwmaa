import { UserRole } from "@/lib/auth-context";
import { cn } from "@/lib/utils";
import { GraduationCap, Shield, User } from "lucide-react";

interface RoleBadgeProps {
  role: UserRole;
  variant?: "default" | "compact";
  showIcon?: boolean;
  className?: string;
}

const roleConfig: Record<
  UserRole,
  {
    label: string;
    color: string;
    bgColor: string;
    borderColor: string;
    icon: typeof User;
  }
> = {
  student: {
    label: "Student",
    color: "text-blue-700",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    icon: User,
  },
  instructor: {
    label: "Instructor",
    color: "text-green-700",
    bgColor: "bg-green-50",
    borderColor: "border-green-200",
    icon: GraduationCap,
  },
  admin: {
    label: "Admin",
    color: "text-orange-700",
    bgColor: "bg-orange-50",
    borderColor: "border-orange-200",
    icon: Shield,
  },
  member: {
    label: "Member",
    color: "text-blue-700",
    bgColor: "bg-blue-50",
    borderColor: "border-blue-200",
    icon: User,
  },
  board_member: {
    label: "Board Member",
    color: "text-purple-700",
    bgColor: "bg-purple-50",
    borderColor: "border-purple-200",
    icon: Shield,
  },
};

export function RoleBadge({
  role,
  variant = "default",
  showIcon = true,
  className,
}: RoleBadgeProps) {
  const config = roleConfig[role];
  const Icon = config.icon;

  if (variant === "compact") {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium border",
          config.color,
          config.bgColor,
          config.borderColor,
          className
        )}
      >
        {showIcon && <Icon className="h-3 w-3" />}
        {config.label}
      </span>
    );
  }

  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-sm font-medium border",
        config.color,
        config.bgColor,
        config.borderColor,
        className
      )}
    >
      {showIcon && <Icon className="h-4 w-4" />}
      {config.label}
    </div>
  );
}
