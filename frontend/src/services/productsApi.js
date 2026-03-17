import { apiClient } from "./api";

export const productsApi = {
  list: () => apiClient.get("/products"),
};
