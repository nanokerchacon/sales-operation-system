import { useEffect, useState } from "react";

export function useAsyncData(loader, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isActive = true;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const response = await loader();
        if (!isActive) {
          return;
        }
        setData(response);
      } catch (requestError) {
        if (!isActive) {
          return;
        }
        setError(requestError instanceof Error ? requestError.message : "No se pudo cargar la información.");
      } finally {
        if (isActive) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      isActive = false;
    };
  }, deps);

  return { data, loading, error };
}
