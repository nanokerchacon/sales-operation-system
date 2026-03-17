import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/useAuth";

const navigationItems = [
  {
    key: "dashboard",
    label: "Dashboard",
    to: "/dashboard",
    permission: "dashboard.view",
    roles: ["direccion_general", "comercial", "finanzas", "admin"],
  },
  {
    key: "clients",
    label: "Clientes",
    to: "/clients",
    permission: "clients.view",
    roles: ["direccion_general", "comercial", "finanzas", "admin"],
  },
  {
    key: "orders",
    label: "Pedidos",
    to: "/orders",
    permission: "orders.view",
    roles: ["direccion_general", "comercial", "admin"],
  },
  {
    key: "deliveries",
    label: "Albaranes",
    to: "/deliveries",
    permission: "deliveries.view",
    roles: ["direccion_general", "comercial", "finanzas", "admin"],
  },
  {
    key: "invoices",
    label: "Facturas",
    to: "/invoices",
    permission: "invoices.view",
    roles: ["direccion_general", "comercial", "finanzas", "admin"],
  },
  {
    key: "incidents",
    label: "Incidencias",
    to: "/incidents",
    permission: "incidents.view",
    roles: ["direccion_general", "comercial", "finanzas", "admin"],
  },
  {
    key: "products",
    label: "Productos",
    to: "/products",
    permission: "products.view",
    roles: ["direccion_general", "comercial", "admin"],
  },
  {
    key: "control",
    label: "Control",
    to: "/control",
    permission: "admin.view",
    roles: ["direccion_general", "admin"],
  },
];

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
  const { user } = useAuth();
  const visibleItems = navigationItems.filter(
    (item) => user?.permissions?.includes(item.permission) && item.roles.includes(user?.primary_role),
  );

  return (
    <aside className="flex min-h-screen w-[272px] flex-col border-r border-slate-800 bg-slate-950 text-slate-100">
      <div className="border-b border-slate-800 px-6 py-6">
        <div className="flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl border border-slate-800 bg-slate-900 shadow-inner">
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
          Navegacion
        </p>
        <ul className="mt-4 space-y-1.5">
          {visibleItems.map((item) => (
            <li key={item.key}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  [
                    "group relative flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition-all duration-150",
                    isActive
                      ? "bg-slate-900 text-white shadow-soft ring-1 ring-slate-800"
                      : "text-slate-400 hover:bg-slate-900/70 hover:text-slate-100",
                  ].join(" ")
                }
              >
                {({ isActive }) => (
                  <>
                    <span className={["absolute left-0 top-2 bottom-2 w-1 rounded-r-full transition-opacity", isActive ? "bg-cyan-400 opacity-100" : "opacity-0 group-hover:opacity-40 bg-slate-500"].join(" ")} />
                    <span
                      className={[
                        "flex h-9 w-9 items-center justify-center rounded-lg border transition-colors",
                        isActive
                          ? "border-slate-700 bg-slate-800 text-slate-100"
                          : "border-slate-800 bg-slate-900 text-slate-500",
                      ].join(" ")}
                    >
                      <GridIcon />
                    </span>
                    <span className="flex-1">{item.label}</span>
                    {isActive ? <span className="h-2.5 w-2.5 rounded-full bg-cyan-300" /> : null}
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="border-t border-slate-800 px-6 py-5">
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 px-4 py-4">
          <p className="text-xs uppercase tracking-[0.22em] text-slate-500">Estado del sistema</p>
          <p className="mt-2 text-sm font-semibold text-slate-100">Sesion protegida activa</p>
          <p className="mt-1 text-sm leading-6 text-slate-400">Navegacion y acceso filtrados por rol y permisos.</p>
        </div>
      </div>
    </aside>
  );
}
