import KpiCard from "./KpiCard";

function buildCards(summary) {
  if (!summary) {
    return [];
  }

  return [
    {
      key: "ok",
      title: summary.labels_es.ok,
      value: summary.ok,
      detail: "Pedidos con entrega y facturación alineadas.",
      tone: "success",
    },
    {
      key: "pending_delivery",
      title: summary.labels_es.pending_delivery,
      value: summary.pending_delivery,
      detail: "Pedidos todavía pendientes de servir.",
      tone: "alert",
    },
    {
      key: "pending_invoice",
      title: summary.labels_es.pending_invoice,
      value: summary.pending_invoice,
      detail: "Pedidos entregados pendientes de facturar.",
      tone: "default",
    },
    {
      key: "invoice_over_delivery",
      title: summary.labels_es.invoice_over_delivery,
      value: summary.invoice_over_delivery,
      detail: "Facturación superior a la entrega registrada.",
      tone: "alert",
    },
  ];
}

export default function StatusSummaryCards({ summary, formatValue }) {
  return (
    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
      {buildCards(summary).map((card) => (
        <KpiCard
          key={card.key}
          title={card.title}
          value={formatValue(card.value)}
          detail={card.detail}
          tone={card.tone}
        />
      ))}
    </div>
  );
}
