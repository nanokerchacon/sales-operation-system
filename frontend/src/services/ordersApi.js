import { apiClient } from "./api";

export const ordersApi = {
  getTraceability: (orderId) => apiClient.get(`/orders/${orderId}/traceability`),
};
