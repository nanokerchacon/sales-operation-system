from __future__ import annotations

import csv
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LINKS_CSV = PROJECT_ROOT / "reconstruction_lab" / "notes" / "document_links.csv"
INDEX_CSV = PROJECT_ROOT / "reconstruction_lab" / "notes" / "document_index.csv"
OUTPUT_CSV = PROJECT_ROOT / "reconstruction_lab" / "notes" / "document_links_review.csv"

OUTPUT_COLUMNS = [
    "order_reference",
    "delivery_reference",
    "invoice_reference",
    "client_name",
    "confidence",
    "matching_rule",
    "notes",
    "reason_ambiguous",
    "suggested_match_1",
    "suggested_match_2",
    "manual_resolution",
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


@dataclass(frozen=True)
class IndexRow:
    document_type: str
    document_number: str
    client_name: str
    client_key: str
    client_tokens: tuple[str, ...]
    document_date: date | None
    order_references: tuple[str, ...]
    delivery_reference: str
    relative_path: str
    invoice_status_hint: str


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


def client_score(left: tuple[str, ...], right: tuple[str, ...]) -> int:
    if not left or not right:
        return 0
    if left == right:
        return 100
    common = set(left) & set(right)
    if not common:
        return 0
    if len(common) >= 2:
        return 75
    return 25


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


def split_refs(raw_value: str) -> tuple[str, ...]:
    values: list[str] = []
    for part in (raw_value or "").split(";"):
        cleaned = part.strip().upper()
        if cleaned and cleaned not in values:
            values.append(cleaned)
    return tuple(values)


def load_index_rows() -> tuple[list[IndexRow], dict[str, list[IndexRow]], dict[str, list[IndexRow]], dict[str, list[IndexRow]]]:
    rows: list[IndexRow] = []
    deliveries_by_order_ref: dict[str, list[IndexRow]] = defaultdict(list)
    orders_by_ref: dict[str, list[IndexRow]] = defaultdict(list)
    invoices_by_client: dict[str, list[IndexRow]] = defaultdict(list)

    with INDEX_CSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            client_key, client_tokens = normalize_client(raw.get("client_name", ""))
            row = IndexRow(
                document_type=(raw.get("document_type", "") or "").strip(),
                document_number=(raw.get("document_number", "") or "").strip(),
                client_name=(raw.get("client_name", "") or "").strip(),
                client_key=client_key,
                client_tokens=client_tokens,
                document_date=parse_date(raw.get("document_date", "")),
                order_references=split_refs(raw.get("order_reference", "")),
                delivery_reference=(raw.get("delivery_reference", "") or "").strip(),
                relative_path=(raw.get("relative_path", "") or "").strip(),
                invoice_status_hint=(raw.get("invoice_status_hint", "") or "").strip(),
            )
            rows.append(row)

            if row.document_type == "delivery":
                for ref in row.order_references:
                    deliveries_by_order_ref[ref].append(row)
            if row.document_type == "order":
                for ref in row.order_references:
                    orders_by_ref[ref].append(row)
            if row.document_type == "invoice" and row.client_key:
                invoices_by_client[row.client_key].append(row)

    return rows, deliveries_by_order_ref, orders_by_ref, invoices_by_client


def is_review_case(link_row: dict[str, str]) -> bool:
    confidence = (link_row.get("confidence", "") or "").strip().lower()
    notes = (link_row.get("notes", "") or "").lower()
    return confidence in {"low", "medium"} or "ambiguous_" in notes


def extract_reason(link_row: dict[str, str]) -> str:
    confidence = (link_row.get("confidence", "") or "").strip().lower()
    notes = (link_row.get("notes", "") or "")
    reasons: list[str] = []
    if confidence in {"low", "medium"}:
        reasons.append(f"confidence_{confidence}")
    delivery_match = re.search(r"ambiguous_delivery_candidates=(\d+)", notes)
    invoice_match = re.search(r"ambiguous_invoice_candidates=(\d+)", notes)
    if delivery_match:
        reasons.append(f"multiple_delivery_candidates:{delivery_match.group(1)}")
    if invoice_match:
        reasons.append(f"multiple_invoice_candidates:{invoice_match.group(1)}")
    return " | ".join(reasons) if reasons else "manual_review_requested"


def format_suggestion(prefix: str, row: IndexRow) -> str:
    date_text = row.document_date.isoformat() if row.document_date else "unknown_date"
    ref_text = row.delivery_reference or ";".join(row.order_references)
    return (
        f"{prefix}:{row.document_number or 'no_number'}"
        f" client={row.client_name or 'unknown'}"
        f" ref={ref_text or '-'}"
        f" date={date_text}"
        f" path={row.relative_path}"
    )


def pick_delivery_suggestions(
    order_reference: str,
    client_tokens: tuple[str, ...],
    deliveries_by_order_ref: dict[str, list[IndexRow]],
) -> list[str]:
    ranked: list[tuple[int, str]] = []
    seen: set[str] = set()
    for candidate in deliveries_by_order_ref.get(order_reference, []):
        score = client_score(client_tokens, candidate.client_tokens)
        suggestion = format_suggestion("delivery", candidate)
        if suggestion in seen:
            continue
        seen.add(suggestion)
        ranked.append((score, suggestion))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [item[1] for item in ranked[:2]]


def pick_invoice_suggestions(
    order_reference: str,
    client_key: str,
    client_tokens: tuple[str, ...],
    order_date: date | None,
    delivery_reference: str,
    invoices_by_client: dict[str, list[IndexRow]],
) -> list[str]:
    ranked: list[tuple[int, str]] = []
    seen: set[str] = set()
    for invoice in invoices_by_client.get(client_key, []):
        score = client_score(client_tokens, invoice.client_tokens)
        if order_date and invoice.document_date:
            score -= abs((invoice.document_date - order_date).days)
        if delivery_reference and invoice.invoice_status_hint:
            score += 5
        suggestion = format_suggestion("invoice", invoice)
        if order_reference and order_reference in suggestion:
            score += 10
        if suggestion in seen:
            continue
        seen.add(suggestion)
        ranked.append((score, suggestion))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [item[1] for item in ranked[:2]]


def main() -> int:
    rows, deliveries_by_order_ref, orders_by_ref, invoices_by_client = load_index_rows()
    _ = rows

    review_rows: list[dict[str, str]] = []
    with LINKS_CSV.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for link_row in reader:
            if not is_review_case(link_row):
                continue

            order_reference = (link_row.get("order_reference", "") or "").strip().upper()
            client_name = (link_row.get("client_name", "") or "").strip()
            client_key, client_tokens = normalize_client(client_name)
            order_rows = orders_by_ref.get(order_reference, [])
            order_date = order_rows[0].document_date if order_rows else None

            reason = extract_reason(link_row)
            suggestions: list[str] = []
            if "multiple_delivery_candidates" in reason or not link_row.get("delivery_reference", ""):
                suggestions.extend(pick_delivery_suggestions(order_reference, client_tokens, deliveries_by_order_ref))
            if "multiple_invoice_candidates" in reason or (link_row.get("confidence", "") or "").strip().lower() in {"low", "medium"}:
                suggestions.extend(
                    pick_invoice_suggestions(
                        order_reference,
                        client_key,
                        client_tokens,
                        order_date,
                        (link_row.get("delivery_reference", "") or "").strip(),
                        invoices_by_client,
                    )
                )

            review_rows.append(
                {
                    "order_reference": link_row.get("order_reference", "") or "",
                    "delivery_reference": link_row.get("delivery_reference", "") or "",
                    "invoice_reference": link_row.get("invoice_reference", "") or "",
                    "client_name": client_name,
                    "confidence": link_row.get("confidence", "") or "",
                    "matching_rule": link_row.get("matching_rule", "") or "",
                    "notes": link_row.get("notes", "") or "",
                    "reason_ambiguous": reason,
                    "suggested_match_1": suggestions[0] if len(suggestions) > 0 else "",
                    "suggested_match_2": suggestions[1] if len(suggestions) > 1 else "",
                    "manual_resolution": "",
                }
            )

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(review_rows)

    print(f"CSV generado en: {OUTPUT_CSV}")
    print(f"Casos para revision manual: {len(review_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
