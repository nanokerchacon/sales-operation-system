import EmptyState from "./EmptyState";
import LoadingState from "./LoadingState";

function getAlignmentClass(align) {
  if (align === "right") {
    return "text-right";
  }

  if (align === "center") {
    return "text-center";
  }

  return "text-left";
}

export default function DataTable({
  columns,
  rows,
  loading = false,
  emptyTitle = "Sin datos disponibles",
  emptyDescription = "No hay registros para mostrar en este momento.",
  emptyAction = null,
  rowKey = "id",
  compact = false,
}) {
  if (loading) {
    return <LoadingState lines={compact ? 4 : 6} variant="table" />;
  }

  if (!rows?.length) {
    return <EmptyState title={emptyTitle} description={emptyDescription} action={emptyAction} />;
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200">
      <table className="min-w-full divide-y divide-slate-200 bg-white">
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                className={[
                  "bg-slate-50 text-xs font-semibold uppercase tracking-[0.16em] text-slate-500",
                  compact ? "px-3 py-3" : "px-4 py-3.5",
                  getAlignmentClass(column.align),
                ].join(" ")}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {rows.map((row, index) => (
            <tr key={row[rowKey] ?? `${index}-${row.client_name ?? "row"}`} className="transition-colors hover:bg-slate-50/80">
              {columns.map((column) => (
                <td
                  key={column.key}
                  className={[
                    "align-middle text-sm text-slate-700",
                    compact ? "px-3 py-3.5" : "px-4 py-4",
                    getAlignmentClass(column.align),
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
