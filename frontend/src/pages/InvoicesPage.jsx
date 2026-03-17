import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import DataTable from "../components/DataTable";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import LoadingState from "../components/LoadingState";
import OperationalStatusBadge from "../components/OperationalStatusBadge";
import SectionCard from "../components/SectionCard";
import SummaryCard from "../components/SummaryCard";
import { invoicesApi } from "../services/invoicesApi";
import { formatCurrency, formatDate, formatInteger } from "../utils/formatters";
import { normalizeCollection } from "../utils/apiData";
import { useAsyncData } from "../utils/useAsyncData";

function normalizeInvoiceRows(value) {
  return normalizeCollection(value).map((invoice, index) => ({
    id: invoice?.id ?? `invoice-${index}`,
    client_id: invoice?.client_id ?? null,
    order_id: invoice?.order_id ?? null,
    delivery_id: invoice?.delivery_id ?? null,
    invoice_number: invoice?.invoice_number || `Factura sin número ${index + 1}`,
    client_name: invoice?.client_name || "Cliente no informado",
    order_number: invoice?.order_number || "",
    delivery_number: invoice?.delivery_number || "",
    invoice_date: invoice?.invoice_date || invoice?.created_at || null,
    due_date: invoice?.due_date || null,
    status: invoice?.status || "-",
    total_amount: Number(invoice?.total_amount || 0),
    payment_status: invoice?.payment_status || "",
    hasDetailRoute: typeof invoice?.id === "number" || /^[0-9]+$/.test(String(invoice?.id || "")),
    hasClientRoute: typeof invoice?.client_id === "number" || /^[0-9]+$/.test(String(invoice?.client_id || "")),
    hasOrderRoute: typeof invoice?.order_id === "number" || /^[0-9]+$/.test(String(invoice?.order_id || "")),
    hasDeliveryRoute: typeof invoice?.delivery_id === "number" || /^[0-9]+$/.test(String(invoice?.delivery_id || "")),
  }));
}

function buildKpis(invoices) {
  const totalInvoices = invoices.length;
  const totalAmount = invoices.reduce((sum, invoice) => sum + Number(invoice.total_amount || 0), 0);
  const withDelivery = invoices.filter((invoice) => invoice.hasDeliveryRoute).length;
  const pendingAcceptance = invoices.filter((invoice) => invoice.status !== "accepted").length;

  return [
    {
      title: "Facturas visibles",
      value: formatInteger(totalInvoices),
      detail: "Documentos accesibles según rol y cartera comercial.",
    },
    {
      title: "Importe total",
      value: formatCurrency(totalAmount),
      detail: "Volumen económico visible de facturación.",
    },
    {
      title: "Con albarán relacionado",
      value: formatInteger(withDelivery),
      detail: "Facturas con trazabilidad hacia expedición.",
    },
    {
      title: "Pendientes documentales",
      value: formatInteger(pendingAcceptance),
      detail: "Facturas sin cierre documental definitivo.",
    },
  ];
}

export default function InvoicesPage() {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("date_desc");
  const { data: invoicesResponse, loading, error } = useAsyncData(invoicesApi.list, []);

  const invoices = useMemo(() => normalizeInvoiceRows(invoicesResponse), [invoicesResponse]);

  const filteredInvoices = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    const baseRows = normalizedSearch
      ? invoices.filter((invoice) =>
          [
            invoice.invoice_number,
            invoice.client_name,
            invoice.order_number,
            invoice.delivery_number,
            invoice.status,
            invoice.payment_status,
          ]
            .filter(Boolean)
            .some((value) => String(value).toLowerCase().includes(normalizedSearch)),
        )
      : invoices;

    const rows = [...baseRows];
    rows.sort((left, right) => {
      if (sort === "amount_desc") {
        return Number(right.total_amount || 0) - Number(left.total_amount || 0);
      }
      if (sort === "client_asc") {
        return String(left.client_name || "").localeCompare(String(right.client_name || ""), "es");
      }
      if (sort === "status_asc") {
        return String(left.status || "").localeCompare(String(right.status || ""), "es");
      }
      return new Date(right.invoice_date || 0) - new Date(left.invoice_date || 0);
    });
    return rows;
  }, [invoices, search, sort]);

  const columns = [
    {
      key: "invoice_number",
      header: "Factura",
      render: (row) => (
        <div>
          {row.hasDetailRoute ? (
            <Link to={`/invoices/${row.id}`} className="font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
              {row.invoice_number}
            </Link>
          ) : (
            <p className="font-semibold text-slate-900">{row.invoice_number}</p>
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
      key: "invoice_date",
      header: "Fecha",
      render: (row) => formatDate(row.invoice_date),
    },
    {
      key: "status",
      header: "Estado",
      render: (row) => <OperationalStatusBadge value={row.status} />,
    },
    {
      key: "due_date",
      header: "Vencimiento",
      render: (row) => formatDate(row.due_date),
    },
    {
      key: "total_amount",
      header: "Total",
      render: (row) => formatCurrency(row.total_amount),
    },
    {
      key: "payment_status",
      header: "Cobro",
      render: (row) => (row.payment_status ? <OperationalStatusBadge value={row.payment_status} /> : "-"),
    },
    {
      key: "action",
      header: "Acción",
      render: (row) => (
        row.hasDetailRoute ? (
          <div className="flex flex-col gap-1">
            <Link to={`/invoices/${row.id}`} className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
              Abrir detalle
            </Link>
            {row.hasDeliveryRoute ? (
              <Link to={`/deliveries/${row.delivery_id}`} className="text-xs text-slate-500 underline-offset-2 hover:text-slate-700 hover:underline">
                Abrir albarán
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
        title="Facturas"
        subtitle="Control documental y financiero con navegación rápida entre cliente, pedido, albarán y factura."
      />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState title="No se pudo cargar el módulo de facturas." message={error} /> : null}

        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {loading
            ? Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className="h-[144px] animate-pulse rounded-md border border-slate-200 bg-white shadow-panel" />
              ))
            : buildKpis(invoices).map((card) => <SummaryCard key={card.title} {...card} />)}
        </section>

        <section className="mt-6">
          <SectionCard
            title="Base de facturas"
            subtitle="Listado profesional para seguimiento documental y control financiero del ciclo pedido-albarán-factura."
            action={
              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Buscar por factura, cliente, pedido, albarán o estado"
                  className="w-full min-w-[300px] rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                />
                <select
                  value={sort}
                  onChange={(event) => setSort(event.target.value)}
                  className="rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                >
                  <option value="date_desc">Más recientes</option>
                  <option value="amount_desc">Mayor importe</option>
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
                rows={filteredInvoices}
                rowKey="id"
                emptyTitle="Sin facturas visibles"
                emptyDescription="No hay facturas disponibles para tu perfil o la búsqueda actual no ha devuelto resultados."
              />
            )}
          </SectionCard>
        </section>
      </main>
    </>
  );
}
