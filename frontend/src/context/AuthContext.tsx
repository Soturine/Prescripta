import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  clearAuthToken,
  fetchMe,
  login as loginRequest,
  logoutSession,
} from "../services/api";
import type { Capability, User, UserRole } from "../types/user";

type AuthContextValue = {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, mfaCode?: string) => Promise<void>;
  logout: () => void;
  canAccess: (roles: UserRole[]) => boolean;
  can: (...capabilities: Capability[]) => boolean;
  canAny: (...capabilities: Capability[]) => boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  function logout() {
    clearAuthToken();
    void logoutSession();
    setToken(null);
    setUser(null);
  }

  useEffect(() => {
    function handleExpiredSession() {
      logout();
    }

    window.addEventListener("prescripta:auth-expired", handleExpiredSession);
    return () => window.removeEventListener("prescripta:auth-expired", handleExpiredSession);
  }, []);

  useEffect(() => {
    let isMounted = true;
    fetchMe()
      .then((currentUser) => {
        if (!isMounted) {
          return;
        }
        setUser(currentUser);
        setToken("cookie-session");
      })
      .catch(() => {
        if (isMounted) {
          logout();
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isLoading,
      async login(email: string, password: string, mfaCode?: string) {
        const response = await loginRequest({ email, password, mfa_code: mfaCode || undefined });
        clearAuthToken();
        setToken("cookie-session");
        setUser(response.user);
      },
      logout,
      canAccess(roles: UserRole[]) {
        return Boolean(user && roles.includes(user.role));
      },
      can(...capabilities: Capability[]) {
        const available = new Set(user?.capabilities ?? []);
        return Boolean(user && capabilities.every((capability) => available.has(capability)));
      },
      canAny(...capabilities: Capability[]) {
        const available = new Set(user?.capabilities ?? []);
        return Boolean(user && capabilities.some((capability) => available.has(capability)));
      },
    }),
    [isLoading, token, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth deve ser usado dentro de AuthProvider.");
  }
  return context;
}
