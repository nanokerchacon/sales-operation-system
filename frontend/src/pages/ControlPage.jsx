import { useMemo } from "react";
import { useAuth } from "../auth/useAuth";
import Header from "../components/Header";
import SectionCard from "../components/SectionCard";
import SummaryCard from "../components/SummaryCard";
import { formatInteger } from "../utils/formatters";

function normalizeList(value) {
  return Array.isArray(value) ? value.filter(Boolean).map((item) => String(item)) : [];
}

function buildControlCards(user, roles, permissions) {
  return [
    {
      title: "Usuario actual",
      value: user?.full_name || user?.name || user?.email || "-",
      detail: "Sesion autenticada actualmente en el panel interno.",
    },
    {
      title: "Rol principal",
      value: user?.primary_role || roles[0] || "-",
      detail: "Rol que condiciona la navegacion y el acceso actual.",
    },
    {
      title: "Roles visibles",
      value: formatInteger(roles.length),
      detail: "Roles expuestos por la sesion autenticada.",
    },
    {
      title: "Permisos activos",
      value: formatInteger(permissions.length),
      detail: "Permisos disponibles para esta sesion protegida.",
    },
  ];
}

export default function ControlPage() {
  const { user } = useAuth();
  const roles = useMemo(() => normalizeList(user?.roles), [user?.roles]);
  const permissions = useMemo(() => normalizeList(user?.permissions), [user?.permissions]);
  const displayName = user?.full_name || user?.name || "-";
  const email = user?.email || "-";
  const primaryRole = user?.primary_role || roles[0] || "-";

  return (
    <>
      <Header title="Control" subtitle="Panel interno del sistema. Acceso restringido." />

      <main className="flex-1 px-8 py-8">
        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
          {buildControlCards(user, roles, permissions).map((card) => <SummaryCard key={card.title} {...card} />)}
        </section>

        <section className="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <SectionCard title="Usuario actual" subtitle="Informacion real de la sesion autenticada en el ERP.">
            <div className="grid gap-5 md:grid-cols-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Nombre</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{displayName}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Email</p>
                <p className="mt-2 text-lg font-semibold text-slate-900 break-all">{email}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Rol principal</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{primaryRole}</p>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Estado</p>
                <p className="mt-2 text-lg font-semibold text-slate-900">{user?.is_active ? "Activo" : "Sin dato"}</p>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Acceso interno" subtitle="Resumen tecnico de roles y permisos expuestos por la sesion actual.">
            <div className="grid gap-5 md:grid-cols-2">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Roles</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {roles.length ? roles.map((role) => (
                    <span key={role} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700">{role}</span>
                  )) : <p className="text-sm text-slate-500">Sin roles visibles en la sesion.</p>}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Permisos</p>
                <div className="mt-3 max-h-[260px] overflow-auto rounded-md border border-slate-200 bg-slate-50 p-3">
                  {permissions.length ? (
                    <div className="flex flex-wrap gap-2">
                      {permissions.map((permission) => (
                        <span key={permission} className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">{permission}</span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500">Sin permisos visibles en la sesion.</p>
                  )}
                </div>
              </div>
            </div>
          </SectionCard>
        </section>
      </main>
    </>
  );
}
