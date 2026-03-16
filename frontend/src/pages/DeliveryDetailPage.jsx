import { Link, useParams } from "react-router-dom";
import DataTable from "../components/DataTable";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import LoadingState from "../components/LoadingState";
import OperationalStatusBadge from "../components/OperationalStatusBadge";
import SectionCard from "../components/SectionCard";
import SummaryCard from "../components/SummaryCard";
import { deliveriesApi } from "../services/deliveriesApi";
import { formatCurrency, formatDate, formatInteger, formatNumber } from "../utils/formatters";
import { useAsyncData } from "../utils/useAsyncData";

function buildSummaryCards(delivery) {
  if (!delivery) {
    return [];
  }

  return [
    { title: "Importe estimado", value: formatCurrency(delivery.total_amount), detail: "Valor calculado a partir de las líneas entregadas." },
    { title: "Líneas", value: formatInteger(delivery.lines.length), detail: "Líneas reales registradas en el albarán." },
    { title: "Estado", value: delivery.status === "completed" ? "Completado" : "Entregado", detail: "Situación operacional resumida del documento." },
    { title: "Facturación", value: delivery.invoice_status ? undefined : "Pendiente", detail: "Estado documental vinculado al pedido origen.", badge: delivery.invoice_status },
  ];
}

export default function DeliveryDetailPage() {
  const { deliveryId } = useParams();
  const { data: delivery, loading, error } = useAsyncData(() => deliveriesApi.getById(deliveryId), [deliveryId]);

  const lineColumns = [
    {
      key: "product",
      header: "Producto",
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900">{row.product_code || row.product_name || "-"}</p>
          <p className="text-xs text-slate-500">{row.product_name || "Sin maestro vinculado"}</p>
        </div>
      ),
    },
    { key: "description", header: "Descripción", render: (row) => <span className="line-clamp-2">{row.description || "-"}</span> },
    { key: "quantity", header: "Cantidad", render: (row) => formatNumber(row.quantity) },
    { key: "unit_price", header: "Precio", render: (row) => (row.unit_price == null ? "-" : formatCurrency(row.unit_price)) },
    { key: "total_amount", header: "Total", render: (row) => (row.total_amount == null ? "-" : formatCurrency(row.total_amount)) },
  ];

  const invoiceColumns = [
    { key: "invoice_number", header: "Factura", render: (row) => <Link to={`/invoices/${row.id}`} className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{row.invoice_number}</Link> },
    { key: "invoice_date", header: "Fecha", render: (row) => formatDate(row.invoice_date) },
    { key: "invoice_status", header: "Estado", render: (row) => <OperationalStatusBadge value={row.invoice_status} /> },
    { key: "total_amount", header: "Importe", render: (row) => (row.total_amount == null ? "-" : formatCurrency(row.total_amount)) },
    { key: "action", header: "Acción", render: (row) => <Link to={`/invoices/${row.id}`} className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">Abrir factura</Link> },
  ];

  const summaryCards = buildSummaryCards(delivery).map((card) => card.badge ? { title: card.title, value: undefined, detail: card.detail, render: <OperationalStatusBadge value={card.badge} /> } : card);

  return (
    <>
      <Header title={loading ? "Albarán" : `Albarán · ${delivery?.delivery_number || ""}`} subtitle="Detalle documental y operativo del albarán con enlaces directos hacia cliente, pedido y estado de facturación." />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState title="No se pudo cargar el albarán." message={error} /> : null}

        <div className="mb-6 flex flex-wrap items-center gap-3 text-sm text-slate-500">
          <Link to="/deliveries" className="font-medium text-slate-700 hover:text-slate-900">Albaranes</Link>
          <span>/</span>
          <span>{delivery?.delivery_number || `Albarán ${deliveryId}`}</span>
          {delivery ? <><span>/</span><Link to={`/clients/${delivery.client_id}`} className="font-medium text-slate-700 hover:text-slate-900">{delivery.client_name}</Link></> : null}
        </div>

        <SectionCard
          title="Cabecera del albarán"
          subtitle="Datos principales del documento y navegación cruzada con pedido y cliente."
          action={
            delivery ? (
              <div className="flex flex-col items-end gap-2">
                <Link to={`/clients/${delivery.client_id}`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">Abrir cliente</Link>
                {delivery.order_id ? <Link to={`/orders/${delivery.order_id}`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">Abrir pedido</Link> : null}
                <Link to={`/incidents/new?clientId=${delivery.client_id}&orderId=${delivery.order_id || ""}&deliveryId=${delivery.id}`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">Registrar incidencia</Link>
              </div>
            ) : null
          }
        >
          {loading ? <LoadingState lines={5} /> : delivery ? (
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Número de albarán</p><p className="mt-2 text-lg font-semibold text-slate-900">{delivery.delivery_number}</p></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Cliente</p><Link to={`/clients/${delivery.client_id}`} className="mt-2 inline-block text-lg font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{delivery.client_name}</Link></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Pedido relacionado</p>{delivery.order_id ? <Link to={`/orders/${delivery.order_id}`} className="mt-2 inline-block text-lg font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{delivery.order_number}</Link> : <p className="mt-2 text-lg font-semibold text-slate-900">-</p>}</div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Fecha</p><p className="mt-2 text-lg font-semibold text-slate-900">{formatDate(delivery.delivery_date)}</p></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Estado</p><div className="mt-2"><OperationalStatusBadge value={delivery.status} /></div></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Facturación</p><div className="mt-2"><OperationalStatusBadge value={delivery.invoice_status} /></div></div>
              <div className="md:col-span-2 xl:col-span-3"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Observaciones</p><p className="mt-2 text-sm leading-6 text-slate-900">{delivery.notes || "Sin observaciones registradas en el modelo actual."}</p></div>
            </div>
          ) : null}
        </SectionCard>

        <section className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {loading ? Array.from({ length: 4 }).map((_, index) => <div key={index} className="h-[144px] animate-pulse rounded-md border border-slate-200 bg-white shadow-panel" />) : summaryCards.map((card) => <SummaryCard key={card.title} title={card.title} value={card.render || card.value} detail={card.detail} />)}
        </section>

        <section className="mt-6 grid gap-6">
          <SectionCard title="Líneas del albarán" subtitle="Detalle real de líneas entregadas con cantidad, valoración y contexto de producto.">
            <DataTable columns={lineColumns} rows={delivery?.lines ?? []} rowKey="id" loading={loading} emptyTitle="Sin líneas registradas" emptyDescription="El albarán no contiene líneas visibles en este momento." />
          </SectionCard>

          <SectionCard title="Relaciones documentales" subtitle="Pedido origen, estado documental y acceso al módulo de facturación.">
            {loading ? <LoadingState lines={5} /> : delivery ? (
              <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Pedido origen</p>{delivery.relations.source_order_id ? <Link to={`/orders/${delivery.relations.source_order_id}`} className="mt-3 inline-block text-sm font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{delivery.relations.source_order_number}</Link> : <p className="mt-3 text-sm text-slate-900">Sin pedido relacionado</p>}</div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Estado documental</p><div className="mt-3"><OperationalStatusBadge value={delivery.relations.document_status} /></div></div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Acceso a facturación</p><Link to="/invoices" className="mt-3 inline-block text-sm font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">Abrir módulo de facturas</Link></div>
                </div>
                <div className="rounded-md border border-dashed border-slate-300 bg-slate-50/70 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Siguiente fase</p><p className="mt-3 text-sm leading-6 text-slate-700">La base queda preparada para enlazar detalle completo de factura por documento sin rehacer esta vista.</p></div>
              </div>
            ) : null}

            <div className="mt-6">
              {loading ? <LoadingState lines={4} /> : delivery?.relations.linked_invoices.length ? <DataTable columns={invoiceColumns} rows={delivery.relations.linked_invoices} rowKey="id" compact /> : <EmptyState title="Sin factura vinculada todavía" description="No existe una factura relacionada visible en el modelo actual. El bloque queda listo para conectar facturas detalladas en la siguiente fase." />}
            </div>
          </SectionCard>
        </section>
      </main>
    </>
  );
}
