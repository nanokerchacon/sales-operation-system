import { translateStatus } from "../services/statusTranslation";

export function getPriorityTone(value) {
  if (["critica", "critical"].includes(value)) {
    return "critical";
  }

  if (["high", "alta", "Alta"].includes(value)) {
    return "high";
  }

  if (["medium", "media", "Media"].includes(value)) {
    return "medium";
  }

  return "low";
}

export function getDisplayStatus(status) {
  return translateStatus(status);
}
