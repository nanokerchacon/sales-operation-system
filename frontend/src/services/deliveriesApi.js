import { apiClient } from "./api";

export const deliveriesApi = {
  list: () => apiClient.get("/deliveries"),
  getById: (deliveryId) => apiClient.get(`/deliveries/${deliveryId}`),
};
