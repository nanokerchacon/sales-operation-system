import { formatDateTime } from "../utils/formatters";

function IconButton({ children, label }) {
  return (
    <button
      type="button"
      aria-label={label}
      className="flex h-11 w-11 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:border-slate-300 hover:text-slate-900"
    >
      {children}
    </button>
  );
}

function BellIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M10 3.5a3 3 0 0 0-3 3v1.1c0 .84-.28 1.65-.8 2.32L5 11.5h10l-1.2-1.58A3.92 3.92 0 0 1 13 7.6V6.5a3 3 0 0 0-3-3Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M8.5 14.5a1.5 1.5 0 0 0 3 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

function SettingsIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M10 6.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" stroke="currentColor" strokeWidth="1.5" />
      <path d="M10 2.5v2M10 15.5v2M17.5 10h-2M4.5 10h-2M15.3 4.7l-1.4 1.4M6.1 13.9l-1.4 1.4M15.3 15.3l-1.4-1.4M6.1 6.1 4.7 4.7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export default function Header({ title, subtitle, lastUpdated }) {
  return (
    <header className="sticky top-0 z-10 border-b border-slate-200/80 bg-white/90 backdrop-blur">
      <div className="flex items-center justify-between px-8 py-5">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.26em] text-slate-500">Centro operativo</p>
          <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900">{title}</h2>
          <p className="mt-1 text-sm text-slate-500">
            {subtitle}
            {lastUpdated ? ` · Actualizado ${formatDateTime(lastUpdated)}` : ""}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <IconButton label="Notificaciones">
            <BellIcon />
          </IconButton>
          <IconButton label="Configuración">
            <SettingsIcon />
          </IconButton>
          <div className="flex items-center gap-3 rounded-md border border-slate-200 bg-white px-4 py-2.5 shadow-sm">
            <div className="flex h-11 w-11 items-center justify-center rounded-md bg-slate-900 text-sm font-semibold text-white">
              AC
            </div>
            <div className="text-left">
              <p className="text-sm font-semibold text-slate-900">Alvaro Chacon</p>
              <p className="text-xs text-slate-500">Soporte IT</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
