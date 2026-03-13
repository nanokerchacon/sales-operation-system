from __future__ import annotations

import csv
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INDEX_CSV = PROJECT_ROOT / "reconstruction_lab" / "notes" / "document_index.csv"
OUTPUT_CSV = PROJECT_ROOT / "reconstruction_lab" / "notes" / "document_links.csv"

OUTPUT_COLUMNS = [
    "order_reference",
    "order_document_number",
    "delivery_reference",
    "delivery_document_number",
    "invoice_reference",
    "invoice_document_number",
    "client_name",
    "operational_status",
    "document_status",
    "confidence",
    "matching_rule",
    "notes",
]

CLIENT_STOPWORDS = {
    "SA",
    "SL",
    "S",
    "L",
    "SLL",
    "SLU",
    "SAS",
    "SARL",
    "LTD",
    "LIMITED",
    "GMBH",
    "AB",
    "AG",
    "BV",
    "NV",
    "SPA",
    "AS",
    "OY",
    "OYJ",
    "INC",
    "CORP",
    "CORPORATION",
    "COMPANY",
    "CO",
    "THE",
    "DE",
    "DEL",
    "LA",
    "LAS",
    "LOS",
    "Y",
    "I",
}
REFERENCE_PATTERN = re.compile(r"\b(\d{2}S?)[\s_-]{1,2}(\d{1,4})\b", re.IGNORECASE)


@dataclass(frozen=True)
class DocumentRow:
    document_type: str
    document_number: str
    client_name: str
    client_key: str
    client_tokens: tuple[str, ...]
    document_date: date | None
    source_root: str
    source_folder: str
    relative_path: str
    extension: str
    order_references: tuple[str, ...]
    reference_keys: tuple[str, ...]
    delivery_reference: str
    invoice_type: str
    invoice_status_hint: str


@dataclass
class LogicalDocument:
    document_type: str
    document_number: str
    client_name: str
    client_key: str
    client_tokens: tuple[str, ...]
    document_date: date | None
    source_folder: str
    relative_paths: list[str]
    order_references: tuple[str, ...]
    reference_keys: tuple[str, ...]
    delivery_reference: str
    invoice_type: str
    invoice_status_hint: str


@dataclass
class CandidateMatch:
    document: LogicalDocument
    confidence: str
    rule: str
    score: int
    note: str


@dataclass
class MatchPlan:
    delivery_match: CandidateMatch | None
    invoice_match: CandidateMatch | None
    score: int
    ambiguous_reason: str


def normalize_ascii(value: str) -> str:
    value = unicodedata.normalize("NFKD", value or "")
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.upper()


def normalize_client(value: str) -> tuple[str, tuple[str, ...]]:
    normalized = normalize_ascii(value)
    normalized = normalized.replace("&", " ")
    normalized = re.sub(r"[^A-Z0-9]+", " ", normalized)
    tokens = [token for token in normalized.split() if token and token not in CLIENT_STOPWORDS]
    if not tokens:
        tokens = [token for token in normalized.split() if token]
    return " ".join(tokens), tuple(tokens)


def normalize_reference(value: str) -> str:
    candidate = normalize_ascii(value).strip()
    match = REFERENCE_PATTERN.search(candidate)
    if match:
        return f"{match.group(1).upper()}_{int(match.group(2))}"

    compact = re.sub(r"[^A-Z0-9]", "", candidate)
    compact_match = re.fullmatch(r"(\d{2}S?)(\d{1,4})", compact)
    if compact_match:
        return f"{compact_match.group(1).upper()}_{int(compact_match.group(2))}"
    return ""


def extract_reference_keys(*raw_values: str) -> tuple[str, ...]:
    references: list[str] = []
    for raw_value in raw_values:
        if not raw_value:
            continue
        direct = normalize_reference(raw_value)
        if direct and direct not in references:
            references.append(direct)
        normalized_text = normalize_ascii(raw_value)
        for match in REFERENCE_PATTERN.finditer(normalized_text):
            normalized = f"{match.group(1).upper()}_{int(match.group(2))}"
            if normalized not in references:
                references.append(normalized)
    return tuple(references)


def client_strength(left: tuple[str, ...], right: tuple[str, ...]) -> str | None:
    if not left or not right:
        return None
    if left == right:
        return "exact"

    left_set = set(left)
    right_set = set(right)
    common = left_set & right_set
    if not common:
        return None
    if len(common) >= 2 and (left_set <= right_set or right_set <= left_set):
        return "strong"
    if len(common) >= 2:
        return "medium"
    return None


def describe_client_strength(strength: str) -> str:
    return {
        "exact": "client_exact",
        "strong": "client_normalized_subset",
        "medium": "client_normalized_partial",
    }.get(strength, "client_unknown")


def parse_date(raw_value: str) -> date | None:
    raw_value = (raw_value or "").strip()
    if not raw_value:
        return None
    for fmt in ("%d-%m-%y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw_value, fmt).date()
        except ValueError:
            continue
    return None


def split_references(raw_value: str) -> tuple[str, ...]:
    references: list[str] = []
    for part in (raw_value or "").split(";"):
        normalized = normalize_reference(part)
        if normalized and normalized not in references:
            references.append(normalized)
    return tuple(references)


def load_index(path: Path) -> list[DocumentRow]:
    rows: list[DocumentRow] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            client_key, client_tokens = normalize_client(raw.get("client_name", ""))
            order_references = split_references(raw.get("order_reference", ""))
            reference_keys = extract_reference_keys(
                raw.get("order_reference", "") or "",
                raw.get("document_number", "") or "",
                raw.get("relative_path", "") or "",
                raw.get("file_name", "") or "",
            )
            rows.append(
                DocumentRow(
                    document_type=raw.get("document_type", ""),
                    document_number=(raw.get("document_number", "") or "").strip(),
                    client_name=(raw.get("client_name", "") or "").strip(),
                    client_key=client_key,
                    client_tokens=client_tokens,
                    document_date=parse_date(raw.get("document_date", "")),
                    source_root=(raw.get("source_root", "") or "").strip(),
                    source_folder=(raw.get("source_folder", "") or "").strip(),
                    relative_path=(raw.get("relative_path", "") or "").strip(),
                    extension=(raw.get("extension", "") or "").strip(),
                    order_references=order_references,
                    reference_keys=reference_keys,
                    delivery_reference=(raw.get("delivery_reference", "") or "").strip(),
                    invoice_type=(raw.get("invoice_type", "") or "").strip(),
                    invoice_status_hint=(raw.get("invoice_status_hint", "") or "").strip(),
                )
            )
    return rows


def aggregate_documents(rows: list[DocumentRow]) -> dict[str, list[LogicalDocument]]:
    buckets: dict[tuple[str, str, str, str, str, str, str], list[DocumentRow]] = defaultdict(list)
    for row in rows:
        primary_reference = row.reference_keys[0] if row.reference_keys else ""
        key = (
            row.document_type,
            row.document_number,
            row.client_key,
            row.document_date.isoformat() if row.document_date else "",
            row.source_folder,
            primary_reference,
            row.delivery_reference,
        )
        buckets[key].append(row)

    aggregated: dict[str, list[LogicalDocument]] = defaultdict(list)
    for group_rows in buckets.values():
        first = group_rows[0]
        aggregated[first.document_type].append(
            LogicalDocument(
                document_type=first.document_type,
                document_number=first.document_number,
                client_name=first.client_name,
                client_key=first.client_key,
                client_tokens=first.client_tokens,
                document_date=first.document_date,
                source_folder=first.source_folder,
                relative_paths=[row.relative_path for row in group_rows],
                order_references=first.order_references,
                reference_keys=first.reference_keys,
                delivery_reference=first.delivery_reference,
                invoice_type=first.invoice_type,
                invoice_status_hint=first.invoice_status_hint,
            )
        )
    return aggregated


def day_distance(later: date | None, earlier: date | None) -> int | None:
    if not later or not earlier:
        return None
    return (later - earlier).days


def choose_best_match(candidates: list[CandidateMatch], ambiguous_counter: Counter[str]) -> CandidateMatch | None:
    if not candidates:
        return None
    ranked = sorted(candidates, key=lambda item: (-item.score, item.document.document_number, item.document.client_name))
    best = ranked[0]
    if len(ranked) > 1 and ranked[1].score == best.score:
        ambiguous_counter[best.rule] += 1
        return None
    return best


def build_delivery_candidates(order_doc: LogicalDocument, deliveries_by_ref: dict[str, list[LogicalDocument]]) -> list[CandidateMatch]:
    candidates: list[CandidateMatch] = []
    if not order_doc.reference_keys:
        return candidates

    seen_documents: set[str] = set()
    for order_reference in order_doc.reference_keys:
        for delivery_doc in deliveries_by_ref.get(order_reference, []):
            delivery_key = f"{delivery_doc.document_number}|{delivery_doc.client_key}|{delivery_doc.document_date}"
            if delivery_key in seen_documents:
                continue
            seen_documents.add(delivery_key)

            strength = client_strength(order_doc.client_tokens, delivery_doc.client_tokens)
            if strength is None:
                continue

            distance = day_distance(delivery_doc.document_date, order_doc.document_date)
            if distance is not None and distance < -7:
                continue
            if distance is not None and distance > 120:
                continue

            if strength == "exact":
                confidence = "high"
                score = 100
                rule = "order_ref_normalized+client_exact"
            elif strength == "strong":
                confidence = "high"
                score = 93
                rule = "order_ref_normalized+client_subset"
            else:
                confidence = "medium"
                score = 80
                rule = "order_ref_normalized+client_partial"

            if len(delivery_doc.reference_keys) == 1:
                score += 3
            elif delivery_doc.reference_keys and order_reference == delivery_doc.reference_keys[0]:
                score += 1

            note_parts = [
                f"matched_ref={order_reference}",
                describe_client_strength(strength),
                f"delivery_files={len(delivery_doc.relative_paths)}",
            ]
            if distance is not None:
                note_parts.append(f"delivery_gap_days={distance}")
            if len(delivery_doc.reference_keys) > 1:
                note_parts.append(f"delivery_multi_refs={len(delivery_doc.reference_keys)}")

            candidates.append(
                CandidateMatch(
                    document=delivery_doc,
                    confidence=confidence,
                    rule=rule,
                    score=score,
                    note=",".join(note_parts),
                )
            )
    return candidates


def build_invoice_candidates(
    order_doc: LogicalDocument,
    delivery_match: CandidateMatch | None,
    invoices: list[LogicalDocument],
) -> list[CandidateMatch]:
    candidates: list[CandidateMatch] = []
    anchor_date = delivery_match.document.document_date if delivery_match else order_doc.document_date
    if anchor_date is None:
        return candidates

    for invoice_doc in invoices:
        strength = client_strength(order_doc.client_tokens, invoice_doc.client_tokens)
        if strength is None:
            continue

        invoice_gap = day_distance(invoice_doc.document_date, anchor_date)
        if invoice_gap is None:
            continue
        if invoice_gap < -10 or invoice_gap > 60:
            continue

        gap_score = max(0, 20 - abs(invoice_gap))
        if delivery_match and strength == "exact" and invoice_gap <= 35:
            confidence = "high"
            score = 90 + gap_score
            rule = "delivery_client_date_window_exact"
        elif delivery_match and strength in {"strong", "medium"} and invoice_gap <= 30:
            confidence = "medium"
            score = (76 if strength == "strong" else 68) + gap_score
            rule = "delivery_client_date_window_partial_ref"
        elif not delivery_match and strength == "exact" and invoice_gap <= 30:
            confidence = "low"
            score = 55 + gap_score
            rule = "order_client_date_window_exact"
        else:
            continue

        if invoice_doc.invoice_status_hint == "accepted":
            score += 2
        elif invoice_doc.invoice_status_hint == "pending_acceptance":
            score += 1

        note = ",".join(
            [
                describe_client_strength(strength),
                f"invoice_gap_days={invoice_gap}",
                f"invoice_files={len(invoice_doc.relative_paths)}",
                f"invoice_status={invoice_doc.invoice_status_hint or 'unknown'}",
            ]
        )
        candidates.append(
            CandidateMatch(
                document=invoice_doc,
                confidence=confidence,
                rule=rule,
                score=score,
                note=note,
            )
        )
    return candidates


def build_match_plan(
    order_doc: LogicalDocument,
    deliveries_by_ref: dict[str, list[LogicalDocument]],
    invoices: list[LogicalDocument],
    ambiguous_counter: Counter[str],
) -> MatchPlan:
    delivery_candidates = build_delivery_candidates(order_doc, deliveries_by_ref)
    plans: list[MatchPlan] = []

    invoice_without_delivery_candidates = build_invoice_candidates(order_doc, None, invoices)
    invoice_without_delivery = choose_best_match(invoice_without_delivery_candidates, ambiguous_counter)
    plans.append(
        MatchPlan(
            delivery_match=None,
            invoice_match=invoice_without_delivery,
            score=invoice_without_delivery.score if invoice_without_delivery else 0,
            ambiguous_reason="",
        )
    )

    for delivery_candidate in delivery_candidates:
        invoice_candidates = build_invoice_candidates(order_doc, delivery_candidate, invoices)
        invoice_match = choose_best_match(invoice_candidates, ambiguous_counter)
        plans.append(
            MatchPlan(
                delivery_match=delivery_candidate,
                invoice_match=invoice_match,
                score=delivery_candidate.score + (invoice_match.score if invoice_match else 0),
                ambiguous_reason="",
            )
        )

    ranked = sorted(
        plans,
        key=lambda item: (
            -item.score,
            -(item.delivery_match.score if item.delivery_match else 0),
            -(item.invoice_match.score if item.invoice_match else 0),
            item.delivery_match.document.document_number if item.delivery_match else "",
            item.invoice_match.document.document_number if item.invoice_match else "",
        ),
    )
    best = ranked[0]
    if len(ranked) > 1 and ranked[1].score == best.score:
        reason = "delivery" if (best.delivery_match is not None or ranked[1].delivery_match is not None) else "invoice"
        ambiguous_counter[f"plan_{reason}"] += 1
        return MatchPlan(None, None, 0, reason)
    return best


def derive_status(invoice_doc: LogicalDocument | None, has_delivery: bool) -> tuple[str, str]:
    operational_status = "delivered" if has_delivery else "confirmed"
    document_status = ""

    if invoice_doc:
        if invoice_doc.invoice_status_hint == "pending_acceptance":
            operational_status = "invoice_pending_acceptance"
            document_status = "pending_acceptance"
        else:
            operational_status = "invoiced"
            if invoice_doc.invoice_status_hint == "accepted":
                document_status = "accepted"
        if invoice_doc.invoice_type == "rectificative":
            document_status = "rectified_review"

    return operational_status, document_status


def write_output(rows: list[dict[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    if not INDEX_CSV.exists():
        print(f"No existe el índice documental: {INDEX_CSV}", file=sys.stderr)
        return 1

    document_rows = load_index(INDEX_CSV)
    aggregated = aggregate_documents(document_rows)

    orders = sorted(aggregated.get("order", []), key=lambda item: (item.order_references[0] if item.order_references else item.document_number, item.client_name))
    deliveries = aggregated.get("delivery", [])
    invoices = aggregated.get("invoice", [])

    deliveries_by_ref: dict[str, list[LogicalDocument]] = defaultdict(list)
    for delivery_doc in deliveries:
        for order_reference in delivery_doc.reference_keys:
            deliveries_by_ref[order_reference].append(delivery_doc)

    output_rows: list[dict[str, str]] = []
    rule_counter: Counter[str] = Counter()
    ambiguous_counter: Counter[str] = Counter()
    orders_without_delivery = 0
    orders_with_delivery = 0
    orders_with_accepted_invoice = 0
    orders_with_pending_invoice = 0

    for order_doc in orders:
        delivery_candidates = build_delivery_candidates(order_doc, deliveries_by_ref)
        invoice_without_delivery_candidates = build_invoice_candidates(order_doc, None, invoices)
        match_plan = build_match_plan(order_doc, deliveries_by_ref, invoices, ambiguous_counter)
        delivery_match = match_plan.delivery_match
        invoice_match = match_plan.invoice_match

        notes: list[str] = [f"order_files={len(order_doc.relative_paths)}"]
        matching_rules: list[str] = []
        confidence_rank = {"high": 3, "medium": 2, "low": 1, "": 0}
        confidence = ""

        if delivery_candidates and delivery_match is None:
            notes.append(f"ambiguous_delivery_candidates={len(delivery_candidates)}")
        if delivery_match:
            invoice_candidates = build_invoice_candidates(order_doc, delivery_match, invoices)
            if invoice_candidates and invoice_match is None:
                notes.append(f"ambiguous_invoice_candidates={len(invoice_candidates)}")
        elif invoice_without_delivery_candidates and invoice_match is None:
            notes.append(f"ambiguous_invoice_candidates={len(invoice_without_delivery_candidates)}")

        if match_plan.ambiguous_reason:
            notes.append(f"ambiguous_plan={match_plan.ambiguous_reason}")

        if delivery_match:
            orders_with_delivery += 1
            matching_rules.append(delivery_match.rule)
            rule_counter[delivery_match.rule] += 1
            notes.append(delivery_match.note)
            confidence = delivery_match.confidence
        else:
            orders_without_delivery += 1

        if invoice_match:
            matching_rules.append(invoice_match.rule)
            rule_counter[invoice_match.rule] += 1
            notes.append(invoice_match.note)
            if confidence_rank[invoice_match.confidence] > confidence_rank[confidence]:
                confidence = invoice_match.confidence
            elif confidence_rank[invoice_match.confidence] == confidence_rank[confidence]:
                confidence = invoice_match.confidence or confidence

            if invoice_match.document.invoice_status_hint == "accepted":
                orders_with_accepted_invoice += 1
            if invoice_match.document.invoice_status_hint == "pending_acceptance":
                orders_with_pending_invoice += 1

        operational_status, document_status = derive_status(
            invoice_match.document if invoice_match else None,
            has_delivery=delivery_match is not None,
        )

        order_reference = order_doc.order_references[0] if order_doc.order_references else ""
        client_name = order_doc.client_name or (delivery_match.document.client_name if delivery_match else "")
        output_rows.append(
            {
                "order_reference": order_reference,
                "order_document_number": order_doc.document_number,
                "delivery_reference": delivery_match.document.delivery_reference if delivery_match else "",
                "delivery_document_number": delivery_match.document.document_number if delivery_match else "",
                "invoice_reference": order_reference if invoice_match else "",
                "invoice_document_number": invoice_match.document.document_number if invoice_match else "",
                "client_name": client_name,
                "operational_status": operational_status,
                "document_status": document_status,
                "confidence": confidence,
                "matching_rule": " | ".join(matching_rules) if matching_rules else "order_only",
                "notes": " | ".join(notes),
            }
        )

    write_output(output_rows, OUTPUT_CSV)

    print(f"CSV generado en: {OUTPUT_CSV}")
    print(f"Pedidos sin albarán: {orders_without_delivery}")
    print(f"Pedidos con albarán: {orders_with_delivery}")
    print(f"Pedidos con factura aceptada: {orders_with_accepted_invoice}")
    print(f"Pedidos con factura pendiente de aceptación: {orders_with_pending_invoice}")
    print(f"Documentos ambiguos: {sum(ambiguous_counter.values())}")
    print("Top reglas de matching aplicadas:")
    if rule_counter:
        for rule, count in rule_counter.most_common(10):
            print(f"  {count:>4}  {rule}")
    else:
        print("  (sin matches)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
