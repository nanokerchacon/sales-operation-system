import { translateStatus } from "../services/statusTranslation";

export const navigationItems = [
  { key: "dashboard", label: "Dashboard", active: true },
  { key: "pedidos", label: "Pedidos", active: false },
  { key: "albaranes", label: "Albaranes", active: false },
  { key: "facturas", label: "Facturas", active: false },
  { key: "riesgos", label: "Riesgos", active: false },
  { key: "clientes", label: "Clientes", active: false },
  { key: "productos", label: "Productos", active: false },
];

export function getRiskTone(value) {
  if (value === "high" || value === "Riesgo alto") {
    return "high";
  }

  if (value === "medium" || value === "Riesgo medio") {
    return "medium";
  }

  return "low";
}

export function getDisplayStatus(status) {
  return translateStatus(status);
}
