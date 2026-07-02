import {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  AUTH_TOKEN_KEY,
  clearAuthToken,
  fetchMe,
  login as loginRequest,
  setAuthToken,
} from "../services/api";
import type { User, UserRole } from "../types/user";

const AUTH_USER_KEY = "prescripta_user";

type AuthContextValue = {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  canAccess: (roles: UserRole[]) => boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredUser() {
  const rawUser = localStorage.getItem(AUTH_USER_KEY);
  if (!rawUser) {
    return null;
  }
  try {
    return JSON.parse(rawUser) as User;
  } catch {
    localStorage.removeItem(AUTH_USER_KEY);
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState(() => localStorage.getItem(AUTH_TOKEN_KEY));
  const [user, setUser] = useState<User | null>(() => readStoredUser());
  const [isLoading, setIsLoading] = useState(Boolean(token));

  function logout() {
    clearAuthToken();
    localStorage.removeItem(AUTH_USER_KEY);
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
    if (!token) {
      setIsLoading(false);
      return;
    }

    let isMounted = true;
    fetchMe()
      .then((currentUser) => {
        if (!isMounted) {
          return;
        }
        setUser(currentUser);
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(currentUser));
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
  }, [token]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isLoading,
      async login(email: string, password: string) {
        const response = await loginRequest({ email, password });
        setAuthToken(response.access_token);
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(response.user));
        setToken(response.access_token);
        setUser(response.user);
      },
      logout,
      canAccess(roles: UserRole[]) {
        return Boolean(user && roles.includes(user.role));
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
