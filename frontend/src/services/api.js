const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001";

async function request(path) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`Error ${response.status} al consultar ${path}`);
  }

  return response.json();
}

export const dashboardApi = {
  getOperations: () => request("/dashboard/operations"),
  getRiskOrders: () => request("/dashboard/risk-orders"),
  getPendingInvoices: () => request("/dashboard/pending-invoices"),
  getRevenueAtRisk: () => request("/dashboard/revenue-at-risk"),
  getWorkQueue: () => request("/dashboard/work-queue"),
  getClientRisk: () => request("/dashboard/client-risk"),
  getAgingInvoices: () => request("/dashboard/aging-invoices"),
};

export { API_BASE_URL };
