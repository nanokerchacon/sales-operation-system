import AgingInvoicesChart from "../components/charts/AgingInvoicesChart";
import PendingRevenueChart from "../components/charts/PendingRevenueChart";
import DataTable from "../components/DataTable";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import KpiCard from "../components/KpiCard";
import LoadingState from "../components/LoadingState";
import OperationalStatusBadge from "../components/OperationalStatusBadge";
import PriorityBadge from "../components/PriorityBadge";
import SectionCard from "../components/SectionCard";
import StatusSummaryCards from "../components/StatusSummaryCards";
import useDashboardData from "../hooks/useDashboardData";
import { formatCurrency, formatInteger, formatNumber } from "../utils/formatters";
import { getDisplayStatus, navigateTo } from "../utils/mappers";

function buildKpis(operations) {
  if (!operations) {
    return [];
  }

  return [
    {
      title: "Total de pedidos",
      value: formatInteger(operations.total_orders),
      detail: "Volumen total monitorizado en operaciones.",
      tone: "default",
    },
    {
      title: "Pedidos con incidencias",
      value: formatInteger(operations.orders_with_issues),
      detail: "Pedidos con desviaciones de entrega o facturacion.",
      tone: "alert",
    },
    {
      title: "Pedidos correctos",
      value: formatInteger(operations.orders_without_issues),
      detail: "Pedidos dentro de la operativa esperada.",
      tone: "success",
    },
    {
      title: "Cantidad pendiente de entregar",
      value: formatNumber(operations.total_pending_delivery_quantity),
      detail: "Unidades aún no servidas al cliente.",
      tone: "muted",
    },
    {
      title: "Cantidad pendiente de facturar",
      value: formatNumber(operations.total_pending_invoice_quantity),
      detail: "Unidades entregadas pendientes de facturación.",
      tone: "default",
    },
  ];
}

function buildRevenueSummary(pendingRevenue) {
  return pendingRevenue.reduce(
    (summary, item) => {
      const amount = Number(item.amount_pending_invoice || 0);
      summary.total += amount;

      if (item.days_since_last_delivery <= 3) {
        summary.bucket0to3 += amount;
      } else if (item.days_since_last_delivery <= 7) {
        summary.bucket4to7 += amount;
      } else if (item.days_since_last_delivery <= 15) {
        summary.bucket8to15 += amount;
      } else {
        summary.bucketOver15 += amount;
      }

      return summary;
    },
    {
      total: 0,
      bucket0to3: 0,
      bucket4to7: 0,
      bucket8to15: 0,
      bucketOver15: 0,
    },
  );
}

function SummaryMetric({ label, value, accent = false }) {
  return (
    <div
      className={`rounded-md border px-4 py-3 ${
        accent ? "border-slate-900 bg-slate-900 text-white" : "border-slate-200 bg-slate-50"
      }`}
    >
      <p
        className={`text-xs font-semibold uppercase tracking-[0.18em] ${
          accent ? "text-slate-300" : "text-slate-500"
        }`}
      >
        {label}
      </p>
      <p className={`mt-2 text-xl font-semibold ${accent ? "text-white" : "text-slate-900"}`}>{value}</p>
    </div>
  );
}

export default function DashboardPage() {
  const { data, loading, error, lastUpdated } = useDashboardData();
  const kpis = buildKpis(data.operations);
  const revenueSummary = buildRevenueSummary(data.pendingRevenue);

  const workQueueColumns = [
    {
      key: "order_number",
      header: "Numero",
      render: (row) => (
        <button
          type="button"
          onClick={() => navigateTo(`/orders/${row.order_id}/traceability`)}
          className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline"
        >
          {row.order_number}
        </button>
      ),
    },
    {
      key: "client_name",
      header: "Cliente",
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900">{row.client_name}</p>
          <p className="text-xs text-slate-500">ID cliente {row.client_id}</p>
        </div>
      ),
    },
    {
      key: "order_id",
      header: "Pedido",
      render: (row) => (
        <div>
          <p className="font-medium text-slate-900">Pedido #{row.order_id}</p>
          <p className="text-xs text-slate-500">{getDisplayStatus(row.order_status)}</p>
        </div>
      ),
    },
    {
      key: "delivered_quantity",
      header: "Entregado",
      render: (row) => formatNumber(row.delivered_quantity),
    },
    {
      key: "invoiced_quantity",
      header: "Facturado",
      render: (row) => formatNumber(row.invoiced_quantity),
    },
    {
      key: "pending_delivery_quantity",
      header: "Pend. entrega",
      render: (row) => formatNumber(row.pending_delivery_quantity),
    },
    {
      key: "pending_invoice_quantity",
      header: "Pend. factura",
      render: (row) => formatNumber(row.pending_invoice_quantity),
    },
    {
      key: "status",
      header: "Estado",
      render: (row) => <OperationalStatusBadge value={row.status} />,
    },
    {
      key: "priority",
      header: "Prioridad",
      render: (row) => <PriorityBadge value={row.priority} />,
    },
  ];

  const clientIncidentsColumns = [
    {
      key: "client_name",
      header: "Cliente",
      render: (row) => <span className="font-medium text-slate-900">{row.client_name}</span>,
    },
    {
      key: "orders_with_issues",
      header: "Pedidos con incidencias",
      render: (row) => formatInteger(row.orders_with_issues),
    },
    {
      key: "total_pending_invoice_quantity",
      header: "Cantidad pendiente",
      render: (row) => formatNumber(row.total_pending_invoice_quantity),
    },
    {
      key: "total_pending_invoice_amount",
      header: "Importe pendiente",
      render: (row) => formatCurrency(row.total_pending_invoice_amount),
    },
    {
      key: "highest_priority_level_es",
      header: "Prioridad",
      render: (row) => <PriorityBadge value={row.highest_priority_level} />,
    },
  ];

  const pendingInvoiceColumns = [
    {
      key: "client_name",
      header: "Cliente",
      render: (row) => <span className="font-medium text-slate-900">{row.client_name}</span>,
    },
    {
      key: "order_id",
      header: "Pedido",
      render: (row) => (
        <button
          type="button"
          onClick={() => navigateTo(`/orders/${row.order_id}/traceability`)}
          className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline"
        >
          {row.order_number || `#${row.order_id}`}
        </button>
      ),
    },
    {
      key: "amount_pending_invoice",
      header: "Pendiente",
      render: (row) => formatCurrency(row.amount_pending_invoice),
    },
    {
      key: "status_es",
      header: "Situación",
      render: (row) => <OperationalStatusBadge value={row.status} />,
    },
  ];

  const incidentOrdersColumns = [
    {
      key: "client_name",
      header: "Cliente",
      render: (row) => <span className="font-medium text-slate-900">{row.client_name}</span>,
    },
    {
      key: "order_id",
      header: "Pedido",
      render: (row) => (
        <button
          type="button"
          onClick={() => navigateTo(`/orders/${row.order_id}/traceability`)}
          className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline"
        >
          {row.order_number || `#${row.order_id}`}
        </button>
      ),
    },
    {
      key: "pending_invoice_quantity",
      header: "Pendiente",
      render: (row) => formatNumber(row.pending_invoice_quantity),
    },
    {
      key: "status_es",
      header: "Incidencia",
      render: (row) => <OperationalStatusBadge value={row.status} />,
    },
  ];

  return (
    <>
      <Header
        title="Dashboard"
        subtitle="Visión consolidada de operaciones, facturación pendiente y control operativo."
        lastUpdated={lastUpdated}
      />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState message={error} /> : null}

        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5">
          {loading
            ? Array.from({ length: 5 }).map((_, index) => (
                <div key={index} className="h-[158px] animate-pulse rounded-md border border-slate-200 bg-white shadow-panel" />
              ))
            : kpis.map((kpi) => <KpiCard key={kpi.title} {...kpi} />)}
        </section>

        <section className="mt-6">
          <SectionCard
            title="Resumen de estados operativos"
            subtitle="Distribución real del flujo pedido, entrega y facturación."
          >
            {loading ? (
              <LoadingState lines={4} />
            ) : (
              <StatusSummaryCards summary={data.orderStatusSummary} formatValue={formatInteger} />
            )}
          </SectionCard>
        </section>

        <section className="mt-6 grid gap-6 2xl:grid-cols-2">
          <SectionCard
            title="Facturación pendiente por antigüedad"
            subtitle="Distribución ejecutiva de importes pendientes según el envejecimiento de facturas."
          >
            {loading ? <LoadingState lines={5} /> : <AgingInvoicesChart agingInvoices={data.agingInvoices} />}
          </SectionCard>

          <SectionCard
            title="Facturacion pendiente acumulada"
            subtitle="Exposición pendiente de facturación consolidada por tramos de antigüedad."
          >
            {loading ? <LoadingState lines={5} /> : <PendingRevenueChart summary={revenueSummary} />}
          </SectionCard>
        </section>

        <section className="mt-6 grid gap-6 xl:grid-cols-dashboard">
          <div className="space-y-6">
            <SectionCard
              title="Cola operativa"
              subtitle="Pedidos priorizados por estado operativo y desviaciones entre entrega y facturación."
            >
              <DataTable
                columns={workQueueColumns}
                rows={data.workQueue}
                loading={loading}
                rowKey="order_id"
                emptyTitle="Sin cola operativa"
                emptyDescription="No existen pedidos para monitorizar en este momento."
              />
            </SectionCard>

            <SectionCard
              title="Pedidos con incidencias"
              subtitle="Pedidos con desviaciones entre entrega y facturación."
            >
              <DataTable
                columns={incidentOrdersColumns}
                rows={data.ordersWithIncidents.slice(0, 6)}
                loading={loading}
                rowKey="order_id"
                emptyTitle="Sin pedidos con incidencias"
                emptyDescription="No se han detectado incidencias operativas en pedidos."
                compact
              />
            </SectionCard>
          </div>

          <div className="space-y-6">
            <SectionCard
              title="Resumen de facturacion pendiente"
              subtitle="Vista agregada de facturación pendiente con distribución por antigüedad."
            >
              {loading ? (
                <LoadingState lines={4} />
              ) : data.pendingRevenue.length ? (
                <div className="space-y-4">
                  <SummaryMetric
                    label="Total pendiente de facturar"
                    value={formatCurrency(revenueSummary.total)}
                    accent
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <SummaryMetric label="0 a 3 días" value={formatCurrency(revenueSummary.bucket0to3)} />
                    <SummaryMetric label="4 a 7 días" value={formatCurrency(revenueSummary.bucket4to7)} />
                    <SummaryMetric label="8 a 15 días" value={formatCurrency(revenueSummary.bucket8to15)} />
                    <SummaryMetric label="Más de 15 días" value={formatCurrency(revenueSummary.bucketOver15)} />
                  </div>
                </div>
              ) : (
                <EmptyState
                  title="Sin resumen financiero"
                  description="No hay importes pendientes de facturar para mostrar."
                />
              )}
            </SectionCard>

            <SectionCard
              title="Aging de facturas"
              subtitle="Bloque consolidado del endpoint de aging para seguimiento ejecutivo."
            >
              {loading ? (
                <LoadingState lines={4} />
              ) : data.agingInvoices ? (
                <div className="space-y-3">
                  <SummaryMetric
                    label="Total pendiente"
                    value={formatCurrency(data.agingInvoices.total_pending_invoice_amount)}
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <SummaryMetric label="0 a 3 días" value={formatCurrency(data.agingInvoices.bucket_0_3_days)} />
                    <SummaryMetric label="4 a 7 días" value={formatCurrency(data.agingInvoices.bucket_4_7_days)} />
                    <SummaryMetric label="8 a 15 días" value={formatCurrency(data.agingInvoices.bucket_8_15_days)} />
                    <SummaryMetric label="Más de 15 días" value={formatCurrency(data.agingInvoices.bucket_over_15_days)} />
                  </div>
                </div>
              ) : (
                <EmptyState
                  title="Sin aging disponible"
                  description="No hay importes pendientes para clasificar por antigüedad."
                />
              )}
            </SectionCard>

            <SectionCard
              title="Facturación pendiente prioritaria"
              subtitle="Pedidos pendientes con mayor importe económico."
            >
              <DataTable
                columns={pendingInvoiceColumns}
                rows={data.pendingInvoices.slice(0, 5)}
                loading={loading}
                rowKey="order_id"
                emptyTitle="Sin facturación pendiente"
                emptyDescription="No existen importes pendientes de facturación."
                compact
              />
            </SectionCard>

            <SectionCard
              title="Incidencias por cliente"
              subtitle="Clientes con mayor carga operativa y facturación pendiente."
            >
              <DataTable
                columns={clientIncidentsColumns}
                rows={data.clientsWithIncidents.slice(0, 6)}
                loading={loading}
                rowKey="client_id"
                emptyTitle="Sin clientes con incidencias"
                emptyDescription="No existen clientes con incidencias acumuladas."
                compact
              />
            </SectionCard>
          </div>
        </section>
      </main>
    </>
  );
}
