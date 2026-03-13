from __future__ import annotations

import csv
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "reconstruction_lab" / "data"
OUTPUT_CSV = PROJECT_ROOT / "reconstruction_lab" / "notes" / "document_index.csv"

SUPPORTED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv"}
CSV_COLUMNS = [
    "document_type",
    "source_root",
    "source_folder",
    "invoice_type",
    "invoice_status_hint",
    "client_name",
    "document_number",
    "order_reference",
    "delivery_reference",
    "document_date",
    "file_name",
    "relative_path",
    "extension",
]

ORDER_REFERENCE_PATTERN = re.compile(r"\b\d{2}S?_{1,2}\d{1,4}\b", re.IGNORECASE)
DATE_PATTERN = re.compile(r"\((\d{1,2}-\d{1,2}-\d{2,4})\)")
LEADING_NUMBER_PATTERN = re.compile(r"^\s*(\d{1,6})(?:\b|[-_ ])")
QUOTE_NUMBER_PATTERN = re.compile(r"\b(26\d{3}|25\d{3}|24\d{3})\b")
INVOICE_NUMBER_PATTERN = re.compile(r"\b(IC|N|EX|CI|FR)\s*(\d{1,4})\b", re.IGNORECASE)

ROOT_TYPE_MAP = {
    "pedidos": "order",
    "albaranes": "delivery",
    "facturas": "invoice",
    "ofertas": "quote",
}

INVOICE_RULES = {
    ("facturas", "IC 2026"): ("intracommunity", "accepted"),
    ("facturas", "N 2026"): ("national", "accepted"),
    ("facturas", "EX 2026"): ("export", "accepted"),
    ("facturas", "CI 2026"): ("commercial_invoice", "accepted"),
    ("facturas", "FACE"): ("electronic", "pending_acceptance"),
    ("facturas", "FACEemit"): ("electronic", "pending_acceptance"),
    ("facturas", "FR 2026"): ("rectificative", "rectified_review"),
}


@dataclass(frozen=True)
class IndexedDocument:
    document_type: str
    source_root: str
    source_folder: str
    invoice_type: str
    invoice_status_hint: str
    client_name: str
    document_number: str
    order_reference: str
    delivery_reference: str
    document_date: str
    file_name: str
    relative_path: str
    extension: str

    def as_row(self) -> dict[str, str]:
        return {column: getattr(self, column) for column in CSV_COLUMNS}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "")
    normalized = normalized.replace("_", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def normalize_counter_key(value: str) -> str:
    if not value:
        return ""
    ascii_value = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(ch for ch in ascii_value if not unicodedata.combining(ch))
    ascii_value = ascii_value.upper()
    ascii_value = re.sub(r"\s+", " ", ascii_value)
    return ascii_value.strip(" -_;,")


def iter_documents(data_root: Path) -> Iterable[Path]:
    for path in sorted(data_root.rglob("*")):
        if path.is_file():
            yield path


def detect_document_type(relative_parts: tuple[str, ...], file_name: str) -> str:
    if not relative_parts:
        return "unknown"

    source_root = relative_parts[0].lower()
    if source_root in ROOT_TYPE_MAP:
        return ROOT_TYPE_MAP[source_root]

    lowered_name = file_name.lower()
    if "factura" in lowered_name:
        return "invoice"
    if "albar" in lowered_name:
        return "delivery"
    if "pedido" in lowered_name:
        return "order"
    if "oferta" in lowered_name or "quote" in lowered_name:
        return "quote"
    return "unknown"


def extract_invoice_metadata(relative_parts: tuple[str, ...]) -> tuple[str, str]:
    if len(relative_parts) < 2:
        return "", ""
    return INVOICE_RULES.get((relative_parts[0], relative_parts[1]), ("", ""))


def extract_date(raw_text: str) -> str:
    match = DATE_PATTERN.search(raw_text)
    return match.group(1) if match else ""


def extract_invoice_number(file_stem: str) -> str:
    match = INVOICE_NUMBER_PATTERN.search(file_stem)
    if not match:
        return ""
    return f"{match.group(1).upper()} {match.group(2)}"


def extract_delivery_reference(file_stem: str) -> str:
    match = LEADING_NUMBER_PATTERN.match(file_stem)
    return match.group(1) if match else ""


def extract_order_reference(raw_text: str) -> str:
    sanitized = DATE_PATTERN.sub(" ", raw_text)
    sanitized = re.sub(r"\b\d{1,2}-\d{1,2}-\d{2,4}\b", " ", sanitized)
    matches = ORDER_REFERENCE_PATTERN.findall(sanitized)
    seen: list[str] = []
    for match in matches:
        normalized = match.upper()
        if normalized not in seen:
            seen.append(normalized)
    return "; ".join(seen)


def extract_quote_number(file_stem: str, relative_parts: tuple[str, ...]) -> str:
    for candidate in [file_stem, *relative_parts[1:]]:
        match = QUOTE_NUMBER_PATTERN.search(candidate)
        if match:
            return match.group(1)
    return ""


def extract_order_number(file_stem: str) -> str:
    match = re.match(r"^\s*([0-9]{2}S?[_-]+[0-9]{1,4}|[0-9]{2}S__\d{1,4})\b", file_stem, re.IGNORECASE)
    if match:
        return match.group(1).replace("-", "_")
    return ""


def cleanup_client_name(value: str) -> str:
    cleaned = normalize_text(value)
    cleaned = re.sub(r"\([^)]*\)", "", cleaned)
    cleaned = re.sub(r"\b(?:pdf|xlsx|xls|csv|msg|jpg|jpeg|png)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^[\s\-_;,]+|[\s\-_;,]+$", "", cleaned)
    return cleaned


def extract_client_for_invoice(file_stem: str, document_number: str, document_date: str) -> str:
    candidate = file_stem
    if document_number:
        candidate = re.sub(rf"^\s*{re.escape(document_number)}\s*", "", candidate, flags=re.IGNORECASE)
    if document_date:
        candidate = candidate.replace(f"({document_date})", "")
    return cleanup_client_name(candidate)


def extract_client_for_order(file_stem: str, relative_parts: tuple[str, ...]) -> str:
    if len(relative_parts) > 2 and relative_parts[1].upper() == "STOCK":
        return "STOCK"

    candidate = file_stem
    candidate = re.sub(r"^\s*[0-9]{2}S?[_-]+[0-9]{1,4}\b", "", candidate, flags=re.IGNORECASE)
    parts = [segment.strip() for segment in candidate.split("-") if segment.strip()]
    if parts:
        return cleanup_client_name(parts[-1])
    return ""


def extract_client_for_delivery(file_stem: str) -> str:
    candidate = re.sub(r"^\s*\d+\s*[- ]\s*", "", file_stem)
    candidate = re.sub(r"\([^)]*\)", "", candidate)
    candidate = ORDER_REFERENCE_PATTERN.sub("", candidate)
    candidate = re.sub(r"\bpara\s+FR\s+\d+\b", "", candidate, flags=re.IGNORECASE)
    return cleanup_client_name(candidate)


def extract_client_for_quote(relative_parts: tuple[str, ...], file_stem: str, document_number: str) -> str:
    if len(relative_parts) > 1:
        root_client = cleanup_client_name(relative_parts[1])
        if root_client:
            return root_client

    candidate = file_stem
    if document_number:
        candidate = re.sub(rf"\b{re.escape(document_number)}\b", "", candidate)
    parts = [segment.strip() for segment in candidate.split("-") if segment.strip()]
    if parts:
        return cleanup_client_name(parts[-1])
    return ""


def build_document(path: Path) -> IndexedDocument:
    relative_path = path.relative_to(DATA_ROOT)
    relative_parts = relative_path.parts
    file_name = path.name
    file_stem = path.stem
    source_root = relative_parts[0] if relative_parts else ""
    source_folder = path.parent.name if path.parent != DATA_ROOT else source_root
    extension = path.suffix.lower()
    document_type = detect_document_type(relative_parts, file_name)
    invoice_type, invoice_status_hint = extract_invoice_metadata(relative_parts)
    document_date = extract_date(file_stem)

    document_number = ""
    order_reference = ""
    delivery_reference = ""
    client_name = ""

    if document_type == "invoice":
        document_number = extract_invoice_number(file_stem)
        client_name = extract_client_for_invoice(file_stem, document_number, document_date)
    elif document_type == "delivery":
        document_number = extract_delivery_reference(file_stem)
        delivery_reference = document_number
        order_reference = extract_order_reference(file_stem)
        client_name = extract_client_for_delivery(file_stem)
    elif document_type == "order":
        document_number = extract_order_number(file_stem)
        order_reference = document_number
        client_name = extract_client_for_order(file_stem, relative_parts)
    elif document_type == "quote":
        document_number = extract_quote_number(file_stem, relative_parts)
        client_name = extract_client_for_quote(relative_parts, file_stem, document_number)
        order_reference = extract_order_reference(file_stem)
    else:
        order_reference = extract_order_reference(file_stem)

    return IndexedDocument(
        document_type=document_type,
        source_root=source_root,
        source_folder=source_folder,
        invoice_type=invoice_type,
        invoice_status_hint=invoice_status_hint,
        client_name=client_name,
        document_number=document_number,
        order_reference=order_reference,
        delivery_reference=delivery_reference,
        document_date=document_date,
        file_name=file_name,
        relative_path=relative_path.as_posix(),
        extension=extension,
    )


def write_csv(documents: list[IndexedDocument], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for document in documents:
            writer.writerow(document.as_row())


def print_top(title: str, counter: Counter[str], limit: int = 20) -> None:
    print(title)
    if not counter:
        print("  (sin datos)")
        return
    for value, count in counter.most_common(limit):
        print(f"  {count:>4}  {value}")


def summarize(documents: list[IndexedDocument]) -> None:
    by_type = Counter(document.document_type for document in documents)
    client_counter = Counter()
    order_counter = Counter()

    for document in documents:
        client_key = normalize_counter_key(document.client_name)
        if client_key:
            client_counter[client_key] += 1

        if document.order_reference:
            for reference in [part.strip() for part in document.order_reference.split(";") if part.strip()]:
                order_counter[reference] += 1

    supported_count = sum(1 for document in documents if document.extension in SUPPORTED_EXTENSIONS)

    print(f"CSV generado en: {OUTPUT_CSV}")
    print(f"Total de documentos: {len(documents)}")
    print(f"Documentos soportados (.pdf/.xlsx/.xls/.csv): {supported_count}")
    print(f"Pedidos detectados: {by_type['order']}")
    print(f"Albaranes detectados: {by_type['delivery']}")
    print(f"Facturas detectadas: {by_type['invoice']}")
    print(f"Ofertas detectadas: {by_type['quote']}")
    print(f"Desconocidos: {by_type['unknown']}")
    print_top("Top 20 clientes detectados:", client_counter, limit=20)
    print_top("Top 20 referencias de pedido detectadas:", order_counter, limit=20)


def main() -> int:
    if not DATA_ROOT.exists():
        print(f"No existe la carpeta de datos: {DATA_ROOT}", file=sys.stderr)
        return 1

    documents = [build_document(path) for path in iter_documents(DATA_ROOT)]
    write_csv(documents, OUTPUT_CSV)
    summarize(documents)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
