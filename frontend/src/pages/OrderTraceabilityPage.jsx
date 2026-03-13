import { useEffect, useState } from "react";
import DataTable from "../components/DataTable";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import LoadingState from "../components/LoadingState";
import OperationalStatusBadge from "../components/OperationalStatusBadge";
import SectionCard from "../components/SectionCard";
import SummaryCard from "../components/SummaryCard";
import { ordersApi } from "../services/ordersApi";
import { formatCurrency, formatDate, formatNumber } from "../utils/formatters";

function buildSummaryCards(summary) {
  if (!summary) {
    return [];
  }

  return [
    {
      title: "Pedido",
      value: formatNumber(summary.total_ordered_quantity),
      detail: "Cantidad total pedida.",
    },
    {
      title: "Entregado",
      value: formatNumber(summary.total_delivered_quantity),
      detail: "Cantidad total entregada.",
    },
    {
      title: "Facturado aceptado",
      value: formatNumber(summary.total_invoiced_quantity),
      detail: "Cantidad documentalmente aceptada.",
    },
    {
      title: "Emitido",
      value: formatNumber(summary.total_issued_quantity),
      detail: "Cantidad con factura emitida.",
    },
    {
      title: "Pendiente aceptación",
      value: formatNumber(summary.total_pending_acceptance_quantity),
      detail: "Cantidad emitida aún pendiente de aceptación.",
    },
    {
      title: "Pendiente entrega",
      value: formatNumber(summary.pending_delivery_quantity),
      detail: "Cantidad aun pendiente de servir.",
    },
    {
      title: "Pendiente cierre",
      value: formatNumber(summary.pending_invoice_quantity),
      detail: "Cantidad entregada aún no aceptada documentalmente.",
    },
  ];
}

export default function OrderTraceabilityPage({ orderId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isActive = true;

    async function loadTraceability() {
      setLoading(true);
      setError("");

      try {
        const response = await ordersApi.getTraceability(orderId);
        if (!isActive) {
          return;
        }
        setData(response);
      } catch (requestError) {
        if (!isActive) {
          return;
        }
        setError(
          requestError instanceof Error
            ? requestError.message
            : "No se pudo cargar la trazabilidad del pedido.",
        );
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    }

    loadTraceability();

    return () => {
      isActive = false;
    };
  }, [orderId]);

  const itemColumns = [
    {
      key: "product_code",
      header: "Producto",
      render: (row) => <span className="font-medium text-slate-900">{row.product_code}</span>,
    },
    {
      key: "description",
      header: "Descripcion",
    },
    {
      key: "ordered_quantity",
      header: "Pedido",
      render: (row) => formatNumber(row.ordered_quantity),
    },
    {
      key: "delivered_quantity",
      header: "Entregado",
      render: (row) => formatNumber(row.delivered_quantity),
    },
    {
      key: "invoiced_quantity",
      header: "Aceptado",
      render: (row) => formatNumber(row.invoiced_quantity),
    },
    {
      key: "pending_delivery_quantity",
      header: "Pend. entrega",
      render: (row) => formatNumber(row.pending_delivery_quantity),
    },
    {
      key: "pending_invoice_quantity",
      header: "Pend. cierre",
      render: (row) => formatNumber(row.pending_invoice_quantity),
    },
    {
      key: "status",
      header: "Estado",
      render: (row) => <OperationalStatusBadge value={row.status} />,
    },
  ];

  const deliveryColumns = [
    {
      key: "delivery_number",
      header: "Albaran",
    },
    {
      key: "delivery_date",
      header: "Fecha",
      render: (row) => formatDate(row.delivery_date),
    },
  ];

  const invoiceColumns = [
    {
      key: "invoice_number",
      header: "Factura",
    },
    {
      key: "invoice_date",
      header: "Fecha",
      render: (row) => formatDate(row.invoice_date),
    },
    {
      key: "invoice_type",
      header: "Tipo",
      render: (row) => <OperationalStatusBadge value={row.invoice_type} />,
    },
    {
      key: "invoice_status",
      header: "Estado doc.",
      render: (row) => <OperationalStatusBadge value={row.invoice_status} />,
    },
    {
      key: "source_folder",
      header: "Carpeta",
      render: (row) => row.source_folder || "-",
    },
    {
      key: "total_amount",
      header: "Importe",
      render: (row) => formatCurrency(row.total_amount),
    },
  ];

  return (
    <>
      <Header
        title={loading ? "Order 360" : `Order 360 · ${data?.order.order_number ?? ""}`}
        subtitle="Trazabilidad completa del pedido, entregas y facturacion asociada."
      />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState message={error} /> : null}

        <SectionCard
          title="Cabecera del pedido"
          subtitle="Vista consolidada del pedido y su situacion operativa."
        >
          {loading ? (
            <LoadingState lines={4} />
          ) : data ? (
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Pedido</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{data.order.order_number}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Cliente</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{data.order.client_name}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Fecha</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{formatDate(data.order.order_date)}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Estado general</p>
                <div className="mt-2">
                  <OperationalStatusBadge value={data.order.status} />
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Estado documental</p>
                <div className="mt-2">
                  <OperationalStatusBadge value={data.order.invoice_document_status} />
                </div>
              </div>
            </div>
          ) : null}
        </SectionCard>

        <section className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4 2xl:grid-cols-7">
          {loading
            ? Array.from({ length: 7 }).map((_, index) => (
                <div key={index} className="h-[144px] animate-pulse rounded-md border border-slate-200 bg-white shadow-panel" />
              ))
            : buildSummaryCards(data?.summary).map((card) => <SummaryCard key={card.title} {...card} />)}
        </section>

        <section className="mt-6 grid gap-6">
          <SectionCard
            title="Detalle por linea"
            subtitle="Seguimiento operativo por producto dentro del pedido."
          >
            <DataTable
              columns={itemColumns}
              rows={data?.items ?? []}
              loading={loading}
              rowKey="order_item_id"
              emptyTitle="Sin lineas"
              emptyDescription="El pedido no contiene lineas registradas."
            />
          </SectionCard>

          <div className="grid gap-6 xl:grid-cols-2">
            <SectionCard
              title="Deliveries relacionados"
              subtitle="Albaranes vinculados al pedido."
            >
              {loading ? (
                <LoadingState lines={4} />
              ) : data?.deliveries.length ? (
                <DataTable
                  columns={deliveryColumns}
                  rows={data.deliveries}
                  rowKey="id"
                  compact
                />
              ) : (
                <EmptyState
                  title="Sin deliveries"
                  description="Todavia no existen albaranes relacionados para este pedido."
                />
              )}
            </SectionCard>

            <SectionCard
              title="Invoices relacionadas"
              subtitle="Facturas emitidas a partir del pedido, con su estado documental."
            >
              {loading ? (
                <LoadingState lines={4} />
              ) : data?.invoices.length ? (
                <DataTable
                  columns={invoiceColumns}
                  rows={data.invoices}
                  rowKey="id"
                  compact
                />
              ) : (
                <EmptyState
                  title="Sin invoices"
                  description="Todavia no existen facturas relacionadas para este pedido."
                />
              )}
            </SectionCard>
          </div>
        </section>
      </main>
    </>
  );
}
