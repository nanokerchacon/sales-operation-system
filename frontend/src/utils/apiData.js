export function normalizeCollection(value) {
  if (Array.isArray(value)) {
    return value;
  }

  if (Array.isArray(value?.items)) {
    return value.items;
  }

  if (Array.isArray(value?.data)) {
    return value.data;
  }

  if (Array.isArray(value?.results)) {
    return value.results;
  }

  return [];
}

export function normalizeObject(value, fallback = null) {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    if (value.data && typeof value.data === "object" && !Array.isArray(value.data)) {
      return value.data;
    }

    if (value.item && typeof value.item === "object" && !Array.isArray(value.item)) {
      return value.item;
    }

    return value;
  }

  return fallback;
}
