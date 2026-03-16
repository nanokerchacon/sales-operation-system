import { translateStatus } from "../services/statusTranslation";

export function getPriorityTone(value) {
  if (value === "high" || value === "Alta") {
    return "high";
  }

  if (value === "medium" || value === "Media") {
    return "medium";
  }

  return "low";
}

export function getDisplayStatus(status) {
  return translateStatus(status);
}
