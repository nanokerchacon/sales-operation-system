import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import DataTable from "../components/DataTable";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import LoadingState from "../components/LoadingState";
import OperationalStatusBadge from "../components/OperationalStatusBadge";
import SectionCard from "../components/SectionCard";
import SummaryCard from "../components/SummaryCard";
import { deliveriesApi } from "../services/deliveriesApi";
import { formatCurrency, formatDate, formatInteger } from "../utils/formatters";
import { normalizeCollection } from "../utils/apiData";
import { useAsyncData } from "../utils/useAsyncData";

function normalizeDeliveryRows(value) {
  return normalizeCollection(value).map((delivery, index) => ({
    id: delivery?.id ?? `delivery-${index}`,
    order_id: delivery?.order_id ?? null,
    client_id: delivery?.client_id ?? null,
    delivery_number: delivery?.delivery_number || `Albarán sin número ${index + 1}`,
    client_name: delivery?.client_name || "Cliente no informado",
    order_number: delivery?.order_number || "",
    delivery_date: delivery?.delivery_date || delivery?.created_at || null,
    status: delivery?.status || "-",
    total_amount: Number(delivery?.total_amount || 0),
    invoice_status: delivery?.invoice_status || "-",
    hasDetailRoute: typeof delivery?.id === "number" || /^[0-9]+$/.test(String(delivery?.id || "")),
    hasClientRoute: typeof delivery?.client_id === "number" || /^[0-9]+$/.test(String(delivery?.client_id || "")),
    hasOrderRoute: typeof delivery?.order_id === "number" || /^[0-9]+$/.test(String(delivery?.order_id || "")),
  }));
}

function buildKpis(deliveries) {
  const totalDeliveries = deliveries.length;
  const totalAmount = deliveries.reduce((sum, delivery) => sum + Number(delivery.total_amount || 0), 0);
  const linkedOrders = deliveries.filter((delivery) => delivery.hasOrderRoute).length;
  const pendingInvoice = deliveries.filter((delivery) => delivery.invoice_status !== "invoice_accepted").length;

  return [
    {
      title: "Albaranes visibles",
      value: formatInteger(totalDeliveries),
      detail: "Documentos accesibles según rol y cartera comercial.",
    },
    {
      title: "Importe total",
      value: formatCurrency(totalAmount),
      detail: "Valor económico estimado sobre líneas entregadas.",
    },
    {
      title: "Con pedido origen",
      value: formatInteger(linkedOrders),
      detail: "Albaranes con trazabilidad directa hacia pedido.",
    },
    {
      title: "Pendientes de facturación",
      value: formatInteger(pendingInvoice),
      detail: "Documentos sin cierre documental completo.",
    },
  ];
}

export default function DeliveriesPage() {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("date_desc");
  const { data: deliveriesResponse, loading, error } = useAsyncData(deliveriesApi.list, []);

  const deliveries = useMemo(() => normalizeDeliveryRows(deliveriesResponse), [deliveriesResponse]);

  const filteredDeliveries = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    const baseRows = normalizedSearch
      ? deliveries.filter((delivery) =>
          [
            delivery.delivery_number,
            delivery.client_name,
            delivery.order_number,
            delivery.status,
            delivery.invoice_status,
          ]
            .filter(Boolean)
            .some((value) => String(value).toLowerCase().includes(normalizedSearch)),
        )
      : deliveries;

    const rows = [...baseRows];
    rows.sort((left, right) => {
      if (sort === "amount_desc") {
        return Number(right.total_amount || 0) - Number(left.total_amount || 0);
      }
      if (sort === "client_asc") {
        return String(left.client_name || "").localeCompare(String(right.client_name || ""), "es");
      }
      if (sort === "invoice_asc") {
        return String(left.invoice_status || "").localeCompare(String(right.invoice_status || ""), "es");
      }
      return new Date(right.delivery_date || 0) - new Date(left.delivery_date || 0);
    });
    return rows;
  }, [deliveries, search, sort]);

  const columns = [
    {
      key: "delivery_number",
      header: "Albarán",
      render: (row) => (
        <div>
          {row.hasDetailRoute ? (
            <Link to={`/deliveries/${row.id}`} className="font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
              {row.delivery_number}
            </Link>
          ) : (
            <p className="font-semibold text-slate-900">{row.delivery_number}</p>
          )}
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
      key: "order_number",
      header: "Pedido",
      render: (row) =>
        row.hasOrderRoute ? (
          <Link to={`/orders/${row.order_id}`} className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
            {row.order_number || `Pedido #${row.order_id}`}
          </Link>
        ) : (
          "-"
        ),
    },
    {
      key: "delivery_date",
      header: "Fecha",
      render: (row) => formatDate(row.delivery_date),
    },
    {
      key: "status",
      header: "Estado",
      render: (row) => <OperationalStatusBadge value={row.status} />,
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
            <Link to={`/deliveries/${row.id}`} className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
              Abrir detalle
            </Link>
            {row.hasOrderRoute ? (
              <Link to={`/orders/${row.order_id}`} className="text-xs text-slate-500 underline-offset-2 hover:text-slate-700 hover:underline">
                Abrir pedido
              </Link>
            ) : null}
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
        title="Albaranes"
        subtitle="Vista operativa de expediciones con navegación rápida hacia cliente, pedido y estado documental."
      />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState title="No se pudo cargar el módulo de albaranes." message={error} /> : null}

        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {loading
            ? Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="h-[144px] animate-pulse rounded-md border border-slate-200 bg-white shadow-panel" />
              ))
            : buildKpis(deliveries).map((card) => <SummaryCard key={card.title} {...card} />)}
        </section>

        <section className="mt-6">
          <SectionCard
            title="Base de albaranes"
            subtitle="Listado profesional para control logístico y preparación de la siguiente fase de facturación."
            action={
              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Buscar por albarán, cliente, pedido o estado"
                  className="w-full min-w-[280px] rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                />
                <select
                  value={sort}
                  onChange={(event) => setSort(event.target.value)}
                  className="rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                >
                  <option value="date_desc">Más recientes</option>
                  <option value="amount_desc">Mayor importe</option>
                  <option value="client_asc">Cliente</option>
                  <option value="invoice_asc">Estado documental</option>
                </select>
              </div>
            }
          >
            {loading ? (
              <LoadingState lines={6} />
            ) : (
              <DataTable
                columns={columns}
                rows={filteredDeliveries}
                rowKey="id"
                emptyTitle="Sin albaranes visibles"
                emptyDescription="No hay albaranes disponibles para tu perfil o la búsqueda actual no ha devuelto resultados."
              />
            )}
          </SectionCard>
        </section>
      </main>
    </>
  );
}
