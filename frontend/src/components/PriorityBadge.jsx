import { getPriorityTone } from "../utils/mappers";
import { translateStatus } from "../services/statusTranslation";

const PRIORITY_CLASSES = {
  low: "border-slate-300 bg-slate-100 text-slate-700",
  medium: "border-amber-200 bg-amber-50 text-amber-800",
  high: "border-red-200 bg-red-50 text-red-700",
  critical: "border-rose-300 bg-rose-100 text-rose-800",
};

export default function PriorityBadge({ value }) {
  const tone = getPriorityTone(value);
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${PRIORITY_CLASSES[tone]}`}>
      {translateStatus(value)}
    </span>
  );
}
