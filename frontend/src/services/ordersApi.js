import { apiClient } from "./api";

export const ordersApi = {
  list: () => apiClient.get("/orders"),
  getById: (orderId) => apiClient.get(`/orders/${orderId}`),
  getTraceability: (orderId) => apiClient.get(`/orders/${orderId}/traceability`),
};
