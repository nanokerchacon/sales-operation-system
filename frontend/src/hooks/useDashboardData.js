import { useEffect, useState } from "react";
import { dashboardApi } from "../services/api";
import { normalizeCollection, normalizeObject } from "../utils/apiData";

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

const dashboardResources = {
  operations: {
    label: "operaciones",
    load: dashboardApi.getOperations,
    normalize: (value) => normalizeObject(value, null),
    fallback: null,
  },
  orderStatusSummary: {
    label: "resumen de estados",
    load: dashboardApi.getOrderStatusSummary,
    normalize: (value) => normalizeObject(value, null),
    fallback: null,
  },
  ordersWithIncidents: {
    label: "pedidos con incidencias",
    load: dashboardApi.getOrdersWithIncidents,
    normalize: (value) => normalizeCollection(value),
    fallback: [],
  },
  pendingInvoices: {
    label: "facturas pendientes",
    load: dashboardApi.getPendingInvoices,
    normalize: (value) => normalizeCollection(value),
    fallback: [],
  },
  pendingRevenue: {
    label: "revenue pendiente",
    load: dashboardApi.getPendingRevenue,
    normalize: (value) => normalizeCollection(value),
    fallback: [],
  },
  workQueue: {
    label: "cola de trabajo",
    load: dashboardApi.getWorkQueue,
    normalize: (value) => normalizeCollection(value),
    fallback: [],
  },
  clientsWithIncidents: {
    label: "clientes con incidencias",
    load: dashboardApi.getClientsWithIncidents,
    normalize: (value) => normalizeCollection(value),
    fallback: [],
  },
  agingInvoices: {
    label: "aging de facturas",
    load: dashboardApi.getAgingInvoices,
    normalize: (value) => normalizeObject(value, null),
    fallback: null,
  },
};

function getErrorMessage(error, fallbackLabel) {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  return `No se pudo cargar ${fallbackLabel}.`;
}

export default function useDashboardData() {
  const [data, setData] = useState(initialState);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [blockErrors, setBlockErrors] = useState({});
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    let isActive = true;

    async function loadDashboard() {
      setLoading(true);
      setError("");
      setBlockErrors({});

      const entries = Object.entries(dashboardResources);
      const results = await Promise.allSettled(
        entries.map(async ([key, config]) => {
          const response = await config.load();
          return [key, config.normalize(response)];
        }),
      );

      if (!isActive) {
        return;
      }

      const nextData = { ...initialState };
      const nextBlockErrors = {};
      let successCount = 0;

      results.forEach((result, index) => {
        const [key, config] = entries[index];

        if (result.status === "fulfilled") {
          const [, normalizedData] = result.value;
          nextData[key] = normalizedData;
          successCount += 1;
          return;
        }

        nextData[key] = config.fallback;
        nextBlockErrors[key] = getErrorMessage(result.reason, config.label);
      });

      setData(nextData);
      setBlockErrors(nextBlockErrors);
      setLastUpdated(successCount > 0 ? new Date() : null);

      if (successCount === 0) {
        setError("No se pudo cargar ningún bloque del dashboard.");
      } else if (Object.keys(nextBlockErrors).length > 0) {
        setError("Algunos bloques del dashboard no se han podido actualizar, pero el resto de la vista sigue disponible.");
      }

      setLoading(false);
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
    blockErrors,
    lastUpdated,
  };
}
