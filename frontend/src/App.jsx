import { Navigate, Route, Routes } from "react-router-dom";
import RequireAuth from "./components/RequireAuth";
import RequirePermission from "./components/RequirePermission";
import AppLayout from "./layouts/AppLayout";
import ClientDetailPage from "./pages/ClientDetailPage";
import ClientsPage from "./pages/ClientsPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import ModulePlaceholderPage from "./pages/ModulePlaceholderPage";
import OrderDetailPage from "./pages/OrderDetailPage";
import OrdersPage from "./pages/OrdersPage";
import OrderTraceabilityPage from "./pages/OrderTraceabilityPage";

function ProtectedModule({ permission, title, description }) {
  return (
    <RequirePermission permission={permission}>
      <ModulePlaceholderPage title={title} description={description} />
    </RequirePermission>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route
          path="dashboard"
          element={
            <RequirePermission permission="dashboard.view">
              <DashboardPage />
            </RequirePermission>
          }
        />
        <Route
          path="clients"
          element={
            <RequirePermission permission="clients.view">
              <ClientsPage />
            </RequirePermission>
          }
        />
        <Route
          path="clients/:clientId"
          element={
            <RequirePermission permission="clients.view">
              <ClientDetailPage />
            </RequirePermission>
          }
        />
        <Route
          path="orders"
          element={
            <RequirePermission permission="orders.view">
              <OrdersPage />
            </RequirePermission>
          }
        />
        <Route
          path="orders/:orderId"
          element={
            <RequirePermission permission="orders.view">
              <OrderDetailPage />
            </RequirePermission>
          }
        />
        <Route
          path="orders/:orderId/traceability"
          element={
            <RequirePermission permission="orders.view">
              <OrderTraceabilityPage />
            </RequirePermission>
          }
        />
        <Route path="deliveries" element={<ProtectedModule permission="deliveries.view" title="Albaranes" description="Vista protegida del módulo de albaranes." />} />
        <Route path="invoices" element={<ProtectedModule permission="invoices.view" title="Facturas" description="Vista protegida del módulo de facturas." />} />
        <Route path="products" element={<ProtectedModule permission="products.view" title="Productos" description="Vista protegida del módulo de productos." />} />
        <Route path="incidents" element={<ProtectedModule permission="incidents.view" title="Incidencias" description="Vista protegida del módulo de incidencias." />} />
        <Route path="admin/users" element={<ProtectedModule permission="admin.view" title="Administración" description="Base preparada para usuarios, roles y asignaciones." />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
