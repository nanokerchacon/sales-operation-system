import { translateStatus } from "../services/statusTranslation";

const TYPE_CLASSES = {
  comercial: "border-blue-200 bg-blue-50 text-blue-700",
  logistica: "border-cyan-200 bg-cyan-50 text-cyan-700",
  documental: "border-violet-200 bg-violet-50 text-violet-700",
  facturacion: "border-orange-200 bg-orange-50 text-orange-700",
  cobro: "border-amber-200 bg-amber-50 text-amber-800",
  producto: "border-emerald-200 bg-emerald-50 text-emerald-700",
  otro: "border-slate-200 bg-slate-50 text-slate-700",
};

export default function IncidentTypeBadge({ value }) {
  const classes = TYPE_CLASSES[value] || TYPE_CLASSES.otro;
  return <span className={`inline-flex min-w-[110px] items-center justify-center rounded-full border px-3 py-1 text-xs font-semibold ${classes}`}>{translateStatus(value)}</span>;
}
