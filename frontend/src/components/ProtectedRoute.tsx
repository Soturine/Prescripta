import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import type { Capability, UserRole } from "../types/user";
import LoadingState from "./LoadingState";

type ProtectedRouteProps = {
  roles?: UserRole[];
  capabilities?: Capability[];
  requireAnyCapability?: boolean;
};

export default function ProtectedRoute({
  roles,
  capabilities,
  requireAnyCapability = false,
}: ProtectedRouteProps) {
  const { can, canAccess, canAny, isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingState label="Validando sessão" />;
  }

  if (!isAuthenticated) {
    return <Navigate replace to="/login" />;
  }

  if (roles && !canAccess(roles)) {
    return <Navigate replace to="/access-denied" />;
  }

  if (
    capabilities?.length &&
    !(requireAnyCapability ? canAny(...capabilities) : can(...capabilities))
  ) {
    return <Navigate replace to="/access-denied" />;
  }

  return <Outlet />;
}
