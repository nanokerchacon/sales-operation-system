export default function ErrorState({ message }) {
  return (
    <div className="rounded-md border border-red-200 bg-red-50 p-6 text-sm text-red-700">
      <p className="font-semibold">No se pudo cargar el dashboard.</p>
      <p className="mt-2">{message || "Revisa la disponibilidad del backend y vuelve a intentarlo."}</p>
    </div>
  );
}
