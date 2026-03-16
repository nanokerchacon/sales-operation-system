import { apiClient } from "./api";

export const incidentsApi = {
  list: () => apiClient.get("/incidents"),
  getById: (incidentId) => apiClient.get(`/incidents/${incidentId}`),
  create: (body) => apiClient.post("/incidents", body),
  update: (incidentId, body) => apiClient.patch(`/incidents/${incidentId}`, body),
};
