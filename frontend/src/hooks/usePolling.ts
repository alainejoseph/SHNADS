import { useState, useEffect, useCallback, useRef } from 'react';

interface UsePollingOptions {
  intervalMs?: number;
  enabled?: boolean;
}

export function usePolling<T>(
  fetcher: () => Promise<T>,
  options: UsePollingOptions = {}
) {
  const { intervalMs = 5000, enabled = true } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const refresh = useCallback(async () => {
    try {
      const result = await fetcherRef.current();
      setData(result);
      setError(null);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unknown error occurred while fetching data');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;

    let isMounted = true;
    refresh();

    const id = setInterval(() => {
      if (isMounted) {
        refresh();
      }
    }, intervalMs);

    return () => {
      isMounted = false;
      clearInterval(id);
    };
  }, [enabled, intervalMs, refresh]);

  return { data, loading, error, refresh };
}

