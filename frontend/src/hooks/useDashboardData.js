import { useEffect, useState } from "react";
import { dashboardApi } from "../services/api";

const initialState = {
  operations: null,
  orderStatusSummary: null,
  ordersWithIncidents: [],
  pendingInvoices: [],
  pendingRevenue: [],
  workQueue: [],
  clientsWithIncidents: [],
  agingInvoices: null,
};

export default function useDashboardData() {
  const [data, setData] = useState(initialState);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    let isActive = true;

    async function loadDashboard() {
      setLoading(true);
      setError("");

      try {
        const [
          operations,
          orderStatusSummary,
          ordersWithIncidents,
          pendingInvoices,
          pendingRevenue,
          workQueue,
          clientsWithIncidents,
          agingInvoices,
        ] = await Promise.all([
          dashboardApi.getOperations(),
          dashboardApi.getOrderStatusSummary(),
          dashboardApi.getOrdersWithIncidents(),
          dashboardApi.getPendingInvoices(),
          dashboardApi.getPendingRevenue(),
          dashboardApi.getWorkQueue(),
          dashboardApi.getClientsWithIncidents(),
          dashboardApi.getAgingInvoices(),
        ]);

        if (!isActive) {
          return;
        }

        setData({
          operations,
          orderStatusSummary,
          ordersWithIncidents,
          pendingInvoices,
          pendingRevenue,
          workQueue,
          clientsWithIncidents,
          agingInvoices,
        });
        setLastUpdated(new Date());
      } catch (requestError) {
        if (!isActive) {
          return;
        }

        setError(
          requestError instanceof Error
            ? requestError.message
            : "No se pudo cargar la informacion del dashboard.",
        );
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => {
      isActive = false;
    };
  }, []);

  return {
    data,
    loading,
    error,
    lastUpdated,
  };
}
