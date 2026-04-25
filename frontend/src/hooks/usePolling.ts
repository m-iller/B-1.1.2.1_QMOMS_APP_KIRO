import { useState, useEffect, useRef } from 'react'

interface UsePollingResult<T> {
  data: T | null
  error: Error | null
  loading: boolean
}

/**
 * Polls `fetchFn` every `intervalMs` milliseconds.
 *
 * @param fetchFn  Function to call on each tick. Updated via ref — no restart needed when it changes.
 * @param intervalMs  Polling interval in ms (default 7000).
 * @param options.enabled  Set false to pause polling.
 * @param options.deps  Extra dependencies that force a full restart + immediate fetch (e.g. [machineId]).
 */
export function usePolling<T>(
  fetchFn: () => Promise<T>,
  intervalMs: number = 7000,
  options?: { enabled?: boolean; deps?: unknown[] }
): UsePollingResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [loading, setLoading] = useState(true)
  const fetchRef = useRef(fetchFn)
  fetchRef.current = fetchFn

  const enabled = options?.enabled !== false
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const deps = options?.deps ?? []

  useEffect(() => {
    if (!enabled) return

    // Reset state when deps change (e.g. navigating to a different machine)
    setData(null)
    setLoading(true)
    setError(null)

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
    const timerId = setInterval(run, intervalMs)
    return () => {
      cancelled = true
      clearInterval(timerId)
    }
    // deps spread intentionally — restart polling when machine ID or other key values change
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, enabled, ...deps])

  return { data, error, loading }
}
