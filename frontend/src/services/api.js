const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`Error ${response.status} al consultar ${path}`);
  }

  return response.json();
}

export const dashboardApi = {
  getOperations: () => request("/dashboard/operations"),
  getOrderStatusSummary: () => request("/dashboard/order-status-summary"),
  getOrdersWithIncidents: () => request("/dashboard/orders-with-incidents"),
  getRiskOrders: () => request("/dashboard/risk-orders"),
  getPendingInvoices: () => request("/dashboard/pending-invoices"),
  getPendingRevenue: () => request("/dashboard/pending-revenue"),
  getRevenueAtRisk: () => request("/dashboard/revenue-at-risk"),
  getWorkQueue: () => request("/dashboard/work-queue"),
  getClientsWithIncidents: () => request("/dashboard/clients-with-incidents"),
  getClientRisk: () => request("/dashboard/client-risk"),
  getAgingInvoices: () => request("/dashboard/aging-invoices"),
};

export const apiClient = {
  get: (path) => request(path),
  post: (path, body) =>
    request(path, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  put: (path, body) =>
    request(path, {
      method: "PUT",
      body: JSON.stringify(body),
    }),
  delete: (path) =>
    request(path, {
      method: "DELETE",
    }),
};

export { API_BASE_URL };
