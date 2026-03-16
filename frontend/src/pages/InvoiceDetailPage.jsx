import { Link, useParams } from "react-router-dom";
import DataTable from "../components/DataTable";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import LoadingState from "../components/LoadingState";
import OperationalStatusBadge from "../components/OperationalStatusBadge";
import SectionCard from "../components/SectionCard";
import SummaryCard from "../components/SummaryCard";
import { invoicesApi } from "../services/invoicesApi";
import { formatCurrency, formatDate, formatNumber } from "../utils/formatters";
import { useAsyncData } from "../utils/useAsyncData";

function buildSummaryCards(invoice) {
  if (!invoice) {
    return [];
  }

  return [
    { title: "Base imponible", value: invoice.summary.taxable_base == null ? "-" : formatCurrency(invoice.summary.taxable_base), detail: "Importe real disponible antes de impuestos si el modelo lo soporta." },
    { title: "Impuestos", value: invoice.summary.tax_amount == null ? "-" : formatCurrency(invoice.summary.tax_amount), detail: "Desglose fiscal disponible en el modelo actual." },
    { title: "Total", value: formatCurrency(invoice.summary.total_amount), detail: "Importe total del documento." },
    { title: "Cobro", value: invoice.summary.payment_status || "Pendiente de modelar", detail: "Hueco preparado para estados de cobro y vencimientos futuros." },
  ];
}

export default function InvoiceDetailPage() {
  const { invoiceId } = useParams();
  const { data: invoice, loading, error } = useAsyncData(() => invoicesApi.getById(invoiceId), [invoiceId]);

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
    { key: "unit_price", header: "Precio", render: (row) => formatCurrency(row.unit_price) },
    { key: "total_amount", header: "Total", render: (row) => formatCurrency(row.total_amount) },
  ];

  const deliveryColumns = [
    { key: "delivery_number", header: "Albarán", render: (row) => <Link to={`/deliveries/${row.id}`} className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{row.delivery_number}</Link> },
    { key: "delivery_date", header: "Fecha", render: (row) => formatDate(row.delivery_date) },
  ];

  return (
    <>
      <Header title={loading ? "Factura" : `Factura · ${invoice?.invoice_number || ""}`} subtitle="Detalle documental y financiero de la factura con enlaces directos hacia cliente, pedido y albarán relacionado." />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState title="No se pudo cargar la factura." message={error} /> : null}

        <div className="mb-6 flex flex-wrap items-center gap-3 text-sm text-slate-500">
          <Link to="/invoices" className="font-medium text-slate-700 hover:text-slate-900">Facturas</Link>
          <span>/</span>
          <span>{invoice?.invoice_number || `Factura ${invoiceId}`}</span>
          {invoice ? <><span>/</span><Link to={`/clients/${invoice.client_id}`} className="font-medium text-slate-700 hover:text-slate-900">{invoice.client_name}</Link></> : null}
        </div>

        <SectionCard
          title="Cabecera de factura"
          subtitle="Datos principales del documento y navegación cruzada con cliente, pedido y albarán."
          action={
            invoice ? (
              <div className="flex flex-col items-end gap-2">
                <Link to={`/clients/${invoice.client_id}`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">Abrir cliente</Link>
                {invoice.order_id ? <Link to={`/orders/${invoice.order_id}`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">Abrir pedido</Link> : null}
                {invoice.delivery_id ? <Link to={`/deliveries/${invoice.delivery_id}`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">Abrir albarán</Link> : null}
                <Link to={`/incidents/new?clientId=${invoice.client_id}&orderId=${invoice.order_id || ""}&deliveryId=${invoice.delivery_id || ""}&invoiceId=${invoice.id}&type=facturacion`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">Registrar incidencia</Link>
              </div>
            ) : null
          }
        >
          {loading ? <LoadingState lines={5} /> : invoice ? (
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Número de factura</p><p className="mt-2 text-lg font-semibold text-slate-900">{invoice.invoice_number}</p></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Cliente</p><Link to={`/clients/${invoice.client_id}`} className="mt-2 inline-block text-lg font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{invoice.client_name}</Link></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Pedido relacionado</p>{invoice.order_id ? <Link to={`/orders/${invoice.order_id}`} className="mt-2 inline-block text-lg font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{invoice.order_number}</Link> : <p className="mt-2 text-lg font-semibold text-slate-900">-</p>}</div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Albarán relacionado</p>{invoice.delivery_id ? <Link to={`/deliveries/${invoice.delivery_id}`} className="mt-2 inline-block text-lg font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{invoice.delivery_number}</Link> : <p className="mt-2 text-lg font-semibold text-slate-900">-</p>}</div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Fecha</p><p className="mt-2 text-lg font-semibold text-slate-900">{formatDate(invoice.invoice_date)}</p></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Estado</p><div className="mt-2"><OperationalStatusBadge value={invoice.status} /></div></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Vencimiento</p><p className="mt-2 text-lg font-semibold text-slate-900">{formatDate(invoice.due_date)}</p></div>
              <div className="md:col-span-2 xl:col-span-3"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Observaciones</p><p className="mt-2 text-sm leading-6 text-slate-900">{invoice.notes || "Sin observaciones registradas en el modelo actual."}</p></div>
            </div>
          ) : null}
        </SectionCard>

        <section className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {loading ? Array.from({ length: 4 }).map((_, index) => <div key={index} className="h-[144px] animate-pulse rounded-md border border-slate-200 bg-white shadow-panel" />) : buildSummaryCards(invoice).map((card) => <SummaryCard key={card.title} {...card} />)}
        </section>

        <section className="mt-6 grid gap-6">
          <SectionCard title="Líneas de factura" subtitle="Detalle real de líneas facturadas con cantidad, valoración y referencia de producto.">
            <DataTable columns={lineColumns} rows={invoice?.lines ?? []} rowKey="id" loading={loading} emptyTitle="Sin líneas registradas" emptyDescription="La factura no contiene líneas visibles en este momento." />
          </SectionCard>

          <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
            <SectionCard title="Resumen económico" subtitle="Desglose económico con los datos reales disponibles en el modelo actual.">
              {loading ? <LoadingState lines={4} /> : invoice ? (
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Base imponible</p><p className="mt-3 text-lg font-semibold text-slate-900">{invoice.summary.taxable_base == null ? "-" : formatCurrency(invoice.summary.taxable_base)}</p></div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Impuestos</p><p className="mt-3 text-lg font-semibold text-slate-900">{invoice.summary.tax_amount == null ? "-" : formatCurrency(invoice.summary.tax_amount)}</p></div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Total</p><p className="mt-3 text-lg font-semibold text-slate-900">{formatCurrency(invoice.summary.total_amount)}</p></div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Estado de cobro</p><p className="mt-3 text-sm font-semibold text-slate-900">{invoice.summary.payment_status || "No modelado todavía"}</p></div>
                </div>
              ) : null}
            </SectionCard>

            <SectionCard title="Relaciones documentales" subtitle="Cliente, pedido, albaranes relacionados y hueco preparado para cobros futuros.">
              {loading ? <LoadingState lines={5} /> : invoice ? (
                <div className="grid gap-6">
                  <div className="grid gap-4 md:grid-cols-3">
                    <div className="rounded-md border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Cliente</p><Link to={`/clients/${invoice.relations.client_id}`} className="mt-3 inline-block text-sm font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{invoice.relations.client_name}</Link></div>
                    <div className="rounded-md border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Pedido origen</p>{invoice.relations.source_order_id ? <Link to={`/orders/${invoice.relations.source_order_id}`} className="mt-3 inline-block text-sm font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{invoice.relations.source_order_number}</Link> : <p className="mt-3 text-sm text-slate-900">Sin pedido relacionado</p>}</div>
                    <div className="rounded-md border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Albarán principal</p>{invoice.relations.primary_delivery_id ? <Link to={`/deliveries/${invoice.relations.primary_delivery_id}`} className="mt-3 inline-block text-sm font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{invoice.relations.primary_delivery_number}</Link> : <p className="mt-3 text-sm text-slate-900">Sin albarán inferido</p>}</div>
                  </div>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="rounded-md border border-slate-200 bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Estado documental</p><div className="mt-3"><OperationalStatusBadge value={invoice.relations.document_status} /></div></div>
                    <div className="rounded-md border border-dashed border-slate-300 bg-slate-50/70 p-4"><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Cobros futuros</p><p className="mt-3 text-sm leading-6 text-slate-700">{invoice.relations.payments_placeholder}</p></div>
                  </div>
                  {invoice.relations.linked_deliveries.length ? <DataTable columns={deliveryColumns} rows={invoice.relations.linked_deliveries} rowKey="id" compact /> : <EmptyState title="Sin albaranes relacionados" description="No se ha podido inferir un albarán relacionado con las líneas actuales de la factura." />}
                </div>
              ) : null}
            </SectionCard>
          </div>
        </section>
      </main>
    </>
  );
}
