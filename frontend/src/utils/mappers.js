import { translateStatus } from "../services/statusTranslation";

export const navigationItems = [
  { key: "dashboard", label: "Dashboard", href: "/" },
  { key: "pedidos", label: "Pedidos", href: null },
  { key: "albaranes", label: "Albaranes", href: null },
  { key: "facturas", label: "Facturas", href: null },
  { key: "incidencias", label: "Incidencias", href: null },
  { key: "clientes", label: "Clientes", href: null },
  { key: "productos", label: "Productos", href: null },
];

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

export function navigateTo(path) {
  if (!path) {
    return;
  }

  if (window.location.pathname === path) {
    return;
  }

  window.history.pushState({}, "", path);
  window.dispatchEvent(new PopStateEvent("popstate"));
}
