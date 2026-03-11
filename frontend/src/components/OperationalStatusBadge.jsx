import { translateStatus } from "../services/statusTranslation";

const STATUS_CLASSES = {
  ok: "border-emerald-200 bg-emerald-50 text-emerald-700",
  pending_delivery: "border-amber-200 bg-amber-50 text-amber-800",
  pending_invoice: "border-orange-200 bg-orange-50 text-orange-700",
  invoice_over_delivery: "border-red-200 bg-red-50 text-red-700",
};

export default function OperationalStatusBadge({ value }) {
  const label = translateStatus(value);
  const classes = STATUS_CLASSES[value] || "border-slate-200 bg-slate-50 text-slate-700";

  return <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${classes}`}>{label}</span>;
}
