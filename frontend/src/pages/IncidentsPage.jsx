import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import DataTable from "../components/DataTable";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import IncidentTypeBadge from "../components/IncidentTypeBadge";
import LoadingState from "../components/LoadingState";
import OperationalStatusBadge from "../components/OperationalStatusBadge";
import PriorityBadge from "../components/PriorityBadge";
import SectionCard from "../components/SectionCard";
import SummaryCard from "../components/SummaryCard";
import { incidentsApi } from "../services/incidentsApi";
import { formatDate, formatInteger } from "../utils/formatters";
import { useAsyncData } from "../utils/useAsyncData";

function buildKpis(incidents) {
  const total = incidents.length;
  const open = incidents.filter((incident) => ["abierta", "en_proceso"].includes(incident.status)).length;
  const resolved = incidents.filter((incident) => ["resuelta", "cerrada"].includes(incident.status)).length;
  const critical = incidents.filter((incident) => incident.priority === "critica").length;

  return [
    { title: "Incidencias visibles", value: formatInteger(total), detail: "Registros accesibles según rol y cartera." },
    { title: "Abiertas o en proceso", value: formatInteger(open), detail: "Trabajo operativo pendiente de cierre." },
    { title: "Resueltas o cerradas", value: formatInteger(resolved), detail: "Incidencias ya estabilizadas." },
    { title: "Críticas", value: formatInteger(critical), detail: "Incidencias de mayor urgencia." },
  ];
}

function resolveDocumentLabel(row) {
  if (row.invoice_number) {
    return `Factura ${row.invoice_number}`;
  }
  if (row.delivery_number) {
    return `Albarán ${row.delivery_number}`;
  }
  if (row.order_number) {
    return `Pedido ${row.order_number}`;
  }
  return "Cliente";
}

export default function IncidentsPage() {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("date_desc");
  const { data: incidents = [], loading, error } = useAsyncData(incidentsApi.list, []);

  const filteredIncidents = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    const baseRows = normalizedSearch
      ? incidents.filter((incident) =>
          [incident.incident_number, incident.client_name, incident.type, incident.status, incident.priority, incident.title]
            .filter(Boolean)
            .some((value) => value.toLowerCase().includes(normalizedSearch)),
        )
      : incidents;

    const rows = [...baseRows];
    rows.sort((left, right) => {
      if (sort === "priority_desc") {
        const order = { critica: 4, alta: 3, media: 2, baja: 1 };
        return (order[right.priority] || 0) - (order[left.priority] || 0);
      }
      if (sort === "status_asc") {
        return String(left.status || "").localeCompare(String(right.status || ""), "es");
      }
      if (sort === "client_asc") {
        return left.client_name.localeCompare(right.client_name, "es");
      }
      return new Date(right.created_at || 0) - new Date(left.created_at || 0);
    });
    return rows;
  }, [incidents, search, sort]);

  const columns = [
    {
      key: "incident_number",
      header: "Incidencia",
      render: (row) => (
        <div>
          <Link to={`/incidents/${row.id}`} className="font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
            {row.incident_number}
          </Link>
          <p className="text-xs text-slate-500 line-clamp-1">{row.title}</p>
        </div>
      ),
    },
    {
      key: "client_name",
      header: "Cliente",
      render: (row) => (
        <Link to={`/clients/${row.client_id}`} className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
          {row.client_name}
        </Link>
      ),
    },
    {
      key: "type",
      header: "Tipo",
      render: (row) => <IncidentTypeBadge value={row.type} />,
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
    {
      key: "document",
      header: "Documento relacionado",
      render: (row) => <span>{resolveDocumentLabel(row)}</span>,
    },
    {
      key: "created_at",
      header: "Fecha",
      render: (row) => formatDate(row.created_at),
    },
    {
      key: "action",
      header: "Acción",
      render: (row) => (
        <Link to={`/incidents/${row.id}`} className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
          Abrir detalle
        </Link>
      ),
    },
  ];

  return (
    <>
      <Header title="Incidencias" subtitle="Gestión operativa, documental y comercial de incidencias vinculadas a clientes y documentos." />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState title="No se pudo cargar el módulo de incidencias." message={error} /> : null}

        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {loading
            ? Array.from({ length: 4 }).map((_, index) => <div key={index} className="h-[144px] animate-pulse rounded-md border border-slate-200 bg-white shadow-panel" />)
            : buildKpis(incidents).map((card) => <SummaryCard key={card.title} {...card} />)}
        </section>

        <section className="mt-6">
          <SectionCard
            title="Base de incidencias"
            subtitle="Listado profesional para priorizar trabajo, revisar afectación documental y navegar entre módulos."
            action={
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Buscar por incidencia, cliente, título o estado"
                  className="w-full min-w-[280px] rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                />
                <select
                  value={sort}
                  onChange={(event) => setSort(event.target.value)}
                  className="rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                >
                  <option value="date_desc">Más recientes</option>
                  <option value="priority_desc">Mayor prioridad</option>
                  <option value="status_asc">Estado</option>
                  <option value="client_asc">Cliente</option>
                </select>
                <Link to="/incidents/new" className="inline-flex rounded-md border border-slate-900 px-4 py-2.5 text-sm font-medium text-slate-900 transition hover:bg-slate-900 hover:text-white">
                  Nueva incidencia
                </Link>
              </div>
            }
          >
            {loading ? (
              <LoadingState lines={6} />
            ) : (
              <DataTable
                columns={columns}
                rows={filteredIncidents}
                rowKey="id"
                emptyTitle="Sin incidencias visibles"
                emptyDescription="No hay incidencias disponibles para tu perfil o la búsqueda actual no ha devuelto resultados."
              />
            )}
          </SectionCard>
        </section>
      </main>
    </>
  );
}
