import { useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import SectionCard from "../components/SectionCard";
import { clientsApi } from "../services/clientsApi";
import { incidentsApi } from "../services/incidentsApi";
import { useAsyncData } from "../utils/useAsyncData";

const INCIDENT_TYPES = ["comercial", "logistica", "documental", "facturacion", "cobro", "producto", "otro"];
const INCIDENT_PRIORITIES = ["baja", "media", "alta", "critica"];

export default function IncidentNewPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const clientIdParam = searchParams.get("clientId") || "";
  const orderIdParam = searchParams.get("orderId") || "";
  const deliveryIdParam = searchParams.get("deliveryId") || "";
  const invoiceIdParam = searchParams.get("invoiceId") || "";

  const { data: clients = [], loading: clientsLoading, error: clientsError } = useAsyncData(clientsApi.list, []);

  const [form, setForm] = useState({
    client_id: clientIdParam,
    order_id: orderIdParam,
    delivery_id: deliveryIdParam,
    invoice_id: invoiceIdParam,
    type: searchParams.get("type") || "documental",
    priority: searchParams.get("priority") || "media",
    title: "",
    description: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");

  const selectedClient = useMemo(
    () => clients.find((client) => String(client.id) === String(form.client_id)),
    [clients, form.client_id],
  );

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setSubmitError("");

    try {
      const created = await incidentsApi.create({
        client_id: Number(form.client_id),
        order_id: form.order_id ? Number(form.order_id) : null,
        delivery_id: form.delivery_id ? Number(form.delivery_id) : null,
        invoice_id: form.invoice_id ? Number(form.invoice_id) : null,
        type: form.type,
        priority: form.priority,
        title: form.title,
        description: form.description,
      });
      navigate(`/incidents/${created.id}`);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "No se pudo crear la incidencia.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Header title="Nueva incidencia" subtitle="Alta operativa de incidencias vinculadas a cliente y documentos, con estructura preparada para seguimiento futuro." />

      <main className="flex-1 px-8 py-8">
        {clientsError ? <ErrorState title="No se pudo cargar el formulario." message={clientsError} /> : null}
        {submitError ? <ErrorState title="No se pudo crear la incidencia." message={submitError} /> : null}

        <div className="mb-6 flex flex-wrap items-center gap-3 text-sm text-slate-500">
          <Link to="/incidents" className="font-medium text-slate-700 hover:text-slate-900">Incidencias</Link>
          <span>/</span>
          <span>Nueva</span>
        </div>

        <SectionCard title="Formulario de incidencia" subtitle="Registro mínimo y robusto para identificar el problema, su prioridad y el documento afectado.">
          <form onSubmit={handleSubmit} className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <div className="grid gap-5">
              <div className="grid gap-5 md:grid-cols-2">
                <label className="grid gap-2 text-sm text-slate-700">
                  <span className="font-medium">Cliente</span>
                  <select
                    value={form.client_id}
                    onChange={(event) => setForm((current) => ({ ...current, client_id: event.target.value }))}
                    required
                    disabled={clientsLoading}
                    className="rounded-md border border-slate-200 px-3 py-2.5 outline-none transition focus:border-slate-400"
                  >
                    <option value="">Selecciona cliente</option>
                    {clients.map((client) => (
                      <option key={client.id} value={client.id}>{client.name}</option>
                    ))}
                  </select>
                </label>

                <label className="grid gap-2 text-sm text-slate-700">
                  <span className="font-medium">Tipo</span>
                  <select
                    value={form.type}
                    onChange={(event) => setForm((current) => ({ ...current, type: event.target.value }))}
                    className="rounded-md border border-slate-200 px-3 py-2.5 outline-none transition focus:border-slate-400"
                  >
                    {INCIDENT_TYPES.map((type) => <option key={type} value={type}>{type}</option>)}
                  </select>
                </label>

                <label className="grid gap-2 text-sm text-slate-700">
                  <span className="font-medium">Prioridad</span>
                  <select
                    value={form.priority}
                    onChange={(event) => setForm((current) => ({ ...current, priority: event.target.value }))}
                    className="rounded-md border border-slate-200 px-3 py-2.5 outline-none transition focus:border-slate-400"
                  >
                    {INCIDENT_PRIORITIES.map((priority) => <option key={priority} value={priority}>{priority}</option>)}
                  </select>
                </label>

                <div className="grid gap-2 text-sm text-slate-700">
                  <span className="font-medium">Contexto</span>
                  <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-600">
                    {selectedClient ? `Cliente seleccionado: ${selectedClient.name}` : "Puedes abrir el formulario desde cliente, pedido, albarán o factura para precargar contexto."}
                  </div>
                </div>
              </div>

              <label className="grid gap-2 text-sm text-slate-700">
                <span className="font-medium">Título</span>
                <input
                  type="text"
                  value={form.title}
                  onChange={(event) => setForm((current) => ({ ...current, title: event.target.value }))}
                  required
                  placeholder="Resumen claro de la incidencia"
                  className="rounded-md border border-slate-200 px-3 py-2.5 outline-none transition focus:border-slate-400"
                />
              </label>

              <label className="grid gap-2 text-sm text-slate-700">
                <span className="font-medium">Descripción</span>
                <textarea
                  value={form.description}
                  onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))}
                  required
                  rows={8}
                  placeholder="Describe el problema, su impacto y cualquier dato relevante para resolverlo."
                  className="rounded-md border border-slate-200 px-3 py-2.5 outline-none transition focus:border-slate-400"
                />
              </label>
            </div>

            <div className="grid gap-5">
              <div className="rounded-md border border-slate-200 bg-slate-50 p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Relaciones opcionales</p>
                <div className="mt-4 grid gap-4">
                  <label className="grid gap-2 text-sm text-slate-700">
                    <span className="font-medium">Pedido</span>
                    <input type="number" value={form.order_id} onChange={(event) => setForm((current) => ({ ...current, order_id: event.target.value }))} className="rounded-md border border-slate-200 px-3 py-2.5 outline-none transition focus:border-slate-400" />
                  </label>
                  <label className="grid gap-2 text-sm text-slate-700">
                    <span className="font-medium">Albarán</span>
                    <input type="number" value={form.delivery_id} onChange={(event) => setForm((current) => ({ ...current, delivery_id: event.target.value }))} className="rounded-md border border-slate-200 px-3 py-2.5 outline-none transition focus:border-slate-400" />
                  </label>
                  <label className="grid gap-2 text-sm text-slate-700">
                    <span className="font-medium">Factura</span>
                    <input type="number" value={form.invoice_id} onChange={(event) => setForm((current) => ({ ...current, invoice_id: event.target.value }))} className="rounded-md border border-slate-200 px-3 py-2.5 outline-none transition focus:border-slate-400" />
                  </label>
                </div>
              </div>

              <div className="rounded-md border border-dashed border-slate-300 bg-white p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Siguiente fase</p>
                <p className="mt-3 text-sm leading-6 text-slate-700">La incidencia queda preparada para añadir asignación, seguimiento, comentarios e histórico sin rehacer este formulario.</p>
              </div>

              <div className="flex flex-wrap gap-3">
                <button type="submit" disabled={submitting || clientsLoading} className="inline-flex rounded-md border border-slate-900 px-4 py-2.5 text-sm font-medium text-slate-900 transition hover:bg-slate-900 hover:text-white disabled:cursor-not-allowed disabled:opacity-60">
                  {submitting ? "Creando..." : "Crear incidencia"}
                </button>
                <Link to="/incidents" className="inline-flex rounded-md border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:text-slate-900">Cancelar</Link>
              </div>
            </div>
          </form>
        </SectionCard>
      </main>
    </>
  );
}
