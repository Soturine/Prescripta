import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
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

// Sincroniza logout entre abas do mesmo navegador. Nunca transporta token: só um sinal.
const AUTH_CHANNEL = "prescripta-auth";

function openAuthChannel(): BroadcastChannel | null {
  return typeof BroadcastChannel === "undefined" ? null : new BroadcastChannel(AUTH_CHANNEL);
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  // Cada login/logout abre uma nova "época". Respostas iniciadas numa época anterior (ex.: o
  // fetchMe lento do carregamento da página) não podem derrubar uma sessão criada depois.
  const sessionEpoch = useRef(0);
  // Login aguarda o logout em voo: senão o Set-Cookie de remoção do logout pode chegar depois
  // do cookie novo do login e apagá-lo.
  const pendingLogout = useRef<Promise<unknown>>(Promise.resolve());
  const channel = useRef<BroadcastChannel | null>(null);

  const clearLocalSession = useCallback(() => {
    sessionEpoch.current += 1;
    clearAuthToken();
    setToken(null);
    setUser(null);
  }, []);

  const logout = useCallback(() => {
    clearLocalSession();
    pendingLogout.current = Promise.resolve(logoutSession()).catch(() => undefined);
    channel.current?.postMessage("logout");
  }, [clearLocalSession]);

  useEffect(() => {
    const opened = openAuthChannel();
    channel.current = opened;
    if (opened) {
      opened.onmessage = (event: MessageEvent) => {
        if (event.data === "logout") clearLocalSession();
      };
    }
    return () => {
      opened?.close();
      channel.current = null;
    };
  }, [clearLocalSession]);

  useEffect(() => {
    function handleExpiredSession() {
      logout();
    }

    window.addEventListener("prescripta:auth-expired", handleExpiredSession);
    return () => window.removeEventListener("prescripta:auth-expired", handleExpiredSession);
  }, [logout]);

  useEffect(() => {
    let isMounted = true;
    const startedEpoch = sessionEpoch.current;
    const isCurrent = () => isMounted && sessionEpoch.current === startedEpoch;
    fetchMe()
      .then((currentUser) => {
        if (!isCurrent()) {
          return;
        }
        setUser(currentUser);
        setToken("cookie-session");
      })
      .catch(() => {
        if (isCurrent()) {
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
  }, [logout]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      token,
      isAuthenticated: Boolean(token && user),
      isLoading,
      async login(email: string, password: string, mfaCode?: string) {
        sessionEpoch.current += 1;
        await pendingLogout.current;
        const response = await loginRequest({ email, password, mfa_code: mfaCode || undefined });
        clearAuthToken();
        setToken("cookie-session");
        setUser(response.user);
        setIsLoading(false);
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
    [isLoading, logout, token, user],
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
