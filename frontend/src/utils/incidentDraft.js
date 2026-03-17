const TYPE_RULES = [
  {
    type: "facturacion",
    keywords: ["factura", "abono", "cobro", "pago", "importe"],
  },
  {
    type: "logistica",
    keywords: ["albaran", "entrega", "transportista", "envio", "pedido no llega", "retraso"],
  },
  {
    type: "documental",
    keywords: ["certificado", "documento", "ficha", "adjunto", "pdf", "factura no localizada"],
  },
];

const HIGH_PRIORITY_KEYWORDS = ["urgente", "muy urgente", "bloqueado", "hoy", "inmediato"];
const LOW_PRIORITY_KEYWORDS = ["cuando puedas", "sin prisa", "informativo"];

const TITLE_PATTERNS = [
  { pattern: /factura no localizada|no encuentra la factura|factura no encontrada/, title: "Factura no localizada" },
  { pattern: /reenvi\w*\s+el?\s+albaran|reenvi\w*\s+de\s+albaran/, title: "Solicitud de reenvío de albarán" },
  { pattern: /pedido no ha llegado|pedido no llega|retraso|entrega/, title: "Retraso en entrega de pedido" },
  { pattern: /certificado/, title: "Solicitud de certificado" },
  { pattern: /documento|adjunto|pdf|ficha/, title: "Solicitud de documentación" },
  { pattern: /cobro|pago|abono|importe/, title: "Consulta sobre facturación" },
];

const TYPE_FALLBACK_TITLES = {
  facturacion: "Incidencia de facturación",
  logistica: "Incidencia logística",
  documental: "Gestión documental pendiente",
  comercial: "Consulta comercial",
  cobro: "Consulta de cobro",
  producto: "Incidencia de producto",
  otro: "Nueva incidencia",
};

function normalizeText(value) {
  return (value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function cleanupSpacing(value) {
  return (value || "").replace(/\s+/g, " ").trim();
}

function toSentenceCase(value) {
  const text = cleanupSpacing(value);
  if (!text) {
    return "";
  }

  return text.charAt(0).toUpperCase() + text.slice(1);
}

function limitLength(value, maxLength) {
  if (value.length <= maxLength) {
    return value;
  }

  return `${value.slice(0, maxLength - 3).trim()}...`;
}

function splitIntoSentences(value) {
  return String(value || "")
    .replace(/\r/g, "\n")
    .split(/[.!?\n]+/)
    .map((sentence) => cleanupSpacing(sentence))
    .filter(Boolean);
}

export function inferIncidentType(freeText) {
  const normalizedText = normalizeText(freeText);

  for (const rule of TYPE_RULES) {
    if (rule.keywords.some((keyword) => normalizedText.includes(keyword))) {
      return rule.type;
    }
  }

  return "documental";
}

export function inferIncidentPriority(freeText) {
  const normalizedText = normalizeText(freeText);

  if (HIGH_PRIORITY_KEYWORDS.some((keyword) => normalizedText.includes(keyword))) {
    return "alta";
  }

  if (LOW_PRIORITY_KEYWORDS.some((keyword) => normalizedText.includes(keyword))) {
    return "baja";
  }

  return "media";
}

export function buildIncidentTitle(freeText, type) {
  const normalizedText = normalizeText(freeText);

  for (const { pattern, title } of TITLE_PATTERNS) {
    if (pattern.test(normalizedText)) {
      return limitLength(title, 60);
    }
  }

  const firstSentence = splitIntoSentences(freeText)[0];
  if (firstSentence) {
    return limitLength(toSentenceCase(firstSentence), 60);
  }

  return TYPE_FALLBACK_TITLES[type] || "Nueva incidencia";
}

export function buildIncidentDescription(freeText) {
  const sentences = splitIntoSentences(freeText);

  if (sentences.length === 0) {
    return "";
  }

  const description = sentences
    .slice(0, 2)
    .map((sentence) => `${toSentenceCase(sentence)}.`)
    .join(" ");

  return cleanupSpacing(description);
}

export function generateIncidentDraft(freeText) {
  const cleanedText = cleanupSpacing(freeText);
  const type = inferIncidentType(cleanedText);

  return {
    title: buildIncidentTitle(cleanedText, type),
    description: buildIncidentDescription(cleanedText),
    type,
    priority: inferIncidentPriority(cleanedText),
  };
}
