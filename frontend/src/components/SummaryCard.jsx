export default function SummaryCard({ title, value, detail }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-5 shadow-panel transition-shadow hover:shadow-md">
      <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">{title}</p>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{value}</p>
      {detail ? <p className="mt-2 text-sm leading-6 text-slate-500">{detail}</p> : null}
    </article>
  );
}
