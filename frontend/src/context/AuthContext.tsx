import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, StudentProfile } from '../types';
import { getCurrentUser, loginUser, registerUser, logoutUser, LoginPayload, RegisterPayload } from '../api/auth';
import { getProfile } from '../api/profile';

interface AuthContextType {
  user: User | null;
  profile: StudentProfile | null;
  loading: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchSession = async () => {
    try {
      const u = await getCurrentUser();
      setUser(u);
      try {
        const p = await getProfile();
        setProfile(p);
      } catch {
        setProfile(null);
      }
    } catch {
      setUser(null);
      setProfile(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSession();
  }, []);

  const login = async (payload: LoginPayload) => {
    const res = await loginUser(payload);
    setUser(res.user);
    try {
      const p = await getProfile();
      setProfile(p);
    } catch {
      setProfile(null);
    }
  };

  const register = async (payload: RegisterPayload) => {
    const res = await registerUser(payload);
    setUser(res.user);
    try {
      const p = await getProfile();
      setProfile(p);
    } catch {
      setProfile(null);
    }
  };

  const logout = async () => {
    try {
      await logoutUser();
    } catch (e) {
      console.error(e);
    }
    setUser(null);
    setProfile(null);
  };

  const refreshProfile = async () => {
    try {
      const p = await getProfile();
      setProfile(p);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        loading,
        login,
        register,
        logout,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

