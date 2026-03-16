import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import DataTable from "../components/DataTable";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import LoadingState from "../components/LoadingState";
import SectionCard from "../components/SectionCard";
import SummaryCard from "../components/SummaryCard";
import { clientsApi } from "../services/clientsApi";
import { formatCurrency, formatDate, formatInteger } from "../utils/formatters";
import { useAsyncData } from "../utils/useAsyncData";

function buildKpis(clients) {
  const totalClients = clients.length;
  const clientsWithOrders = clients.filter((client) => client.order_count > 0).length;
  const totalVolume = clients.reduce((sum, client) => sum + Number(client.total_order_amount || 0), 0);
  const lastOrderDate = clients
    .map((client) => client.last_order_date)
    .filter(Boolean)
    .sort((left, right) => new Date(right) - new Date(left))[0];

  return [
    {
      title: "Clientes accesibles",
      value: formatInteger(totalClients),
      detail: "Clientes visibles según tu perfil y alcance.",
    },
    {
      title: "Con pedidos",
      value: formatInteger(clientsWithOrders),
      detail: "Clientes con historial comercial registrado.",
    },
    {
      title: "Volumen acumulado",
      value: formatCurrency(totalVolume),
      detail: "Importe total pedido acumulado visible.",
    },
    {
      title: "Último pedido",
      value: lastOrderDate ? formatDate(lastOrderDate) : "-",
      detail: "Fecha más reciente de actividad comercial.",
    },
  ];
}

export default function ClientsPage() {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("name_asc");
  const { data: clients = [], loading, error } = useAsyncData(clientsApi.list, []);

  const filteredClients = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    const baseRows = normalizedSearch
      ? clients.filter((client) =>
          [client.name, client.tax_id, client.email]
            .filter(Boolean)
            .some((value) => value.toLowerCase().includes(normalizedSearch)),
        )
      : clients;

    const rows = [...baseRows];
    rows.sort((left, right) => {
      if (sort === "volume_desc") {
        return Number(right.total_order_amount || 0) - Number(left.total_order_amount || 0);
      }
      if (sort === "last_order_desc") {
        return new Date(right.last_order_date || 0) - new Date(left.last_order_date || 0);
      }
      if (sort === "orders_desc") {
        return Number(right.order_count || 0) - Number(left.order_count || 0);
      }
      return left.name.localeCompare(right.name, "es");
    });
    return rows;
  }, [clients, search, sort]);

  const columns = [
    {
      key: "name",
      header: "Cliente",
      render: (row) => (
        <div>
          <p className="font-semibold text-slate-900">{row.name}</p>
          <p className="text-xs text-slate-500">ID {row.id}</p>
        </div>
      ),
    },
    {
      key: "tax_id",
      header: "CIF/NIF",
      render: (row) => row.tax_id || "-",
    },
    {
      key: "location",
      header: "Ubicación",
      render: (row) => <span className="line-clamp-2">{row.location || "-"}</span>,
    },
    {
      key: "contact",
      header: "Contacto",
      render: (row) => (
        <div>
          <p className="text-slate-900">{row.email || "-"}</p>
          <p className="text-xs text-slate-500">{row.phone || "Sin teléfono"}</p>
        </div>
      ),
    },
    {
      key: "order_count",
      header: "Pedidos",
      render: (row) => formatInteger(row.order_count),
    },
    {
      key: "last_order_date",
      header: "Último pedido",
      render: (row) => formatDate(row.last_order_date),
    },
    {
      key: "total_order_amount",
      header: "Volumen",
      render: (row) => formatCurrency(row.total_order_amount),
    },
    {
      key: "action",
      header: "Acción",
      render: (row) => (
        <Link
          to={`/clients/${row.id}`}
          className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline"
        >
          Abrir ficha
        </Link>
      ),
    },
  ];

  return (
    <>
      <Header
        title="Clientes"
        subtitle="Listado operativo de clientes con actividad comercial agregada y acceso directo a su ficha."
      />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState title="No se pudo cargar el módulo de clientes." message={error} /> : null}

        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {loading ? (
            Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="h-[144px] animate-pulse rounded-md border border-slate-200 bg-white shadow-panel" />
            ))
          ) : (
            buildKpis(clients).map((card) => <SummaryCard key={card.title} {...card} />)
          )}
        </section>

        <section className="mt-6">
          <SectionCard
            title="Base de clientes"
            subtitle="Vista consolidada del maestro comercial con métricas y acceso a ficha."
            action={
              <div className="flex flex-col gap-3 sm:flex-row">
                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Buscar por nombre, CIF o email"
                  className="w-full min-w-[260px] rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                />
                <select
                  value={sort}
                  onChange={(event) => setSort(event.target.value)}
                  className="rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                >
                  <option value="name_asc">Nombre</option>
                  <option value="orders_desc">Más pedidos</option>
                  <option value="last_order_desc">Último pedido</option>
                  <option value="volume_desc">Mayor volumen</option>
                </select>
              </div>
            }
          >
            {loading ? (
              <LoadingState lines={6} />
            ) : (
              <DataTable
                columns={columns}
                rows={filteredClients}
                rowKey="id"
                emptyTitle="Sin clientes visibles"
                emptyDescription="No hay clientes disponibles para tu perfil o la búsqueda no ha devuelto resultados."
              />
            )}
          </SectionCard>
        </section>
      </main>
    </>
  );
}
