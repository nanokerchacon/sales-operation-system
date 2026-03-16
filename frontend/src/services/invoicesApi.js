import { apiClient } from "./api";

export const invoicesApi = {
  list: () => apiClient.get("/invoices"),
  getById: (invoiceId) => apiClient.get(`/invoices/${invoiceId}`),
};
