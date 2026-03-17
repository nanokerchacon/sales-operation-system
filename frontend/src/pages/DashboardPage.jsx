import { Link, useNavigate } from "react-router-dom";
import AgingInvoicesChart from "../components/charts/AgingInvoicesChart";
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
      title: "Pedidos con incidencias",
      value: formatInteger(operations.orders_with_issues),
      detail: "Pedidos con desviaciones de entrega, emision o aceptacion.",
      tone: "alert",
    },
    {
      title: "Pedidos correctos",
      value: formatInteger(operations.orders_without_issues),
      detail: "Pedidos dentro de la operativa esperada.",
      tone: "success",
    },
    {
      title: "Pendiente de entregar",
      value: formatNumber(operations.total_pending_delivery_quantity),
      detail: "Unidades aun no servidas al cliente.",
      tone: "muted",
    },
    {
      title: "Pendiente documental",
      value: formatNumber(operations.total_pending_invoice_quantity),
      detail: "Unidades entregadas aun no aceptadas documentalmente.",
      tone: "default",
    },
  ];
}

function buildRevenueSummary(pendingRevenue) {
  return pendingRevenue.reduce(
    (summary, item) => {
      const amount = Number(item.amount_pending_invoice || 0);
      const daysSinceLastDelivery = Number(item.days_since_last_delivery || 0);
      summary.total += amount;

      if (daysSinceLastDelivery <= 3) {
        summary.bucket0to3 += amount;
      } else if (daysSinceLastDelivery <= 7) {
        summary.bucket4to7 += amount;
      } else if (daysSinceLastDelivery <= 15) {
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
      className={`rounded-xl border px-4 py-3 ${
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

function QuickAction({ to, label, detail }) {
  return (
    <Link
      to={to}
      className="rounded-xl border border-slate-200 bg-white px-4 py-4 transition hover:border-slate-300 hover:bg-slate-50"
    >
      <p className="text-sm font-semibold text-slate-900">{label}</p>
      <p className="mt-1 text-sm leading-6 text-slate-500">{detail}</p>
    </Link>
  );
}

function BlockError({ message }) {
  return <ErrorState title="Bloque no disponible" message={message} />;
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const { data, loading, error, blockErrors, lastUpdated } = useDashboardData();
  const kpis = buildKpis(data.operations);
  const revenueSummary = buildRevenueSummary(data.pendingRevenue);

  const workQueueColumns = [
    {
      key: "order_number",
      header: "Numero",
      render: (row) => (
        <button
          type="button"
          onClick={() => navigate(`/orders/${row.order_id}/traceability`)}
          className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline"
        >
          {row.order_number || `#${row.order_id}`}
        </button>
      ),
    },
    {
      key: "client_name",
      header: "Cliente",
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900">{row.client_name || "-"}</p>
          <p className="text-xs text-slate-500">ID cliente {row.client_id || "-"}</p>
        </div>
      ),
    },
    {
      key: "order_id",
      header: "Pedido",
      render: (row) => (
        <div>
          <p className="font-medium text-slate-900">Pedido #{row.order_id || "-"}</p>
          <p className="text-xs text-slate-500">{getDisplayStatus(row.order_status)}</p>
        </div>
      ),
    },
    {
      key: "delivered_quantity",
      header: "Entregado",
      align: "right",
      render: (row) => formatNumber(row.delivered_quantity),
    },
    {
      key: "invoiced_quantity",
      header: "Aceptado",
      align: "right",
      render: (row) => formatNumber(row.invoiced_quantity),
    },
    {
      key: "pending_acceptance_quantity",
      header: "Pend. aceptacion",
      align: "right",
      render: (row) => formatNumber(row.pending_acceptance_quantity),
    },
    {
      key: "pending_delivery_quantity",
      header: "Pend. entrega",
      align: "right",
      render: (row) => formatNumber(row.pending_delivery_quantity),
    },
    {
      key: "status",
      header: "Estado",
      render: (row) => <OperationalStatusBadge value={row.status} />,
    },
    {
      key: "invoice_document_status",
      header: "Estado doc.",
      render: (row) => <OperationalStatusBadge value={row.invoice_document_status} />,
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
      render: (row) => <span className="font-medium text-slate-900">{row.client_name || "-"}</span>,
    },
    {
      key: "orders_with_issues",
      header: "Pedidos con incidencias",
      align: "right",
      render: (row) => formatInteger(row.orders_with_issues),
    },
    {
      key: "total_pending_invoice_quantity",
      header: "Cantidad pendiente",
      align: "right",
      render: (row) => formatNumber(row.total_pending_invoice_quantity),
    },
    {
      key: "total_pending_invoice_amount",
      header: "Importe pendiente",
      align: "right",
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
      render: (row) => <span className="font-medium text-slate-900">{row.client_name || "-"}</span>,
    },
    {
      key: "order_id",
      header: "Pedido",
      render: (row) => (
        <button
          type="button"
          onClick={() => navigate(`/orders/${row.order_id}/traceability`)}
          className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline"
        >
          {row.order_number || `#${row.order_id}`}
        </button>
      ),
    },
    {
      key: "amount_pending_invoice",
      header: "Pendiente",
      align: "right",
      render: (row) => formatCurrency(row.amount_pending_invoice),
    },
    {
      key: "invoice_document_status",
      header: "Estado doc.",
      render: (row) => <OperationalStatusBadge value={row.invoice_document_status} />,
    },
    {
      key: "status_es",
      header: "Situacion",
      render: (row) => <OperationalStatusBadge value={row.status} />,
    },
  ];

  const incidentOrdersColumns = [
    {
      key: "client_name",
      header: "Cliente",
      render: (row) => <span className="font-medium text-slate-900">{row.client_name || "-"}</span>,
    },
    {
      key: "order_id",
      header: "Pedido",
      render: (row) => (
        <button
          type="button"
          onClick={() => navigate(`/orders/${row.order_id}/traceability`)}
          className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline"
        >
          {row.order_number || `#${row.order_id}`}
        </button>
      ),
    },
    {
      key: "pending_invoice_quantity",
      header: "Pendiente",
      align: "right",
      render: (row) => formatNumber(row.pending_invoice_quantity),
    },
    {
      key: "invoice_document_status",
      header: "Estado doc.",
      render: (row) => <OperationalStatusBadge value={row.invoice_document_status} />,
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
        subtitle="Vision consolidada de operaciones, facturacion pendiente y control operativo."
        lastUpdated={lastUpdated}
      />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState title="Estado parcial del dashboard" message={error} /> : null}

        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5">
          {loading ? (
            <LoadingState lines={5} variant="cards" className="md:col-span-2 xl:col-span-3 2xl:col-span-5" />
          ) : kpis.length ? (
            kpis.map((kpi) => <KpiCard key={kpi.title} {...kpi} />)
          ) : blockErrors.operations ? (
            <div className="md:col-span-2 xl:col-span-3 2xl:col-span-5"><BlockError message={blockErrors.operations} /></div>
          ) : (
            <div className="md:col-span-2 xl:col-span-3 2xl:col-span-5">
              <EmptyState title="Sin KPIs operativos" description="Todavia no hay metricas globales disponibles para mostrar en el dashboard." />
            </div>
          )}
        </section>

        <section className="mt-6">
          <SectionCard
            title="Acciones rapidas"
            subtitle="Accesos directos para las tareas mas habituales del ERP."
          >
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <QuickAction to="/incidents/new" label="Nueva incidencia" detail="Registrar una incidencia y generar propuesta asistida." />
              <QuickAction to="/invoices" label="Ver facturas" detail="Revisar facturacion, estados y pendientes documentales." />
              <QuickAction to="/orders" label="Ver pedidos" detail="Consultar operativa, trazabilidad y estados de pedido." />
              <QuickAction to="/clients" label="Ver clientes" detail="Acceder a cartera, detalle comercial y actividad reciente." />
            </div>
          </SectionCard>
        </section>

        <section className="mt-6">
          <SectionCard
            title="Resumen de estados operativos"
            subtitle="Distribucion real del flujo de pedido, entrega, emision y aceptacion documental."
          >
            {loading ? (
              <LoadingState lines={4} />
            ) : blockErrors.orderStatusSummary ? (
              <BlockError message={blockErrors.orderStatusSummary} />
            ) : data.orderStatusSummary ? (
              <StatusSummaryCards summary={data.orderStatusSummary} formatValue={formatInteger} />
            ) : (
              <EmptyState title="Sin resumen operativo" description="No hay distribucion de estados disponible para el periodo actual." />
            )}
          </SectionCard>
        </section>

        <section className="mt-6 grid gap-6 2xl:grid-cols-2">
          <SectionCard
            title="Facturacion pendiente por antiguedad"
            subtitle="Distribucion ejecutiva de importes pendientes segun su envejecimiento documental."
          >
            {loading ? (
              <LoadingState lines={5} />
            ) : blockErrors.agingInvoices ? (
              <BlockError message={blockErrors.agingInvoices} />
            ) : (
              <AgingInvoicesChart agingInvoices={data.agingInvoices} />
            )}
          </SectionCard>

          <SectionCard
            title="Estado documental de facturas"
            subtitle="Separacion entre aceptacion definitiva y facturas aun pendientes de validacion."
          >
            {loading ? (
              <LoadingState lines={4} />
            ) : blockErrors.operations ? (
              <BlockError message={blockErrors.operations} />
            ) : data.operations ? (
              <div className="grid gap-3 md:grid-cols-2">
                <SummaryMetric
                  label="Pedidos con factura aceptada"
                  value={formatInteger(data.operations.accepted_invoice_orders)}
                  accent
                />
                <SummaryMetric
                  label="Pedidos pendientes de aceptacion"
                  value={formatInteger(data.operations.pending_acceptance_invoice_orders)}
                />
                <SummaryMetric
                  label="Cantidad aceptada"
                  value={formatNumber(data.operations.total_accepted_invoice_quantity)}
                />
                <SummaryMetric
                  label="Cantidad pendiente aceptacion"
                  value={formatNumber(data.operations.total_pending_acceptance_quantity)}
                />
              </div>
            ) : (
              <EmptyState
                title="Sin estado documental"
                description="No hay datos documentales agregados para mostrar en este momento."
              />
            )}
          </SectionCard>
        </section>

        <section className="mt-6 grid gap-6 xl:grid-cols-dashboard">
          <div className="space-y-6">
            <SectionCard
              title="Cola operativa"
              subtitle="Pedidos priorizados por estado operativo y documental."
            >
              {blockErrors.workQueue && !loading ? <div className="mb-4"><BlockError message={blockErrors.workQueue} /></div> : null}
              <div className="operational-queue-table-wrapper w-full overflow-x-auto [&>div]:overflow-visible [&_table]:min-w-[1200px] [&_table]:w-full">
                <DataTable
                  columns={workQueueColumns}
                  rows={data.workQueue}
                  loading={loading}
                  rowKey="order_id"
                  emptyTitle="Sin cola operativa"
                  emptyDescription="Cuando existan pedidos con seguimiento activo apareceran aqui."
                  emptyAction={<Link to="/orders" className="inline-flex rounded-md border border-slate-900 px-4 py-2.5 text-sm font-medium text-slate-900 transition hover:bg-slate-900 hover:text-white">Ver pedidos</Link>}
                />
              </div>
            </SectionCard>

            <SectionCard
              title="Pedidos con incidencias"
              subtitle="Pedidos con desviaciones entre entrega, facturacion y aceptacion."
            >
              {blockErrors.ordersWithIncidents && !loading ? <div className="mb-4"><BlockError message={blockErrors.ordersWithIncidents} /></div> : null}
              <DataTable
                columns={incidentOrdersColumns}
                rows={data.ordersWithIncidents.slice(0, 6)}
                loading={loading}
                rowKey="order_id"
                emptyTitle="Sin pedidos con incidencias"
                emptyDescription="No se han detectado incidencias operativas en pedidos durante este periodo."
                emptyAction={<Link to="/incidents" className="inline-flex rounded-md border border-slate-900 px-4 py-2.5 text-sm font-medium text-slate-900 transition hover:bg-slate-900 hover:text-white">Ver incidencias</Link>}
                compact
              />
            </SectionCard>
          </div>

          <div className="space-y-6">
            <SectionCard
              title="Resumen de facturacion pendiente"
              subtitle="Vista agregada del cierre documental pendiente con distribucion por antiguedad."
            >
              {loading ? (
                <LoadingState lines={4} />
              ) : blockErrors.pendingRevenue ? (
                <BlockError message={blockErrors.pendingRevenue} />
              ) : data.pendingRevenue.length ? (
                <div className="space-y-4">
                  <SummaryMetric
                    label="Total pendiente de cierre"
                    value={formatCurrency(revenueSummary.total)}
                    accent
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <SummaryMetric label="0 a 3 dias" value={formatCurrency(revenueSummary.bucket0to3)} />
                    <SummaryMetric label="4 a 7 dias" value={formatCurrency(revenueSummary.bucket4to7)} />
                    <SummaryMetric label="8 a 15 dias" value={formatCurrency(revenueSummary.bucket8to15)} />
                    <SummaryMetric label="Mas de 15 dias" value={formatCurrency(revenueSummary.bucketOver15)} />
                  </div>
                </div>
              ) : (
                <EmptyState
                  title="Sin resumen financiero"
                  description="No hay importes pendientes de cierre documental para mostrar ahora mismo."
                />
              )}
            </SectionCard>

            <SectionCard
              title="Aging de facturas"
              subtitle="Bloque consolidado para seguimiento ejecutivo del pendiente de cobro documental."
            >
              {loading ? (
                <LoadingState lines={4} />
              ) : blockErrors.agingInvoices ? (
                <BlockError message={blockErrors.agingInvoices} />
              ) : data.agingInvoices ? (
                <div className="space-y-3">
                  <SummaryMetric
                    label="Total pendiente"
                    value={formatCurrency(data.agingInvoices.total_pending_invoice_amount)}
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <SummaryMetric label="0 a 3 dias" value={formatCurrency(data.agingInvoices.bucket_0_3_days)} />
                    <SummaryMetric label="4 a 7 dias" value={formatCurrency(data.agingInvoices.bucket_4_7_days)} />
                    <SummaryMetric label="8 a 15 dias" value={formatCurrency(data.agingInvoices.bucket_8_15_days)} />
                    <SummaryMetric label="Mas de 15 dias" value={formatCurrency(data.agingInvoices.bucket_over_15_days)} />
                  </div>
                </div>
              ) : (
                <EmptyState
                  title="Sin aging disponible"
                  description="No hay importes pendientes que clasificar por antiguedad."
                />
              )}
            </SectionCard>

            <SectionCard
              title="Facturacion pendiente prioritaria"
              subtitle="Pedidos pendientes de emision o aceptacion con mayor impacto economico."
            >
              {blockErrors.pendingInvoices && !loading ? <div className="mb-4"><BlockError message={blockErrors.pendingInvoices} /></div> : null}
              <DataTable
                columns={pendingInvoiceColumns}
                rows={data.pendingInvoices.slice(0, 5)}
                loading={loading}
                rowKey="order_id"
                emptyTitle="Sin facturacion pendiente"
                emptyDescription="No existen importes pendientes de cierre documental en este momento."
                emptyAction={<Link to="/invoices" className="inline-flex rounded-md border border-slate-900 px-4 py-2.5 text-sm font-medium text-slate-900 transition hover:bg-slate-900 hover:text-white">Ir a facturas</Link>}
                compact
              />
            </SectionCard>

            <SectionCard
              title="Incidencias por cliente"
              subtitle="Clientes con mayor carga operativa y cierre documental pendiente."
            >
              {blockErrors.clientsWithIncidents && !loading ? <div className="mb-4"><BlockError message={blockErrors.clientsWithIncidents} /></div> : null}
              <DataTable
                columns={clientIncidentsColumns}
                rows={data.clientsWithIncidents.slice(0, 6)}
                loading={loading}
                rowKey="client_id"
                emptyTitle="Sin clientes con incidencias"
                emptyDescription="Cuando existan clientes con carga operativa acumulada apareceran aqui."
                emptyAction={<Link to="/clients" className="inline-flex rounded-md border border-slate-900 px-4 py-2.5 text-sm font-medium text-slate-900 transition hover:bg-slate-900 hover:text-white">Ver clientes</Link>}
                compact
              />
            </SectionCard>
          </div>
        </section>
      </main>
    </>
  );
}
