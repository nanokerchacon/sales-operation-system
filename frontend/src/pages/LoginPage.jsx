import { useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/useAuth";

export default function LoginPage() {
  const { login, isAuthenticated } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@local");
  const [password, setPassword] = useState("Local123!");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const redirectTo = location.state?.from?.pathname || "/dashboard";

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      await login(email, password);
      navigate(redirectTo, { replace: true });
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "No se pudo iniciar sesión.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[radial-gradient(circle_at_top,rgba(15,23,42,0.12),transparent_30%),linear-gradient(180deg,#f8fafc_0%,#e2e8f0_100%)] px-6 py-12">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl lg:grid-cols-[1.1fr_0.9fr]">
        <div className="hidden bg-slate-950 px-10 py-12 text-slate-100 lg:block">
          <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Nanoker ERP</p>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight">Control de acceso y navegación profesional.</h1>
          <p className="mt-4 max-w-md text-sm leading-7 text-slate-400">
            Esta primera fase activa autenticación real, roles base y menú adaptado al perfil sin romper el dashboard ni la operativa existente.
          </p>
          <div className="mt-10 rounded-xl border border-slate-800 bg-slate-900/70 p-5 text-sm text-slate-300">
            Usuarios locales de prueba disponibles tras ejecutar el seed de seguridad.
          </div>
        </div>

        <div className="px-8 py-10 sm:px-10">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500">Acceso seguro</p>
          <h2 className="mt-3 text-3xl font-semibold tracking-tight text-slate-900">Iniciar sesión</h2>
          <p className="mt-2 text-sm text-slate-500">Usa uno de los usuarios seed para entrar en el ERP.</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <label className="block">
              <span className="text-sm font-medium text-slate-700">Email</span>
              <input
                className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-slate-400"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="username"
                required
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">Contraseña</span>
              <input
                className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-slate-400"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                required
              />
            </label>

            {error ? <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-500"
            >
              {submitting ? "Accediendo..." : "Entrar"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
