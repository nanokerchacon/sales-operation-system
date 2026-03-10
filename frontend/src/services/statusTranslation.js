export const statusTranslation = {
  draft: "Borrador",
  completed: "Completado",
  delivered_not_invoiced: "Entregado no facturado",
  partially_invoiced: "Facturación parcial",
  low: "Riesgo bajo",
  medium: "Riesgo medio",
  high: "Riesgo alto",
  none: "Sin riesgo",
};

export function translateStatus(status) {
  return statusTranslation[status] || status || "-";
}
