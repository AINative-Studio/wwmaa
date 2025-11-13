"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type UserRole = "student" | "instructor" | "admin" | "member" | "board_member";

export type MembershipTier = "basic" | "premium" | "elite";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  avatar: string;
  membershipTier?: MembershipTier;
  beltRank?: string;
  dojo?: string;
}

export interface RegisterData {
  name: string;
  email: string;
  password: string;
  role: UserRole;
  membershipTier?: MembershipTier;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<boolean>;
  logout: () => void;
  register: (userData: RegisterData) => Promise<boolean>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = useCallback(async (email: string, password: string): Promise<boolean> => {
    try {
      // 1. Get CSRF token
      const csrfResponse = await fetch(`${API_URL}/api/security/csrf-token`, {
        credentials: 'include',
      });

      if (!csrfResponse.ok) {
        console.error('Failed to get CSRF token');
        return false;
      }

      const { csrf_token } = await csrfResponse.json();

      // 2. Login with credentials
      const loginResponse = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrf_token,
        },
        credentials: 'include',
        body: JSON.stringify({ email, password }),
      });

      if (!loginResponse.ok) {
        const error = await loginResponse.json();
        console.error('Login failed:', error);
        return false;
      }

      const data = await loginResponse.json();

      // 3. Store tokens and user data
      const userData: User = {
        id: data.user.id,
        name: `${data.user.first_name} ${data.user.last_name}`,
        email: data.user.email,
        role: data.user.role as UserRole,
        avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${data.user.email}`,
      };

      setUser(userData);

      if (typeof window !== "undefined") {
        localStorage.setItem("auth_user", JSON.stringify(userData));
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
      }

      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      const refreshToken = typeof window !== "undefined" ? localStorage.getItem("refresh_token") : null;

      // Call logout endpoint
      await fetch(`${API_URL}/api/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local state regardless of API call result
      setUser(null);
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_user");
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
      }
    }
  }, []);

  const register = useCallback(async (userData: RegisterData): Promise<boolean> => {
    try {
      // Get CSRF token
      const csrfResponse = await fetch(`${API_URL}/api/security/csrf-token`, {
        credentials: 'include',
      });

      if (!csrfResponse.ok) {
        console.error('Failed to get CSRF token');
        return false;
      }

      const { csrf_token } = await csrfResponse.json();

      // Register user
      const registerResponse = await fetch(`${API_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrf_token,
        },
        credentials: 'include',
        body: JSON.stringify({
          email: userData.email,
          password: userData.password,
          first_name: userData.name.split(' ')[0],
          last_name: userData.name.split(' ').slice(1).join(' ') || userData.name.split(' ')[0],
          terms_accepted: true,
        }),
      });

      if (!registerResponse.ok) {
        const error = await registerResponse.json();
        console.error('Registration failed:', error);
        return false;
      }

      return true;
    } catch (error) {
      console.error('Registration error:', error);
      return false;
    }
  }, []);

  // Check for stored user on mount
  React.useEffect(() => {
    if (typeof window !== "undefined") {
      const storedUser = localStorage.getItem("auth_user");
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch (e) {
          localStorage.removeItem("auth_user");
        }
      }
    }
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    login,
    logout,
    register,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
