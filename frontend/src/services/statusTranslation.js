export const statusTranslation = {
  draft: "Borrador",
  confirmed: "Confirmado",
  pending: "Pendiente",
  delivered: "Entregado",
  invoiced: "Facturado",
  completed: "Completado",
  ok: "Completo",
  pending_delivery: "Pendiente de entrega",
  pending_invoice: "Pendiente de facturar",
  invoice_pending_acceptance: "Pendiente de aceptación",
  invoice_over_delivery: "Error de facturacion",
  not_invoiced: "Sin factura emitida",
  invoice_issued: "Factura emitida",
  invoice_accepted: "Factura aceptada",
  accepted: "Aceptada",
  pending_acceptance: "Pendiente de aceptación",
  rectified_review: "En revisión rectificativa",
  national: "Nacional",
  intracommunity: "Intracomunitaria",
  export: "Exportación",
  commercial_invoice: "Commercial invoice",
  electronic: "Electrónica",
  rectificative: "Rectificativa",
  low: "Baja",
  medium: "Media",
  high: "Alta",
  none: "Sin incidencias",
};

export function translateStatus(status) {
  return statusTranslation[status] || status || "-";
}
