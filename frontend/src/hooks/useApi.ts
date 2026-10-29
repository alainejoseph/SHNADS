import { useState, useCallback } from 'react';

export function useApi<T, P extends unknown[]>(apiFunc: (...args: P) => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const execute = useCallback(
    async (...args: P): Promise<T | null> => {
      setLoading(true);
      setError(null);
      try {
        const result = await apiFunc(...args);
        setData(result);
        return result;
      } catch (err: unknown) {
        const message =
          err instanceof Error
            ? err.message
            : 'An unexpected error occurred';
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    [apiFunc]
  );

  return { data, loading, error, execute };
}

