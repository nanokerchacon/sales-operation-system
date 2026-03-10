import AgingInvoicesChart from "../components/charts/AgingInvoicesChart";
import RevenueRiskChart from "../components/charts/RevenueRiskChart";
import DataTable from "../components/DataTable";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import KpiCard from "../components/KpiCard";
import LoadingState from "../components/LoadingState";
import RiskBadge from "../components/RiskBadge";
import SectionCard from "../components/SectionCard";
import useDashboardData from "../hooks/useDashboardData";
import { formatCurrency, formatInteger, formatNumber } from "../utils/formatters";
import { getDisplayStatus } from "../utils/mappers";

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
      title: "Pedidos con riesgo",
      value: formatInteger(operations.orders_with_risk),
      detail: "Pedidos con desviación de entrega o facturación.",
      tone: "alert",
    },
    {
      title: "Pedidos sin riesgo",
      value: formatInteger(operations.orders_without_risk),
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

function buildRevenueSummary(revenueAtRisk) {
  return revenueAtRisk.reduce(
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
  const revenueSummary = buildRevenueSummary(data.revenueAtRisk);

  const workQueueColumns = [
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
          <p className="text-xs text-slate-500">{getDisplayStatus(row.status)}</p>
        </div>
      ),
    },
    {
      key: "pending_invoice_quantity",
      header: "Cantidad pendiente",
      render: (row) => formatNumber(row.pending_invoice_quantity),
    },
    {
      key: "amount_pending_invoice",
      header: "Importe pendiente",
      render: (row) => formatCurrency(row.amount_pending_invoice),
    },
    {
      key: "days_since_last_delivery",
      header: "Días desde última entrega",
      render: (row) => `${formatInteger(row.days_since_last_delivery)} días`,
    },
    {
      key: "status",
      header: "Estado",
      render: (row) => <span className="text-sm font-medium text-slate-700">{getDisplayStatus(row.status)}</span>,
    },
    {
      key: "risk_level_es",
      header: "Riesgo",
      render: (row) => <RiskBadge value={row.risk_level_es} />,
    },
  ];

  const clientRiskColumns = [
    {
      key: "client_name",
      header: "Cliente",
      render: (row) => <span className="font-medium text-slate-900">{row.client_name}</span>,
    },
    {
      key: "orders_with_risk",
      header: "Pedidos con riesgo",
      render: (row) => formatInteger(row.orders_with_risk),
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
      key: "highest_risk_level_es",
      header: "Nivel de riesgo",
      render: (row) => <RiskBadge value={row.highest_risk_level_es} />,
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
      render: (row) => `#${row.order_id}`,
    },
    {
      key: "amount_pending_invoice",
      header: "Pendiente",
      render: (row) => formatCurrency(row.amount_pending_invoice),
    },
    {
      key: "risk_status_es",
      header: "Situación",
      render: (row) => <span className="text-sm text-slate-600">{row.risk_status_es}</span>,
    },
  ];

  const riskOrdersColumns = [
    {
      key: "client_name",
      header: "Cliente",
      render: (row) => <span className="font-medium text-slate-900">{row.client_name}</span>,
    },
    {
      key: "order_id",
      header: "Pedido",
      render: (row) => `#${row.order_id}`,
    },
    {
      key: "pending_invoice_quantity",
      header: "Pendiente",
      render: (row) => formatNumber(row.pending_invoice_quantity),
    },
    {
      key: "risk_status_es",
      header: "Riesgo",
      render: (row) => <span className="text-sm text-slate-600">{row.risk_status_es}</span>,
    },
  ];

  return (
    <>
      <Header
        title="Dashboard"
        subtitle="Visión consolidada de operaciones, facturación pendiente y riesgo comercial."
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

        <section className="mt-6 grid gap-6 2xl:grid-cols-2">
          <SectionCard
            title="Facturación pendiente por antigüedad"
            subtitle="Distribución ejecutiva de importes pendientes según el envejecimiento de facturas."
          >
            {loading ? <LoadingState lines={5} /> : <AgingInvoicesChart agingInvoices={data.agingInvoices} />}
          </SectionCard>

          <SectionCard
            title="Riesgo financiero acumulado"
            subtitle="Exposición pendiente de facturación consolidada por tramos de antigüedad."
          >
            {loading ? <LoadingState lines={5} /> : <RevenueRiskChart summary={revenueSummary} />}
          </SectionCard>
        </section>

        <section className="mt-6 grid gap-6 xl:grid-cols-dashboard">
          <div className="space-y-6">
            <SectionCard
              title="Cola operativa"
              subtitle="Pedidos entregados con impacto pendiente de facturación, ordenados por severidad."
            >
              <DataTable
                columns={workQueueColumns}
                rows={data.workQueue}
                loading={loading}
                rowKey="order_id"
                emptyTitle="Sin cola operativa"
                emptyDescription="No existen pedidos pendientes de facturación en este momento."
              />
            </SectionCard>

            <SectionCard
              title="Pedidos en riesgo"
              subtitle="Pedidos con desviación entre entregas e importes facturados."
            >
              <DataTable
                columns={riskOrdersColumns}
                rows={data.riskOrders.slice(0, 6)}
                loading={loading}
                rowKey="order_id"
                emptyTitle="Sin pedidos en riesgo"
                emptyDescription="No se han detectado pedidos con incidencias de riesgo."
                compact
              />
            </SectionCard>
          </div>

          <div className="space-y-6">
            <SectionCard
              title="Resumen financiero en riesgo"
              subtitle="Vista agregada desde revenue-at-risk con distribución por antigüedad."
            >
              {loading ? (
                <LoadingState lines={4} />
              ) : data.revenueAtRisk.length ? (
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
              title="Riesgo por cliente"
              subtitle="Clientes con mayor exposición operativa y financiera."
            >
              <DataTable
                columns={clientRiskColumns}
                rows={data.clientRisk.slice(0, 6)}
                loading={loading}
                rowKey="client_id"
                emptyTitle="Sin clientes en riesgo"
                emptyDescription="No existen clientes con riesgo acumulado."
                compact
              />
            </SectionCard>
          </div>
        </section>
      </main>
    </>
  );
}
