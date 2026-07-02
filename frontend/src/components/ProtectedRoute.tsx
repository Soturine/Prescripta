import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import type { UserRole } from "../types/user";
import LoadingState from "./LoadingState";

type ProtectedRouteProps = {
  roles?: UserRole[];
};

export default function ProtectedRoute({ roles }: ProtectedRouteProps) {
  const { canAccess, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingState label="Validando sessão" />;
  }

  if (!isAuthenticated) {
    return <Navigate replace to="/login" />;
  }

  if (roles && !canAccess(roles)) {
    return <Navigate replace to="/access-denied" />;
  }

  return <Outlet />;
}
