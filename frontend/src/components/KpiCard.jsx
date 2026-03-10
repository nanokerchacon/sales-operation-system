export default function KpiCard({ title, value, detail, tone = "default" }) {
  const toneClasses = {
    default: "border-slate-200 bg-white",
    alert: "border-amber-200 bg-amber-50/50",
    success: "border-emerald-200 bg-emerald-50/50",
    muted: "border-slate-200 bg-slate-50/80",
  };

  return (
    <article className={`rounded-md border p-5 shadow-panel ${toneClasses[tone] || toneClasses.default}`}>
      <p className="text-sm font-medium text-slate-500">{title}</p>
      <p className="mt-4 text-3xl font-semibold tracking-tight text-slate-900">{value}</p>
      <p className="mt-2 text-sm text-slate-500">{detail}</p>
    </article>
  );
}
