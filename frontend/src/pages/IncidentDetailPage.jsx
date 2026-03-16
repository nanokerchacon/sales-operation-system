import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAuth } from "../auth/useAuth";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import IncidentTypeBadge from "../components/IncidentTypeBadge";
import LoadingState from "../components/LoadingState";
import OperationalStatusBadge from "../components/OperationalStatusBadge";
import PriorityBadge from "../components/PriorityBadge";
import SectionCard from "../components/SectionCard";
import SummaryCard from "../components/SummaryCard";
import { incidentsApi } from "../services/incidentsApi";
import { formatDate } from "../utils/formatters";
import { useAsyncData } from "../utils/useAsyncData";

const STATUS_OPTIONS = ["abierta", "en_proceso", "resuelta", "cerrada"];
const PRIORITY_OPTIONS = ["baja", "media", "alta", "critica"];

function buildSummaryCards(incident) {
  if (!incident) {
    return [];
  }

  return [
    { title: "Tipo", value: <IncidentTypeBadge value={incident.type} />, detail: "Clasificación funcional de la incidencia." },
    { title: "Estado", value: <OperationalStatusBadge value={incident.status} />, detail: "Situación operativa actual." },
    { title: "Prioridad", value: <PriorityBadge value={incident.priority} />, detail: "Nivel de urgencia para el equipo." },
    { title: "Resolución", value: incident.resolved_at ? formatDate(incident.resolved_at) : "Pendiente", detail: "Fecha de resolución si ya existe." },
  ];
}

export default function IncidentDetailPage() {
  const { user } = useAuth();
  const { incidentId } = useParams();
  const { data: incident, loading, error } = useAsyncData(() => incidentsApi.getById(incidentId), [incidentId]);
  const [incidentState, setIncidentState] = useState(null);
  const [form, setForm] = useState({ status: "abierta", priority: "media", resolution_notes: "" });
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState("");

  const canUpdate = user?.permissions?.includes("incidents.update");
  const currentIncident = incidentState || incident;

  useEffect(() => {
    if (!incident) {
      return;
    }
    setIncidentState(incident);
    setForm({
      status: incident.status,
      priority: incident.priority,
      resolution_notes: incident.resolution_notes || "",
    });
  }, [incident]);

  async function handleUpdate(event) {
    event.preventDefault();
    setSaving(true);
    setSaveError("");
    setSaveSuccess("");
    try {
      const updated = await incidentsApi.update(incidentId, {
        status: form.status,
        priority: form.priority,
        resolution_notes: form.resolution_notes,
        resolved_at: ["resuelta", "cerrada"].includes(form.status) ? new Date().toISOString() : null,
      });
      setIncidentState(updated);
      setForm({
        status: updated.status,
        priority: updated.priority,
        resolution_notes: updated.resolution_notes || "",
      });
      setSaveSuccess("Incidencia actualizada correctamente.");
    } catch (updateError) {
      setSaveError(updateError instanceof Error ? updateError.message : "No se pudo actualizar la incidencia.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <Header title={loading ? "Incidencia" : `Incidencia · ${currentIncident?.incident_number || ""}`} subtitle="Detalle operativo de la incidencia con contexto documental y actualización mínima de resolución." />

      <main className="flex-1 px-8 py-8">
        {error ? <ErrorState title="No se pudo cargar la incidencia." message={error} /> : null}
        {saveError ? <ErrorState title="No se pudo actualizar la incidencia." message={saveError} /> : null}

        <div className="mb-6 flex flex-wrap items-center gap-3 text-sm text-slate-500">
          <Link to="/incidents" className="font-medium text-slate-700 hover:text-slate-900">Incidencias</Link>
          <span>/</span>
          <span>{currentIncident?.incident_number || `Incidencia ${incidentId}`}</span>
          {currentIncident ? (
            <>
              <span>/</span>
              <Link to={`/clients/${currentIncident.client_id}`} className="font-medium text-slate-700 hover:text-slate-900">{currentIncident.client_name}</Link>
            </>
          ) : null}
        </div>

        <SectionCard
          title="Cabecera de incidencia"
          subtitle="Cliente, documentos relacionados y contexto principal para gestión diaria."
          action={
            currentIncident ? (
              <div className="flex flex-col items-end gap-2">
                <Link to={`/clients/${currentIncident.client_id}`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">Abrir cliente</Link>
                {currentIncident.order_id ? <Link to={`/orders/${currentIncident.order_id}`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">Abrir pedido</Link> : null}
                {currentIncident.delivery_id ? <Link to={`/deliveries/${currentIncident.delivery_id}`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">Abrir albarán</Link> : null}
                {currentIncident.invoice_id ? <Link to={`/invoices/${currentIncident.invoice_id}`} className="text-sm font-medium text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">Abrir factura</Link> : null}
              </div>
            ) : null
          }
        >
          {loading ? (
            <LoadingState lines={6} />
          ) : currentIncident ? (
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Número</p><p className="mt-2 text-lg font-semibold text-slate-900">{currentIncident.incident_number}</p></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Cliente</p><Link to={`/clients/${currentIncident.client_id}`} className="mt-2 inline-block text-lg font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{currentIncident.client_name}</Link></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Tipo</p><div className="mt-2"><IncidentTypeBadge value={currentIncident.type} /></div></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Estado</p><div className="mt-2"><OperationalStatusBadge value={currentIncident.status} /></div></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Prioridad</p><div className="mt-2"><PriorityBadge value={currentIncident.priority} /></div></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Creación</p><p className="mt-2 text-lg font-semibold text-slate-900">{formatDate(currentIncident.created_at)}</p></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Resolución</p><p className="mt-2 text-lg font-semibold text-slate-900">{formatDate(currentIncident.resolved_at)}</p></div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Pedido</p>{currentIncident.order_id ? <Link to={`/orders/${currentIncident.order_id}`} className="mt-2 inline-block text-sm font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{currentIncident.order_number}</Link> : <p className="mt-2 text-sm text-slate-900">-</p>}</div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Albarán</p>{currentIncident.delivery_id ? <Link to={`/deliveries/${currentIncident.delivery_id}`} className="mt-2 inline-block text-sm font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{currentIncident.delivery_number}</Link> : <p className="mt-2 text-sm text-slate-900">-</p>}</div>
              <div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Factura</p>{currentIncident.invoice_id ? <Link to={`/invoices/${currentIncident.invoice_id}`} className="mt-2 inline-block text-sm font-semibold text-slate-900 underline-offset-2 hover:text-slate-700 hover:underline">{currentIncident.invoice_number}</Link> : <p className="mt-2 text-sm text-slate-900">-</p>}</div>
            </div>
          ) : null}
        </SectionCard>

        <section className="mt-6 grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {loading
            ? Array.from({ length: 4 }).map((_, index) => <div key={index} className="h-[144px] animate-pulse rounded-md border border-slate-200 bg-white shadow-panel" />)
            : buildSummaryCards(currentIncident).map((card) => <SummaryCard key={card.title} {...card} />)}
        </section>

        <section className="mt-6 grid gap-6 xl:grid-cols-[1fr_0.95fr]">
          <div className="grid gap-6">
            <SectionCard title="Contenido" subtitle="Título y descripción del problema para entender impacto y contexto.">
              {loading ? <LoadingState lines={5} /> : currentIncident ? (
                <div className="grid gap-5">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Título</p>
                    <p className="mt-2 text-lg font-semibold text-slate-900">{currentIncident.title}</p>
                  </div>
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Descripción</p>
                    <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-900">{currentIncident.description}</p>
                  </div>
                </div>
              ) : null}
            </SectionCard>

            <SectionCard title="Relaciones" subtitle="Acceso rápido a cliente y documentos vinculados a la incidencia.">
              {loading ? <LoadingState lines={4} /> : currentIncident ? (
                <div className="grid gap-4 md:grid-cols-2">
                  <Link to={`/clients/${currentIncident.client_id}`} className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm font-semibold text-slate-900 hover:border-slate-300">Cliente · {currentIncident.client_name}</Link>
                  {currentIncident.order_id ? <Link to={`/orders/${currentIncident.order_id}`} className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm font-semibold text-slate-900 hover:border-slate-300">Pedido · {currentIncident.order_number}</Link> : <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">Sin pedido relacionado</div>}
                  {currentIncident.delivery_id ? <Link to={`/deliveries/${currentIncident.delivery_id}`} className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm font-semibold text-slate-900 hover:border-slate-300">Albarán · {currentIncident.delivery_number}</Link> : <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">Sin albarán relacionado</div>}
                  {currentIncident.invoice_id ? <Link to={`/invoices/${currentIncident.invoice_id}`} className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm font-semibold text-slate-900 hover:border-slate-300">Factura · {currentIncident.invoice_number}</Link> : <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">Sin factura relacionada</div>}
                </div>
              ) : null}
            </SectionCard>
          </div>

          <SectionCard title="Resolución" subtitle="Actualización mínima de estado, prioridad y notas de resolución para esta fase.">
            {loading ? <LoadingState lines={6} /> : currentIncident ? (
              canUpdate ? (
                <form onSubmit={handleUpdate} className="grid gap-5">
                  <label className="grid gap-2 text-sm text-slate-700">
                    <span className="font-medium">Estado</span>
                    <select value={form.status} onChange={(event) => setForm((current) => ({ ...current, status: event.target.value }))} className="rounded-md border border-slate-200 px-3 py-2.5 outline-none transition focus:border-slate-400">
                      {STATUS_OPTIONS.map((status) => <option key={status} value={status}>{status}</option>)}
                    </select>
                  </label>
                  <label className="grid gap-2 text-sm text-slate-700">
                    <span className="font-medium">Prioridad</span>
                    <select value={form.priority} onChange={(event) => setForm((current) => ({ ...current, priority: event.target.value }))} className="rounded-md border border-slate-200 px-3 py-2.5 outline-none transition focus:border-slate-400">
                      {PRIORITY_OPTIONS.map((priority) => <option key={priority} value={priority}>{priority}</option>)}
                    </select>
                  </label>
                  <label className="grid gap-2 text-sm text-slate-700">
                    <span className="font-medium">Notas de resolución</span>
                    <textarea value={form.resolution_notes} onChange={(event) => setForm((current) => ({ ...current, resolution_notes: event.target.value }))} rows={8} className="rounded-md border border-slate-200 px-3 py-2.5 outline-none transition focus:border-slate-400" placeholder="Describe acciones tomadas, acuerdos o siguiente paso previsto." />
                  </label>
                  {saveSuccess ? <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{saveSuccess}</p> : null}
                  <button type="submit" disabled={saving} className="inline-flex w-fit rounded-md border border-slate-900 px-4 py-2.5 text-sm font-medium text-slate-900 transition hover:bg-slate-900 hover:text-white disabled:cursor-not-allowed disabled:opacity-60">
                    {saving ? "Guardando..." : "Guardar actualización"}
                  </button>
                </form>
              ) : (
                <div className="grid gap-4">
                  <p className="text-sm leading-6 text-slate-700">No tienes permiso de actualización sobre incidencias en esta sesión.</p>
                  <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Notas actuales</p>
                    <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-900">{currentIncident.resolution_notes || "Sin notas de resolución registradas todavía."}</p>
                  </div>
                </div>
              )
            ) : null}
          </SectionCard>
        </section>
      </main>
    </>
  );
}
