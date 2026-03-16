import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";

export default function RequirePermission({ permission, children }) {
  const { user } = useAuth();

  if (!user?.permissions?.includes(permission)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
