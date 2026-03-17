import { useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import ErrorState from "../components/ErrorState";
import Header from "../components/Header";
import SectionCard from "../components/SectionCard";
import { clientsApi } from "../services/clientsApi";
import { incidentsApi } from "../services/incidentsApi";
import { generateIncidentDraft } from "../utils/incidentDraft";
import { useAsyncData } from "../utils/useAsyncData";

const INCIDENT_TYPES = ["comercial", "logistica", "documental", "facturacion", "cobro", "producto", "otro"];
const INCIDENT_PRIORITIES = ["baja", "media", "alta", "critica"];

function normalizeCollection(value) {
  if (Array.isArray(value)) {
    return value;
  }

  if (Array.isArray(value?.items)) {
    return value.items;
  }

  if (Array.isArray(value?.data)) {
    return value.data;
  }

  return [];
}

function getValidFormValue(value, allowedValues, fallback) {
  return allowedValues.includes(value) ? value : fallback;
}

function normalizeDraftResponse(value) {
  return {
    title: String(value?.title || ""),
    description: String(value?.description || ""),
    type: String(value?.type || ""),
    priority: String(value?.priority || ""),
  };
}

export default function IncidentNewPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const clientIdParam = searchParams.get("clientId") || "";
  const orderIdParam = searchParams.get("orderId") || "";
  const deliveryIdParam = searchParams.get("deliveryId") || "";
  const invoiceIdParam = searchParams.get("invoiceId") || "";
  const typeParam = searchParams.get("type") || "documental";
  const priorityParam = searchParams.get("priority") || "media";

  const { data: clientsResponse, loading: clientsLoading, error: clientsError } = useAsyncData(clientsApi.list, []);

  const clients = useMemo(() => normalizeCollection(clientsResponse), [clientsResponse]);

  const [form, setForm] = useState({
    client_id: clientIdParam,
    order_id: orderIdParam,
    delivery_id: deliveryIdParam,
    invoice_id: invoiceIdParam,
    type: getValidFormValue(typeParam, INCIDENT_TYPES, "documental"),
    priority: getValidFormValue(priorityParam, INCIDENT_PRIORITIES, "media"),
    title: "",
    description: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState("");
  const [draftPrompt, setDraftPrompt] = useState("");
  const [draftError, setDraftError] = useState("");
  const [draftLoading, setDraftLoading] = useState(false);
  const [draftNotice, setDraftNotice] = useState("");

  const selectedClient = useMemo(
    () => clients.find((client) => String(client?.id) === String(form.client_id)) || null,
    [clients, form.client_id],
  );

  function applyDraftToForm(draft) {
    const normalizedDraft = normalizeDraftResponse(draft);

    setForm((current) => ({
      ...current,
      title: normalizedDraft.title || current.title || "",
      description: normalizedDraft.description || current.description || "",
      type: getValidFormValue(normalizedDraft.type, INCIDENT_TYPES, current.type),
      priority: getValidFormValue(normalizedDraft.priority, INCIDENT_PRIORITIES, current.priority),
    }));
  }

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
        type: getValidFormValue(form.type, INCIDENT_TYPES, "documental"),
        priority: getValidFormValue(form.priority, INCIDENT_PRIORITIES, "media"),
        title: String(form.title || ""),
        description: String(form.description || ""),
      });
      navigate(`/incidents/${created.id}`);
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : "No se pudo crear la incidencia.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleGenerateDraft() {
    const prompt = draftPrompt.trim();

    if (!prompt) {
      setDraftError("Escribe una breve explicación de la incidencia para generar una propuesta.");
      setDraftNotice("");
      return;
    }

    setDraftLoading(true);
    setDraftError("");
    setDraftNotice("");

    try {
      const draft = await incidentsApi.generateDraft(prompt);
      applyDraftToForm(draft);
    } catch (error) {
      try {
        const fallbackDraft = generateIncidentDraft(prompt);
        applyDraftToForm(fallbackDraft);
        setDraftNotice("No se pudo usar la generación asistida. Se ha aplicado una propuesta local.");
      } catch (fallbackError) {
        setDraftError(
          fallbackError instanceof Error
            ? fallbackError.message
            : error instanceof Error
              ? error.message
              : "No se pudo generar la propuesta automáticamente.",
        );
      }
    } finally {
      setDraftLoading(false);
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
          <div className="mb-6 rounded-md border border-slate-200 bg-slate-50 p-5">
            <div className="flex flex-col gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Asistente de redacción</p>
                <p className="mt-2 text-sm leading-6 text-slate-700">Escribe la incidencia en lenguaje natural y te proponemos una versión estructurada.</p>
              </div>

              <label className="grid gap-2 text-sm text-slate-700">
                <span className="font-medium">Descripción libre</span>
                <textarea
                  value={draftPrompt}
                  onChange={(event) => {
                    setDraftPrompt(event.target.value);
                    if (draftError) {
                      setDraftError("");
                    }
                    if (draftNotice) {
                      setDraftNotice("");
                    }
                  }}
                  rows={4}
                  placeholder="Ejemplo: el cliente no encuentra la factura y la necesita hoy"
                  className="rounded-md border border-slate-200 bg-white px-3 py-2.5 outline-none transition focus:border-slate-400"
                />
              </label>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={handleGenerateDraft}
                  disabled={draftLoading}
                  className="inline-flex rounded-md border border-slate-900 px-4 py-2.5 text-sm font-medium text-slate-900 transition hover:bg-slate-900 hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {draftLoading ? "Generando..." : "Generar propuesta"}
                </button>
                <p className="text-sm text-slate-500">La propuesta rellena tipo, prioridad, título y descripción sin enviar la incidencia.</p>
              </div>

              {draftNotice ? <p className="rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-800">{draftNotice}</p> : null}
              {draftError ? <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">{draftError}</p> : null}
            </div>
          </div>

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
                      <option key={client?.id ?? client?.name ?? "client-option"} value={client?.id ?? ""}>{client?.name || "Cliente sin nombre"}</option>
                    ))}
                  </select>
                </label>

                <label className="grid gap-2 text-sm text-slate-700">
                  <span className="font-medium">Tipo</span>
                  <select
                    value={getValidFormValue(form.type, INCIDENT_TYPES, "documental")}
                    onChange={(event) => setForm((current) => ({ ...current, type: event.target.value }))}
                    className="rounded-md border border-slate-200 px-3 py-2.5 outline-none transition focus:border-slate-400"
                  >
                    {INCIDENT_TYPES.map((type) => <option key={type} value={type}>{type}</option>)}
                  </select>
                </label>

                <label className="grid gap-2 text-sm text-slate-700">
                  <span className="font-medium">Prioridad</span>
                  <select
                    value={getValidFormValue(form.priority, INCIDENT_PRIORITIES, "media")}
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
