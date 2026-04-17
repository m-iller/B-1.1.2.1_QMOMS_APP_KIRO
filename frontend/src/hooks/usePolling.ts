import { useState, useEffect, useRef } from 'react'

interface UsePollingResult<T> {
  data: T | null
  error: Error | null
  loading: boolean
}

export function usePolling<T>(
  fetchFn: () => Promise<T>,
  intervalMs: number = 7000,
  options?: { enabled?: boolean }
): UsePollingResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [loading, setLoading] = useState(true)
  const fetchRef = useRef(fetchFn)
  fetchRef.current = fetchFn

  const enabled = options?.enabled !== false

  useEffect(() => {
    if (!enabled) return

    let cancelled = false

    const run = async () => {
      try {
        const result = await fetchRef.current()
        if (!cancelled) {
          setData(result)
          setError(null)
          setLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)))
          setLoading(false)
        }
      }
    }

    run()
    const id = setInterval(run, intervalMs)
    return () => {
      cancelled = true
      clearInterval(id)
    }
  }, [intervalMs, enabled])

  return { data, error, loading }
}
