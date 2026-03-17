export default function SectionCard({ title, subtitle, action, children, className = "" }) {
  return (
    <section className={`overflow-hidden rounded-xl border border-slate-200 bg-white shadow-panel ${className}`.trim()}>
      <div className="flex flex-col gap-4 border-b border-slate-200 px-6 py-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <h3 className="text-lg font-semibold tracking-tight text-slate-900">{title}</h3>
          {subtitle ? <p className="mt-1.5 max-w-3xl text-sm leading-6 text-slate-500">{subtitle}</p> : null}
        </div>
        {action ? <div className="shrink-0">{action}</div> : null}
      </div>
      <div className="p-6">{children}</div>
    </section>
  );
}
