import { getRiskTone } from "../utils/mappers";

export default function RiskBadge({ value }) {
  const tone = getRiskTone(value);
  const toneClasses = {
    low: "border-slate-300 bg-slate-100 text-slate-700",
    medium: "border-amber-200 bg-amber-50 text-amber-800",
    high: "border-red-200 bg-red-50 text-red-700",
  };

  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${toneClasses[tone]}`}>
      {value}
    </span>
  );
}
