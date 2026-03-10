export default function SectionCard({ title, subtitle, action, children, className = "" }) {
  return (
    <section className={`rounded-md border border-slate-200 bg-white shadow-panel ${className}`}>
      <div className="flex items-start justify-between border-b border-slate-200 px-6 py-5">
        <div>
          <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
          {subtitle ? <p className="mt-1 text-sm text-slate-500">{subtitle}</p> : null}
        </div>
        {action ? <div>{action}</div> : null}
      </div>
      <div className="p-6">{children}</div>
    </section>
  );
}
