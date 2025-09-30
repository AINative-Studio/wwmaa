"use client";

import { ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth, UserRole } from "@/lib/auth-context";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ShieldAlert } from "lucide-react";

interface ProtectedRouteProps {
  children: ReactNode;
  allowedRoles?: UserRole[];
  requireAuth?: boolean;
}

export function ProtectedRoute({
  children,
  allowedRoles,
  requireAuth = true,
}: ProtectedRouteProps) {
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Redirect to login if authentication is required but user is not authenticated
    if (requireAuth && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, requireAuth, router]);

  // If not authenticated and auth is required, show nothing (will redirect)
  if (requireAuth && !isAuthenticated) {
    return null;
  }

  // If authenticated but role is not allowed
  if (isAuthenticated && allowedRoles && user && !allowedRoles.includes(user.role)) {
    return (
      <div className="container mx-auto px-6 py-16">
        <Alert variant="destructive" className="max-w-2xl mx-auto">
          <ShieldAlert className="h-5 w-5" />
          <AlertTitle className="text-lg font-semibold">Access Denied</AlertTitle>
          <AlertDescription className="mt-2">
            You do not have permission to access this page. This page is restricted to{" "}
            {allowedRoles.map((role, idx) => (
              <span key={role}>
                {idx > 0 && idx === allowedRoles.length - 1 && " and "}
                {idx > 0 && idx < allowedRoles.length - 1 && ", "}
                <span className="font-semibold capitalize">{role}</span>
                {idx === 0 && allowedRoles.length === 1 && "s"}
              </span>
            ))}{" "}
            only.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return <>{children}</>;
}

// HOC version for wrapping page components
export function withAuth<P extends object>(
  Component: React.ComponentType<P>,
  allowedRoles?: UserRole[]
) {
  return function AuthenticatedComponent(props: P) {
    return (
      <ProtectedRoute allowedRoles={allowedRoles}>
        <Component {...props} />
      </ProtectedRoute>
    );
  };
}
