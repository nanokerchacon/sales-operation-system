import EmptyState from "./EmptyState";
import LoadingState from "./LoadingState";

export default function DataTable({
  columns,
  rows,
  loading = false,
  emptyTitle = "Sin datos disponibles",
  emptyDescription = "No hay registros para mostrar en este momento.",
  rowKey = "id",
  compact = false,
}) {
  if (loading) {
    return <LoadingState lines={5} />;
  }

  if (!rows?.length) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200">
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={[
                  "bg-slate-50 text-left text-xs font-semibold uppercase tracking-[0.16em] text-slate-500",
                  compact ? "px-3 py-3" : "px-4 py-3.5",
                ].join(" ")}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row, index) => (
            <tr key={row[rowKey] ?? `${index}-${row.client_name ?? "row"}`} className="hover:bg-slate-50/80">
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={[
                    "align-middle text-sm text-slate-700",
                    compact ? "px-3 py-3.5" : "px-4 py-4",
                  ].join(" ")}
                >
                  {column.render ? column.render(row) : row[column.key] ?? "-"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
