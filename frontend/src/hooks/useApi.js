import { useCallback, useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

function getToken() {
  return sessionStorage.getItem("access_token");
}

/**
 * Shared fetch hook used across all 12+ dashboard views.
 * Handles auth headers, loading/error state, and JSON parsing consistently
 * so individual views don't reimplement fetch boilerplate.
 */
export function useApi(path, { method = "GET", body, skip = false } = {}) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(!skip);

  const execute = useCallback(async (overrideBody) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
        },
        body: method !== "GET" ? JSON.stringify(overrideBody ?? body) : undefined,
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        throw new Error(errBody.error || `Request failed with ${res.status}`);
      }

      const json = await res.json();
      setData(json);
      return json;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [path, method, body]);

  useEffect(() => {
    if (!skip && method === "GET") {
      execute();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [path, skip]);

  return { data, error, loading, refetch: execute };
}
