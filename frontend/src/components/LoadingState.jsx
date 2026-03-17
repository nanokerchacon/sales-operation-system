export default function LoadingState({ lines = 4, variant = "list", className = "" }) {
  if (variant === "cards") {
    return (
      <div className={`grid gap-5 md:grid-cols-2 xl:grid-cols-4 ${className}`.trim()}>
        {Array.from({ length: lines }).map((_, index) => (
          <div key={index} className="rounded-xl border border-slate-200 bg-white p-5 shadow-panel">
            <div className="h-3 w-28 animate-pulse rounded-full bg-slate-200" />
            <div className="mt-4 h-9 w-24 animate-pulse rounded-lg bg-slate-200" />
            <div className="mt-4 h-3 w-full animate-pulse rounded-full bg-slate-100" />
            <div className="mt-2 h-3 w-3/4 animate-pulse rounded-full bg-slate-100" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === "table") {
    return (
      <div className={`overflow-hidden rounded-xl border border-slate-200 bg-white ${className}`.trim()}>
        <div className="grid grid-cols-4 gap-4 border-b border-slate-200 bg-slate-50 px-4 py-3.5">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-3 animate-pulse rounded-full bg-slate-200" />
          ))}
        </div>
        <div className="divide-y divide-slate-100">
          {Array.from({ length: lines }).map((_, index) => (
            <div key={index} className="grid grid-cols-4 gap-4 px-4 py-4">
              {Array.from({ length: 4 }).map((__, cellIndex) => (
                <div key={cellIndex} className="h-3.5 animate-pulse rounded-full bg-slate-100" />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`.trim()}>
      {Array.from({ length: lines }).map((_, index) => (
        <div key={index} className="rounded-xl border border-slate-200 bg-white px-4 py-4 shadow-panel">
          <div className="h-3 w-1/3 animate-pulse rounded-full bg-slate-200" />
          <div className="mt-3 h-3 w-full animate-pulse rounded-full bg-slate-100" />
          <div className="mt-2 h-3 w-4/5 animate-pulse rounded-full bg-slate-100" />
        </div>
      ))}
    </div>
  );
}
