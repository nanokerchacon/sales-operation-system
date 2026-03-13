import { translateStatus } from "../services/statusTranslation";

const STATUS_CLASSES = {
  ok: "border-emerald-200 bg-emerald-50 text-emerald-700",
  pending_delivery: "border-amber-200 bg-amber-50 text-amber-800",
  pending_invoice: "border-orange-200 bg-orange-50 text-orange-700",
  invoice_pending_acceptance: "border-sky-200 bg-sky-50 text-sky-700",
  invoice_over_delivery: "border-red-200 bg-red-50 text-red-700",
  not_invoiced: "border-slate-200 bg-slate-50 text-slate-700",
  invoice_issued: "border-indigo-200 bg-indigo-50 text-indigo-700",
  invoice_accepted: "border-emerald-200 bg-emerald-50 text-emerald-700",
  accepted: "border-emerald-200 bg-emerald-50 text-emerald-700",
  pending_acceptance: "border-sky-200 bg-sky-50 text-sky-700",
  rectified_review: "border-rose-200 bg-rose-50 text-rose-700",
};

export default function OperationalStatusBadge({ value }) {
  const label = translateStatus(value);
  const classes = STATUS_CLASSES[value] || "border-slate-200 bg-slate-50 text-slate-700";

  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${classes}`}>{label}</span>;
}
