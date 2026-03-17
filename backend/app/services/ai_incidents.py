import json
from typing import Any

import requests

from app.core.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.schemas.incident import IncidentDraftGenerateResponse

VALID_INCIDENT_TYPES = {"documental", "logistica", "facturacion"}
VALID_INCIDENT_PRIORITIES = {"baja", "media", "alta"}
DEFAULT_INCIDENT_TYPE = "documental"
DEFAULT_INCIDENT_PRIORITY = "media"
DEFAULT_INCIDENT_TITLE = "Nueva incidencia"
DEFAULT_INCIDENT_DESCRIPTION = "Pendiente de revisión a partir del texto facilitado por el usuario."
GENERIC_TITLE_VALUES = {"incidencia", "nueva incidencia", "incidente", "issue", "ticket"}
OLLAMA_TIMEOUT_SECONDS = 60

SYSTEM_PROMPT = """
Eres un asistente experto en gestión de incidencias empresariales.
Convierte texto libre en una incidencia estructurada.
Devuelve exclusivamente JSON válido con esta forma exacta:
{
  "title": "string",
  "description": "string",
  "type": "documental | logistica | facturacion",
  "priority": "baja | media | alta"
}
Reglas:
- title: corto, profesional y claro
- description: limpia, útil y profesional
- type: inferido según el contenido
- priority: inferida según urgencia real
- no inventar datos
- no devolver texto extra fuera del JSON
- si hay duda entre categorías, prioriza la clasificación más útil operativamente
""".strip()


class IncidentDraftGenerationError(RuntimeError):
    pass


class IncidentDraftConfigurationError(IncidentDraftGenerationError):
    pass


def _normalize_label(value: str | None) -> str:
    return (
        str(value or "")
        .strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )


def _clean_text(value: str | None) -> str:
    return " ".join(str(value or "").split()).strip()


def _truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return f"{value[: max_length - 3].rstrip()}..."


def _fallback_title(source_text: str) -> str:
    cleaned_source = _clean_text(source_text)
    if not cleaned_source:
        return DEFAULT_INCIDENT_TITLE

    first_segment = cleaned_source
    for separator in (".", "\n", "?", "!"):
        if separator in first_segment:
            first_segment = first_segment.split(separator, 1)[0]
    first_segment = _clean_text(first_segment)
    if not first_segment:
        return DEFAULT_INCIDENT_TITLE

    title = first_segment[:1].upper() + first_segment[1:]
    return _truncate(title, 60)


def _fallback_description(source_text: str) -> str:
    cleaned_source = _clean_text(source_text)
    if not cleaned_source:
        return DEFAULT_INCIDENT_DESCRIPTION

    if cleaned_source.endswith((".", "!", "?")):
        return cleaned_source
    return f"{cleaned_source}."


def infer_incident_type(source_text: str) -> str:
    normalized = _normalize_label(source_text)

    if any(keyword in normalized for keyword in ("factura", "abono", "cobro", "pago", "importe")):
        return "facturacion"
    if any(keyword in normalized for keyword in ("albaran", "entrega", "transportista", "envio", "pedido no llega", "retraso")):
        return "logistica"
    return "documental"


def infer_incident_priority(source_text: str) -> str:
    normalized = _normalize_label(source_text)

    if any(keyword in normalized for keyword in ("urgente", "muy urgente", "bloqueado", "hoy", "inmediato")):
        return "alta"
    if any(keyword in normalized for keyword in ("cuando puedas", "sin prisa", "informativo")):
        return "baja"
    return DEFAULT_INCIDENT_PRIORITY


def normalize_incident_type(value: str | None, source_text: str) -> str:
    normalized = _normalize_label(value)
    aliases = {
        "facturacion": "facturacion",
        "facturacion y cobro": "facturacion",
        "billing": "facturacion",
        "invoice": "facturacion",
        "documental": "documental",
        "documentacion": "documental",
        "documentacion cliente": "documental",
        "logistica": "logistica",
        "logistico": "logistica",
        "envio": "logistica",
        "transporte": "logistica",
    }

    if normalized in aliases:
        return aliases[normalized]
    if normalized in VALID_INCIDENT_TYPES:
        return normalized
    return infer_incident_type(source_text)


def normalize_incident_priority(value: Any, source_text: str) -> str:
    if isinstance(value, (int, float)):
        numeric_priority = int(value)
        if numeric_priority <= 1:
            return "baja"
        if numeric_priority == 2:
            return "media"
        return "alta"

    normalized = _normalize_label(value)
    aliases = {
        "1": "baja",
        "2": "media",
        "3": "alta",
        "baja": "baja",
        "low": "baja",
        "media": "media",
        "medium": "media",
        "alta": "alta",
        "high": "alta",
        "urgente": "alta",
    }

    if normalized in aliases:
        return aliases[normalized]
    if normalized in VALID_INCIDENT_PRIORITIES:
        return normalized
    return infer_incident_priority(source_text)


def extract_json_block(raw_response: str) -> str:
    text = str(raw_response or "").strip()
    if not text:
        raise IncidentDraftGenerationError("La respuesta del modelo llegó vacía.")

    if text.startswith("{") and text.endswith("}"):
        return text

    start_index = text.find("{")
    if start_index == -1:
        raise IncidentDraftGenerationError("La respuesta del modelo no contiene JSON.")

    depth = 0
    in_string = False
    escape = False

    for index in range(start_index, len(text)):
        char = text[index]

        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start_index:index + 1]

    raise IncidentDraftGenerationError("La respuesta del modelo contiene texto, pero no un bloque JSON válido.")


def parse_incident_draft(raw_response: str, source_text: str) -> IncidentDraftGenerateResponse:
    json_block = extract_json_block(raw_response)

    try:
        raw_data = json.loads(json_block)
    except json.JSONDecodeError as exc:
        raise IncidentDraftGenerationError("La respuesta del modelo no contiene un JSON válido.") from exc

    if not isinstance(raw_data, dict):
        raise IncidentDraftGenerationError("La respuesta del modelo debe ser un objeto JSON.")

    title = _clean_text(raw_data.get("title"))
    normalized_title = _truncate(title, 120) if title and _normalize_label(title) not in GENERIC_TITLE_VALUES else _fallback_title(source_text)

    description = _clean_text(raw_data.get("description"))
    normalized_description = description or _fallback_description(source_text)

    normalized_payload = {
        "title": normalized_title,
        "description": normalized_description,
        "type": normalize_incident_type(raw_data.get("type"), source_text),
        "priority": normalize_incident_priority(raw_data.get("priority"), source_text),
    }

    return IncidentDraftGenerateResponse(**normalized_payload)


def build_prompt(text: str) -> str:
    cleaned_text = _clean_text(text)
    if not cleaned_text:
        raise ValueError("El texto de entrada no puede estar vacío.")

    return f"{SYSTEM_PROMPT}\n\nTexto de entrada:\n{cleaned_text}"


def call_ollama(prompt: str) -> str:
    base_url = (OLLAMA_BASE_URL or "http://localhost:11434").rstrip("/")
    model = _clean_text(OLLAMA_MODEL) or "llama3.2"

    if not base_url:
        raise IncidentDraftConfigurationError("OLLAMA_BASE_URL is not configured.")
    if not model:
        raise IncidentDraftConfigurationError("OLLAMA_MODEL is not configured.")

    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        raise IncidentDraftGenerationError("No se pudo conectar con Ollama.") from exc

    if response.status_code >= 400:
        raise IncidentDraftGenerationError(f"Ollama devolvió un error HTTP {response.status_code}.")

    try:
        result = response.json()
    except ValueError as exc:
        raise IncidentDraftGenerationError("Ollama devolvió una respuesta JSON inválida.") from exc

    raw_response = result.get("response")
    if raw_response is None:
        raise IncidentDraftGenerationError("Ollama no devolvió el campo 'response' en la generación.")

    cleaned_response = str(raw_response).strip()
    if not cleaned_response:
        raise IncidentDraftGenerationError("Ollama devolvió un campo 'response' vacío.")

    return cleaned_response


def generate_incident_draft(text: str) -> IncidentDraftGenerateResponse:
    cleaned_text = _clean_text(text)
    if not cleaned_text:
        raise ValueError("El texto de entrada no puede estar vacío.")

    prompt = build_prompt(cleaned_text)
    raw_response = call_ollama(prompt)
    return parse_incident_draft(raw_response, cleaned_text)
