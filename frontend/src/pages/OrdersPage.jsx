import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import DataTable from "../components/DataTable";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import LoadingState from "../components/LoadingState";
import OperationalStatusBadge from "../components/OperationalStatusBadge";
import SectionCard from "../components/SectionCard";
import SummaryCard from "../components/SummaryCard";
import { ordersApi } from "../services/ordersApi";
import { formatCurrency, formatDate, formatInteger } from "../utils/formatters";
import { normalizeCollection } from "../utils/apiData";
import { useAsyncData } from "../utils/useAsyncData";

function normalizeOrderRows(value) {
  return normalizeCollection(value).map((order, index) => ({
    id: order?.id ?? `order-${index}`,
    client_id: order?.client_id ?? null,
    order_number: order?.order_number || `Pedido sin número ${index + 1}`,
    client_name: order?.client_name || order?.client_name_snapshot || "Cliente no informado",
    order_date: order?.order_date || null,
    status: order?.status || "-",
    total_amount: Number(order?.total_amount || 0),
    delivery_status: order?.delivery_status || "-",
    invoice_status: order?.invoice_status || "-",
    hasDetailRoute: typeof order?.id === "number" || /^[0-9]+$/.test(String(order?.id || "")),
    hasClientRoute: typeof order?.client_id === "number" || /^[0-9]+$/.test(String(order?.client_id || "")),
  }));
}

function buildKpis(orders) {
  const totalOrders = orders.length;
  const totalAmount = orders.reduce((sum, order) => sum + Number(order.total_amount || 0), 0);
  const pendingDelivery = orders.filter((order) => order.delivery_status !== "delivered").length;
  const pendingInvoice = orders.filter((order) => order.invoice_status !== "invoice_accepted").length;

  return [
    {
      title: "Pedidos visibles",
      value: formatInteger(totalOrders),
      detail: "Pedidos accesibles según rol y cartera.",
    },
    {
      title: "Importe total",
      value: formatCurrency(totalAmount),
      detail: "Volumen económico total visible.",
    },
    {
      title: "Pendientes de entrega",
      value: formatInteger(pendingDelivery),
      detail: "Pedidos que siguen abiertos logísticamente.",
    },
    {
      title: "Pendientes de facturación",
      value: formatInteger(pendingInvoice),
      detail: "Pedidos sin cierre documental completo.",
    },
  ];
}

export default function OrdersPage() {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("date_desc");
  const { data: ordersResponse, loading, error } = useAsyncData(ordersApi.list, []);

  const orders = useMemo(() => normalizeOrderRows(ordersResponse), [ordersResponse]);

  const filteredOrders = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    const baseRows = normalizedSearch
      ? orders.filter((order) =>
          [order.order_number, order.client_name, order.status, order.delivery_status, order.invoice_status]
            .filter(Boolean)
            .some((value) => String(value).toLowerCase().includes(normalizedSearch)),
        )
      : orders;

    const rows = [...baseRows];
    rows.sort((left, right) => {
      if (sort === "total_desc") {
        return Number(right.total_amount || 0) - Number(left.total_amount || 0);
      }
      if (sort === "client_asc") {
        return String(left.client_name || "").localeCompare(String(right.client_name || ""), "es");
      }
      if (sort === "status_asc") {
        return String(left.status || "").localeCompare(String(right.status || ""), "es");
      }
      return new Date(right.order_date || 0) - new Date(left.order_date || 0);
    });
    return rows;
  }, [orders, search, sort]);

  const columns = [
    {
      key: "order_number",
      header: "Pedido",
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900">{row.order_number}</p>
          <p className="text-xs text-slate-500">ID {row.id}</p>
        </div>
      ),
    },
    {
      key: "client_name",
      header: "Cliente",
      render: (row) => (
        row.hasClientRoute ? (
          <Link to={`/clients/${row.client_id}`} className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
            {row.client_name}
          </Link>
        ) : (
          <span className="font-medium text-slate-900">{row.client_name}</span>
        )
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
      key: "total_amount",
      header: "Total",
      render: (row) => formatCurrency(row.total_amount),
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
      key: "action",
      header: "Acción",
      render: (row) => (
        row.hasDetailRoute ? (
          <div className="flex flex-col gap-1">
            <Link to={`/orders/${row.id}`} className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
              Abrir detalle
            </Link>
            <Link to={`/orders/${row.id}/traceability`} className="text-xs text-slate-500 underline-offset-2 hover:text-slate-700 hover:underline">
              Ver trazabilidad
            </Link>
          </div>
        ) : (
          <span className="text-sm text-slate-500">Sin detalle disponible</span>
        )
      ),
    },
  ];

  return (
    <>
      <Header
        title="Pedidos"
        subtitle="Núcleo operativo de pedidos con foco comercial, logístico y documental en una sola vista."
      />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState title="No se pudo cargar el módulo de pedidos." message={error} /> : null}

        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {loading
            ? Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="h-[144px] animate-pulse rounded-md border border-slate-200 bg-white shadow-panel" />
              ))
            : buildKpis(orders).map((card) => <SummaryCard key={card.title} {...card} />)}
        </section>

        <section className="mt-6">
          <SectionCard
            title="Base de pedidos"
            subtitle="Listado profesional para seguimiento comercial y operativo del ciclo pedido-entrega-factura."
            action={
              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Buscar por pedido, cliente o estado"
                  className="w-full min-w-[260px] rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                />
                <select
                  value={sort}
                  onChange={(event) => setSort(event.target.value)}
                  className="rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                >
                  <option value="date_desc">Más recientes</option>
                  <option value="total_desc">Mayor importe</option>
                  <option value="client_asc">Cliente</option>
                  <option value="status_asc">Estado</option>
                </select>
              </div>
            }
          >
            {loading ? (
              <LoadingState lines={6} />
            ) : (
              <DataTable
                columns={columns}
                rows={filteredOrders}
                rowKey="id"
                emptyTitle="Sin pedidos visibles"
                emptyDescription="No hay pedidos disponibles para tu perfil o la búsqueda no ha devuelto resultados."
              />
            )}
          </SectionCard>
        </section>
      </main>
    </>
  );
}
