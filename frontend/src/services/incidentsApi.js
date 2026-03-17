import { apiClient } from "./api";

export const incidentsApi = {
  list: () => apiClient.get("/incidents"),
  getById: (incidentId) => apiClient.get(`/incidents/${incidentId}`),
  create: (body) => apiClient.post("/incidents", body),
  generateDraft: (text) => apiClient.post("/incidents/generate", { text }),
  update: (incidentId, body) => apiClient.patch(`/incidents/${incidentId}`, body),
};
