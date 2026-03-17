export default function KpiCard({ title, value, detail, tone = "default" }) {
  const toneClasses = {
    default: "border-slate-200 bg-white",
    alert: "border-amber-200 bg-amber-50/60",
    success: "border-emerald-200 bg-emerald-50/60",
    muted: "border-slate-200 bg-slate-50/90",
  };

  return (
    <article className={`rounded-xl border p-5 shadow-panel transition-shadow hover:shadow-md ${toneClasses[tone] || toneClasses.default}`}>
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">{title}</p>
      <p className="mt-4 text-3xl font-semibold tracking-tight text-slate-950">{value}</p>
      <p className="mt-2 text-sm leading-6 text-slate-500">{detail}</p>
    </article>
  );
}
