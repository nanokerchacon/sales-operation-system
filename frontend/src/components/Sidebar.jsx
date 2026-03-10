import { navigationItems } from "../utils/mappers";

function GridIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <rect x="2.5" y="2.5" width="5" height="5" rx="1.2" stroke="currentColor" strokeWidth="1.4" />
      <rect x="12.5" y="2.5" width="5" height="5" rx="1.2" stroke="currentColor" strokeWidth="1.4" />
      <rect x="2.5" y="12.5" width="5" height="5" rx="1.2" stroke="currentColor" strokeWidth="1.4" />
      <rect x="12.5" y="12.5" width="5" height="5" rx="1.2" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  );
}

export default function Sidebar() {
  return (
    <aside className="flex min-h-screen w-[272px] flex-col border-r border-slate-800 bg-slate-950 text-slate-100">
      <div className="border-b border-slate-800 px-6 py-6">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-md border border-slate-800 bg-slate-900">
            <img
              src="/logo/logo-icono-white-removebg.png"
              alt="Nanoker ERP"
              className="h-14 w-14 object-contain"
            />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-slate-400">Nanoker ERP</p>
            <h1 className="mt-1 text-lg font-semibold text-white">Sales Operations</h1>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-4 py-6">
        <p className="px-3 text-[11px] font-semibold uppercase tracking-[0.26em] text-slate-500">
          Navegación
        </p>
        <ul className="mt-4 space-y-1.5">
          {navigationItems.map((item) => (
            <li key={item.key}>
              <button
                type="button"
                className={[
                  "flex w-full items-center gap-3 rounded-md px-3 py-3 text-left text-sm font-medium transition-colors",
                  item.active
                    ? "bg-slate-900 text-white shadow-soft"
                    : "text-slate-400 hover:bg-slate-900/70 hover:text-slate-100",
                ].join(" ")}
              >
                <span
                  className={[
                    "flex h-9 w-9 items-center justify-center rounded-md border",
                    item.active
                      ? "border-slate-700 bg-slate-800 text-slate-100"
                      : "border-slate-800 bg-slate-900 text-slate-500",
                  ].join(" ")}
                >
                  <GridIcon />
                </span>
                <span className="flex-1">{item.label}</span>
                {item.active ? <span className="h-2 w-2 rounded-full bg-slate-300" /> : null}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <div className="border-t border-slate-800 px-6 py-5">
        <div className="rounded-md border border-slate-800 bg-slate-900/70 px-4 py-4">
          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Estado del sistema</p>
          <p className="mt-2 text-sm font-semibold text-slate-100">Panel operativo en línea</p>
          <p className="mt-1 text-sm text-slate-400">Visibilidad ejecutiva sobre pedidos, facturación y riesgo.</p>
        </div>
      </div>
    </aside>
  );
}
