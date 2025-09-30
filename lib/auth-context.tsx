"use client";

import React, { createContext, useContext, useState, useCallback, ReactNode } from "react";

export type UserRole = "student" | "instructor" | "admin";

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

// Mock users for demo purposes
const MOCK_USERS: User[] = [
  {
    id: "1",
    name: "Sarah Chen",
    email: "student@demo.com",
    role: "student",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah",
    membershipTier: "premium",
    beltRank: "Blue Belt",
    dojo: "San Francisco Dojo",
  },
  {
    id: "2",
    name: "Mike Johnson",
    email: "instructor@demo.com",
    role: "instructor",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Mike",
    beltRank: "3rd Degree Black Belt",
    dojo: "Los Angeles Dojo",
  },
  {
    id: "3",
    name: "Admin User",
    email: "admin@demo.com",
    role: "admin",
    avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Admin",
  },
];

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  const login = useCallback(async (email: string, password: string): Promise<boolean> => {
    // Mock authentication - accept any password for demo
    const foundUser = MOCK_USERS.find((u) => u.email.toLowerCase() === email.toLowerCase());

    if (foundUser) {
      setUser(foundUser);
      // In a real app, you would store the token in localStorage/cookies
      if (typeof window !== "undefined") {
        localStorage.setItem("auth_user", JSON.stringify(foundUser));
      }
      return true;
    }

    return false;
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth_user");
    }
  }, []);

  const register = useCallback(async (userData: RegisterData): Promise<boolean> => {
    // Mock registration - just create a new user
    const newUser: User = {
      id: `user_${Date.now()}`,
      name: userData.name,
      email: userData.email,
      role: userData.role,
      avatar: `https://api.dicebear.com/7.x/avataaars/svg?seed=${userData.name}`,
      membershipTier: userData.membershipTier,
    };

    setUser(newUser);
    if (typeof window !== "undefined") {
      localStorage.setItem("auth_user", JSON.stringify(newUser));
    }

    return true;
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
