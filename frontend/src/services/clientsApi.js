import { apiClient } from "./api";

export const clientsApi = {
  list: () => apiClient.get("/clients"),
  getById: (clientId) => apiClient.get(`/clients/${clientId}`),
  getOrders: (clientId) => apiClient.get(`/clients/${clientId}/orders`),
};
