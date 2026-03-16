import { Link, useParams } from "react-router-dom";
import DataTable from "../components/DataTable";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import LoadingState from "../components/LoadingState";
import OperationalStatusBadge from "../components/OperationalStatusBadge";
import SectionCard from "../components/SectionCard";
import SummaryCard from "../components/SummaryCard";
import { translateStatus } from "../services/statusTranslation";
import { ordersApi } from "../services/ordersApi";
import { formatCurrency, formatDate, formatInteger, formatNumber } from "../utils/formatters";
import { useAsyncData } from "../utils/useAsyncData";

function buildSummaryCards(order) {
  if (!order) {
    return [];
  }

  return [
    {
      title: "Total pedido",
      value: formatCurrency(order.total_amount),
      detail: "Importe total consolidado del pedido.",
    },
    {
      title: "Líneas",
      value: formatInteger(order.lines.length),
      detail: "Líneas registradas en el documento.",
    },
    {
      title: "Entrega",
      value: translateStatus(order.traceability.delivery_status),
      detail: "Situación logística resumida.",
    },
    {
      title: "Facturación",
      value: translateStatus(order.traceability.invoice_status),
      detail: "Situación documental resumida.",
    },
  ];
}

function FutureBlock({ title, description }) {
  return (
    <SectionCard title={title} subtitle={description}>
      <EmptyState
        title="Base preparada"
        description="El bloque queda listo para conectar el módulo real en la siguiente fase sin rehacer navegación ni estructura."
      />
    </SectionCard>
  );
}

export default function OrderDetailPage() {
  const { orderId } = useParams();
  const {
    data: order,
    loading,
    error,
  } = useAsyncData(() => ordersApi.getById(orderId), [orderId]);

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
    {
      key: "description",
      header: "Descripción",
      render: (row) => <span className="line-clamp-2">{row.description || "-"}</span>,
    },
    {
      key: "quantity",
      header: "Cantidad",
      render: (row) => formatNumber(row.quantity),
    },
    {
      key: "unit_price",
      header: "Precio",
      render: (row) => formatCurrency(row.unit_price),
    },
    {
      key: "total_amount",
      header: "Total",
      render: (row) => formatCurrency(row.total_amount),
    },
  ];

  const documentColumns = [
    {
      key: "document_number",
      header: "Documento",
      render: (row) => <span className="font-medium text-slate-900">{row.document_number}</span>,
    },
    {
      key: "document_date",
      header: "Fecha",
      render: (row) => formatDate(row.document_date),
    },
    {
      key: "status",
      header: "Estado",
      render: (row) => (row.status ? <OperationalStatusBadge value={row.status} /> : "-"),
    },
    {
      key: "total_amount",
      header: "Importe",
      render: (row) => (row.total_amount == null ? "-" : formatCurrency(row.total_amount)),
    },
  ];

  return (
    <>
      <Header
        title={loading ? "Pedido" : `Pedido · ${order?.order_number || ""}`}
        subtitle="Detalle operativo del pedido con contexto comercial, líneas y trazabilidad preparada para el ciclo completo."
      />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState title="No se pudo cargar el pedido." message={error} /> : null}

        <div className="mb-6 flex flex-wrap items-center gap-3 text-sm text-slate-500">
          <Link to="/orders" className="font-medium text-slate-700 hover:text-slate-900">
            Pedidos
          </Link>
          <span>/</span>
          <span>{order?.order_number || `Pedido ${orderId}`}</span>
          {order ? (
            <>
              <span>/</span>
              <Link to={`/clients/${order.client_id}`} className="font-medium text-slate-700 hover:text-slate-900">
                {order.client_name}
              </Link>
            </>
          ) : null}
        </div>

        <SectionCard
          title="Cabecera del pedido"
          subtitle="Datos principales del pedido y puntos de navegación cruzada con cliente y trazabilidad."
          action={
            order ? (
              <div className="flex flex-col items-end gap-2">
                <Link to={`/clients/${order.client_id}`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
                  Abrir cliente
                </Link>
                <Link to={`/orders/${order.id}/traceability`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
                  Abrir trazabilidad
                </Link>
              </div>
            ) : null
          }
        >
          {loading ? (
            <LoadingState lines={5} />
          ) : order ? (
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Número de pedido</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{order.order_number}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Cliente</p>
                <Link to={`/clients/${order.client_id}`} className="mt-2 inline-block text-lg font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
                  {order.client_name}
                </Link>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Fecha</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{formatDate(order.order_date)}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Estado</p>
                <div className="mt-2">
                  <OperationalStatusBadge value={order.status} />
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Referencia cliente</p>
                <p className="mt-2 text-sm text-slate-900">{order.client_reference || "-"}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Importe total</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{formatCurrency(order.total_amount)}</p>
              </div>
              <div className="md:col-span-2 xl:col-span-3">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Observaciones</p>
                <p className="mt-2 text-sm leading-6 text-slate-900">{order.notes || "Sin observaciones registradas."}</p>
              </div>
            </div>
          ) : null}
        </SectionCard>

        <section className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {loading
            ? Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="h-[144px] animate-pulse rounded-md border border-slate-200 bg-white shadow-panel" />
              ))
            : buildSummaryCards(order).map((card) => <SummaryCard key={card.title} {...card} />)}
        </section>

        <section className="mt-6 grid gap-6">
          <SectionCard
            title="Líneas del pedido"
            subtitle="Detalle económico y descriptivo por línea para revisión comercial y operativa."
          >
            <DataTable
              columns={lineColumns}
              rows={order?.lines ?? []}
              rowKey="id"
              loading={loading}
              emptyTitle="Sin líneas registradas"
              emptyDescription="El pedido no contiene líneas disponibles en este momento."
            />
          </SectionCard>

          <SectionCard
            title="Bloque de trazabilidad"
            subtitle="Resumen logístico y documental con acceso directo a la vista de trazabilidad existente."
          >
            {loading ? (
              <LoadingState lines={5} />
            ) : order ? (
              <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Estado logístico</p>
                    <div className="mt-3">
                      <OperationalStatusBadge value={order.traceability.logistics_status} />
                    </div>
                  </div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Estado entrega</p>
                    <div className="mt-3">
                      <OperationalStatusBadge value={order.traceability.delivery_status} />
                    </div>
                  </div>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Estado facturación</p>
                    <div className="mt-3">
                      <OperationalStatusBadge value={order.traceability.invoice_status} />
                    </div>
                  </div>
                </div>

                <div className="flex items-start justify-end">
                  <Link to={`/orders/${order.id}/traceability`} className="inline-flex rounded-md border border-slate-900 px-4 py-2.5 text-sm font-medium text-slate-900 transition hover:bg-slate-900 hover:text-white">
                    Abrir vista de trazabilidad
                  </Link>
                </div>
              </div>
            ) : null}

            <div className="mt-6 grid gap-6 xl:grid-cols-2">
              <div>
                {loading ? (
                  <LoadingState lines={4} />
                ) : order?.traceability.deliveries.length ? (
                  <DataTable columns={documentColumns} rows={order.traceability.deliveries} rowKey="id" compact />
                ) : (
                  <EmptyState
                    title="Sin albaranes vinculados"
                    description="La base queda preparada para conectar el módulo de albaranes sin rehacer esta ficha."
                  />
                )}
              </div>
              <div>
                {loading ? (
                  <LoadingState lines={4} />
                ) : order?.traceability.invoices.length ? (
                  <DataTable columns={documentColumns} rows={order.traceability.invoices} rowKey="id" compact />
                ) : (
                  <EmptyState
                    title="Sin facturas vinculadas"
                    description="La base queda preparada para conectar el módulo de facturas sin rehacer esta ficha."
                  />
                )}
              </div>
            </div>
          </SectionCard>

          <div className="grid gap-6 xl:grid-cols-3">
            <FutureBlock title="Albaranes" description="Contenedor visual listo para el siguiente módulo operativo." />
            <FutureBlock title="Facturas" description="Contenedor visual listo para el siguiente módulo documental." />
            <FutureBlock title="Incidencias" description="Contenedor visual listo para el siguiente módulo de incidencias." />
          </div>
        </section>
      </main>
    </>
  );
}
