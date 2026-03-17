export default function EmptyState({ title, description, action = null }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-gradient-to-br from-slate-50 to-white px-6 py-10 text-center shadow-sm">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-400">
        <span className="text-lg">•</span>
      </div>
      <p className="mt-4 text-base font-semibold text-slate-800">{title}</p>
      <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-slate-500">{description}</p>
      {action ? <div className="mt-5 flex justify-center">{action}</div> : null}
    </div>
  );
}
