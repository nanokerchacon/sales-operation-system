export const statusTranslation = {
  draft: "Borrador",
  completed: "Completado",
  ok: "Completo",
  pending_delivery: "Pendiente de entrega",
  pending_invoice: "Pendiente de facturar",
  invoice_over_delivery: "Error de facturación",
  low: "Baja",
  medium: "Media",
  high: "Alta",
  none: "Sin incidencias",
};

export function translateStatus(status) {
  return statusTranslation[status] || status || "-";
}
