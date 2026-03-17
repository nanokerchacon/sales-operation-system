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
import { normalizeCollection } from "../utils/apiData";
import { formatDate, formatInteger } from "../utils/formatters";
import { useAsyncData } from "../utils/useAsyncData";

function normalizeIncidentRows(value) {
  return normalizeCollection(value).map((incident, index) => {
    const numericId = Number(incident?.id);
    const numericClientId = Number(incident?.client_id);
    const fallbackIdentifier = `INC-${String(index + 1).padStart(4, "0")}`;

    return {
      id: Number.isFinite(numericId) && numericId > 0 ? numericId : null,
      client_id: Number.isFinite(numericClientId) && numericClientId > 0 ? numericClientId : null,
      incident_number: String(incident?.incident_number || incident?.code || fallbackIdentifier),
      client_name: String(incident?.client_name || incident?.client?.name || "Cliente no disponible"),
      type: String(incident?.type || "documental"),
      status: String(incident?.status || "abierta"),
      priority: String(incident?.priority || "media"),
      title: String(incident?.title || "Incidencia sin titulo"),
      invoice_number: String(incident?.invoice_number || ""),
      delivery_number: String(incident?.delivery_number || ""),
      order_number: String(incident?.order_number || ""),
      created_at: incident?.created_at || incident?.updated_at || null,
      hasDetailRoute: Number.isFinite(numericId) && numericId > 0,
      hasClientRoute: Number.isFinite(numericClientId) && numericClientId > 0,
    };
  });
}

function buildKpis(incidents) {
  const total = incidents.length;
  const open = incidents.filter((incident) => ["abierta", "en_proceso"].includes(incident.status)).length;
  const resolved = incidents.filter((incident) => ["resuelta", "cerrada"].includes(incident.status)).length;
  const critical = incidents.filter((incident) => ["critica", "alta"].includes(incident.priority)).length;

  return [
    { title: "Incidencias visibles", value: formatInteger(total), detail: "Registros accesibles segun rol y cartera." },
    { title: "Abiertas o en proceso", value: formatInteger(open), detail: "Trabajo operativo pendiente de cierre." },
    { title: "Resueltas o cerradas", value: formatInteger(resolved), detail: "Incidencias ya estabilizadas." },
    { title: "Alta prioridad", value: formatInteger(critical), detail: "Casos que requieren atencion prioritaria." },
  ];
}

function resolveDocumentLabel(row) {
  if (row.invoice_number) {
    return `Factura ${row.invoice_number}`;
  }
  if (row.delivery_number) {
    return `Albaran ${row.delivery_number}`;
  }
  if (row.order_number) {
    return `Pedido ${row.order_number}`;
  }
  return "Sin documento vinculado";
}

export default function IncidentsPage() {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("date_desc");
  const { data: incidentsResponse, loading, error } = useAsyncData(incidentsApi.list, []);

  const incidents = useMemo(() => normalizeIncidentRows(incidentsResponse), [incidentsResponse]);

  const filteredIncidents = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    const baseRows = normalizedSearch
      ? incidents.filter((incident) =>
          [incident.incident_number, incident.client_name, incident.type, incident.status, incident.priority, incident.title]
            .filter(Boolean)
            .some((value) => String(value).toLowerCase().includes(normalizedSearch)),
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
        return String(left.client_name || "").localeCompare(String(right.client_name || ""), "es");
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
          {row.hasDetailRoute ? (
            <Link to={`/incidents/${row.id}`} className="font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
              {row.incident_number}
            </Link>
          ) : (
            <span className="font-semibold text-slate-900">{row.incident_number}</span>
          )}
          <p className="text-xs text-slate-500 line-clamp-1">{row.title}</p>
        </div>
      ),
    },
    {
      key: "client_name",
      header: "Cliente",
      render: (row) =>
        row.hasClientRoute ? (
          <Link to={`/clients/${row.client_id}`} className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
            {row.client_name}
          </Link>
        ) : (
          <span>{row.client_name}</span>
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
      align: "right",
      render: (row) => formatDate(row.created_at),
    },
    {
      key: "action",
      header: "Accion",
      render: (row) =>
        row.hasDetailRoute ? (
          <Link to={`/incidents/${row.id}`} className="font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">
            Abrir detalle
          </Link>
        ) : (
          <span className="text-slate-500">Detalle no disponible</span>
        ),
    },
  ];

  return (
    <>
      <Header title="Incidencias" subtitle="Gestion operativa, documental y comercial de incidencias vinculadas a clientes y documentos." />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState title="No se pudo cargar el modulo de incidencias." message={error} /> : null}

        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {loading ? (
            <LoadingState lines={4} variant="cards" className="md:col-span-2 xl:col-span-4" />
          ) : (
            buildKpis(incidents).map((card) => <SummaryCard key={card.title} {...card} />)
          )}
        </section>

        <section className="mt-6">
          <SectionCard
            title="Base de incidencias"
            subtitle="Consulta, prioriza y navega rapidamente entre casos documentales, logisticos y de facturacion."
            action={
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <input
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Buscar por cliente, incidencia, titulo o estado"
                  className="w-full min-w-[280px] rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                />
                <select
                  value={sort}
                  onChange={(event) => setSort(event.target.value)}
                  className="rounded-md border border-slate-200 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-slate-400"
                >
                  <option value="date_desc">Mas recientes</option>
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
            <DataTable
              columns={columns}
              rows={filteredIncidents}
              loading={loading}
              rowKey="id"
              emptyTitle="No hay incidencias todavia"
              emptyDescription="Cuando registres la primera incidencia o la busqueda tenga resultados, aparecera aqui con su prioridad y estado."
              emptyAction={<Link to="/incidents/new" className="inline-flex rounded-md border border-slate-900 px-4 py-2.5 text-sm font-medium text-slate-900 transition hover:bg-slate-900 hover:text-white">Nueva incidencia</Link>}
            />
          </SectionCard>
        </section>
      </main>
    </>
  );
}
