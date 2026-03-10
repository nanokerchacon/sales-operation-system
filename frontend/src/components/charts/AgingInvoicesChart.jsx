import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { formatCurrency } from "../../utils/formatters";

const BAR_COLORS = ["#4f6b8a", "#c58b28", "#c66a1f", "#b42318"];

function buildChartData(agingInvoices) {
  if (!agingInvoices) {
    return [];
  }

  return [
    { name: "0-3 días", value: Number(agingInvoices.bucket_0_3_days || 0) },
    { name: "4-7 días", value: Number(agingInvoices.bucket_4_7_days || 0) },
    { name: "8-15 días", value: Number(agingInvoices.bucket_8_15_days || 0) },
    { name: "Más de 15 días", value: Number(agingInvoices.bucket_over_15_days || 0) },
  ];
}

export default function AgingInvoicesChart({ agingInvoices }) {
  const chartData = buildChartData(agingInvoices);
  const hasData = chartData.some((item) => item.value > 0);

  if (!hasData) {
    return (
      <div className="flex h-[280px] items-center justify-center rounded-md border border-dashed border-slate-300 bg-slate-50 text-sm text-slate-500">
        No hay datos disponibles para visualizar.
      </div>
    );
  }

  return (
    <div className="h-[280px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} barGap={10}>
          <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="name"
            tickLine={false}
            axisLine={false}
            tick={{ fill: "#64748b", fontSize: 12 }}
          />
          <YAxis
            tickLine={false}
            axisLine={false}
            tick={{ fill: "#64748b", fontSize: 12 }}
            tickFormatter={(value) => formatCurrency(value)}
            width={95}
          />
          <Tooltip
            cursor={{ fill: "rgba(148, 163, 184, 0.08)" }}
            formatter={(value) => formatCurrency(value)}
            contentStyle={{
              borderRadius: "8px",
              border: "1px solid #cbd5e1",
              boxShadow: "0 8px 24px rgba(15, 23, 42, 0.08)",
            }}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={54}>
            {chartData.map((entry, index) => (
              <Cell key={entry.name} fill={BAR_COLORS[index]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
