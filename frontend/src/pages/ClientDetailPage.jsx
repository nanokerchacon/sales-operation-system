import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import DataTable from "../components/DataTable";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import LoadingState from "../components/LoadingState";
import OperationalStatusBadge from "../components/OperationalStatusBadge";
import SectionCard from "../components/SectionCard";
import SummaryCard from "../components/SummaryCard";
import { clientsApi } from "../services/clientsApi";
import { formatCurrency, formatDate, formatInteger } from "../utils/formatters";
import { useAsyncData } from "../utils/useAsyncData";

const tabs = [
  { key: "summary", label: "Resumen" },
  { key: "orders", label: "Pedidos" },
  { key: "deliveries", label: "Albaranes" },
  { key: "invoices", label: "Facturas" },
  { key: "incidents", label: "Incidencias" },
];

function PlaceholderPanel({ title, description }) {
  return (
    <SectionCard title={title} subtitle={description}>
      <EmptyState
        title="Preparado para la siguiente fase"
        description="La estructura del módulo ya está lista para conectar datos reales sin rehacer la navegación del cliente."
      />
    </SectionCard>
  );
}

export default function ClientDetailPage() {
  const { clientId } = useParams();
  const [activeTab, setActiveTab] = useState("summary");
  const {
    data: client,
    loading: clientLoading,
    error: clientError,
  } = useAsyncData(() => clientsApi.getById(clientId), [clientId]);
  const {
    data: ordersResponse,
    loading: ordersLoading,
    error: ordersError,
  } = useAsyncData(() => clientsApi.getOrders(clientId), [clientId]);

  const orders = ordersResponse?.orders || [];

  const summaryCards = useMemo(() => {
    if (!client) {
      return [];
    }
    return [
      {
        title: "Total pedidos",
        value: formatInteger(client.summary.order_count),
        detail: "Pedidos visibles para el perfil actual.",
      },
      {
        title: "Volumen acumulado",
        value: formatCurrency(client.summary.total_order_amount),
        detail: "Importe total pedido acumulado del cliente.",
      },
      {
        title: "Último pedido",
        value: client.summary.last_order_date ? formatDate(client.summary.last_order_date) : "-",
        detail: "Fecha más reciente de actividad comercial registrada.",
      },
      {
        title: "Estado general",
        value: client.summary.order_count > 0 ? "Activo" : "Sin pedidos",
        detail: "Indicador simple de actividad comercial actual.",
      },
    ];
  }, [client]);

  const orderColumns = [
    {
      key: "order_number",
      header: "Pedido",
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900">{row.order_number}</p>
          <p className="text-xs text-slate-500">Pedido #{row.id}</p>
        </div>
      ),
    },
    {
      key: "order_date",
      header: "Fecha",
      render: (row) => formatDate(row.order_date),
    },
    {
      key: "status",
      header: "Estado",
      render: (row) => <OperationalStatusBadge value={row.status} />,
    },
    {
      key: "delivery_status",
      header: "Entrega",
      render: (row) => <OperationalStatusBadge value={row.delivery_status} />,
    },
    {
      key: "invoice_status",
      header: "Facturación",
      render: (row) => <OperationalStatusBadge value={row.invoice_status} />,
    },
    {
      key: "total_amount",
      header: "Total",
      render: (row) => formatCurrency(row.total_amount),
    },
    {
      key: "action",
      header: "Acción",
      render: (row) => (
        <div className="flex flex-col gap-1">
          <Link
            to={`/orders/${row.id}`}
            className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline"
          >
            Abrir pedido
          </Link>
          <Link
            to={`/orders/${row.id}/traceability`}
            className="text-xs text-slate-500 underline-offset-2 hover:text-slate-700 hover:underline"
          >
            Ver trazabilidad
          </Link>
        </div>
      ),
    },
  ];

  const isLoading = clientLoading || ordersLoading;
  const error = clientError || ordersError;

  function renderActiveTab() {
    if (activeTab === "summary") {
      return (
        <SectionCard
          title="Resumen operativo"
          subtitle="Datos maestros y contexto comercial base del cliente."
        >
          {client ? (
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">CIF/NIF</p>
                <p className="mt-2 text-sm text-slate-900">{client.tax_id || "-"}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Email</p>
                <p className="mt-2 text-sm text-slate-900">{client.email || "-"}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Teléfono</p>
                <p className="mt-2 text-sm text-slate-900">{client.phone || "-"}</p>
              </div>
              <div className="md:col-span-2 xl:col-span-3">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Dirección / ubicación</p>
                <p className="mt-2 text-sm text-slate-900">{client.location || "-"}</p>
              </div>
            </div>
          ) : null}
        </SectionCard>
      );
    }

    if (activeTab === "orders") {
      return (
        <SectionCard
          title="Historial de pedidos"
          subtitle="Pedidos reales asociados al cliente con acceso directo a detalle y trazabilidad."
        >
          <DataTable
            columns={orderColumns}
            rows={orders}
            rowKey="id"
            emptyTitle="Sin pedidos asociados"
            emptyDescription="Este cliente no tiene pedidos visibles para tu perfil en este momento."
          />
        </SectionCard>
      );
    }

    if (activeTab === "deliveries") {
      return <PlaceholderPanel title="Albaranes" description="Estructura preparada para la futura pestaña de albaranes del cliente." />;
    }

    if (activeTab === "invoices") {
      return <PlaceholderPanel title="Facturas" description="Estructura preparada para la futura pestaña de facturas del cliente." />;
    }

    return <PlaceholderPanel title="Incidencias" description="Estructura preparada para la futura pestaña de incidencias del cliente." />;
  }

  return (
    <>
      <Header
        title={isLoading ? "Cliente" : client?.name || "Cliente"}
        subtitle="Ficha base del cliente con resumen operativo y navegación comercial hacia sus pedidos."
      />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState title="No se pudo cargar la ficha de cliente." message={error} /> : null}

        <div className="mb-6 flex items-center gap-3 text-sm text-slate-500">
          <Link to="/clients" className="font-medium text-slate-700 hover:text-slate-900">
            Clientes
          </Link>
          <span>/</span>
          <span>{client?.name || "Ficha"}</span>
        </div>

        <SectionCard
          title="Cabecera del cliente"
          subtitle="Datos maestros principales del cliente y punto de acceso a su futura vista 360."
        >
          {isLoading ? (
            <LoadingState lines={4} />
          ) : client ? (
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Cliente</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{client.name}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">CIF/NIF</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{client.tax_id || "-"}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Email</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{client.email || "-"}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Teléfono</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{client.phone || "-"}</p>
              </div>
            </div>
          ) : null}
        </SectionCard>

        <section className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {isLoading
            ? Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="h-[144px] animate-pulse rounded-md border border-slate-200 bg-white shadow-panel" />
              ))
            : summaryCards.map((card) => <SummaryCard key={card.title} {...card} />)}
        </section>

        <section className="mt-6">
          <div className="flex flex-wrap gap-2 rounded-md border border-slate-200 bg-white p-2 shadow-panel">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={[
                  "rounded-md px-4 py-2.5 text-sm font-medium transition",
                  activeTab === tab.key
                    ? "bg-slate-900 text-white"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                ].join(" ")}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </section>

        <section className="mt-6">{renderActiveTab()}</section>
      </main>
    </>
  );
}
