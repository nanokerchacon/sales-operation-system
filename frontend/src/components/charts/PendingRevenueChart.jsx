import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { formatCurrency } from "../../utils/formatters";

const PIE_COLORS = ["#4f6b8a", "#c58b28", "#c66a1f", "#b42318"];

function buildChartData(summary) {
  return [
    { name: "0-3 dias", value: Number(summary.bucket0to3 || 0) },
    { name: "4-7 dias", value: Number(summary.bucket4to7 || 0) },
    { name: "8-15 dias", value: Number(summary.bucket8to15 || 0) },
    { name: "Mas de 15 dias", value: Number(summary.bucketOver15 || 0) },
  ].filter((item) => item.value > 0);
}

export default function PendingRevenueChart({ summary }) {
  const chartData = buildChartData(summary);
  const hasData = chartData.length > 0 && Number(summary.total || 0) > 0;

  if (!hasData) {
    return (
      <div className="flex h-[280px] items-center justify-center rounded-md border border-dashed border-slate-300 bg-slate-50 text-sm text-slate-500">
        No hay datos disponibles para visualizar.
      </div>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_170px] lg:items-center">
      <div className="h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              innerRadius={72}
              outerRadius={102}
              paddingAngle={2}
              stroke="#ffffff"
              strokeWidth={3}
            >
              {chartData.map((entry, index) => (
                <Cell key={entry.name} fill={PIE_COLORS[index]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => formatCurrency(value)}
              contentStyle={{
                borderRadius: "8px",
                border: "1px solid #cbd5e1",
                boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
              }}
            />
            <text x="50%" y="46%" textAnchor="middle" dominantBaseline="middle" fill="#64748b" fontSize="12">
              Total pendiente
            </text>
            <text x="50%" y="56%" textAnchor="middle" dominantBaseline="middle" fill="#0f172a" fontSize="18" fontWeight="600">
              {formatCurrency(summary.total)}
            </text>
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="space-y-3">
        {chartData.map((item, index) => (
          <div key={item.name} className="flex items-start gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-3">
            <span
              className="mt-1 h-3 w-3 rounded-full"
              style={{ backgroundColor: PIE_COLORS[index] }}
              aria-hidden="true"
            />
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-900">{item.name}</p>
              <p className="text-xs text-slate-500">{formatCurrency(item.value)}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
