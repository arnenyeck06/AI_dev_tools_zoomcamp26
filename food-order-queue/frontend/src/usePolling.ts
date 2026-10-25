import { useEffect, useRef } from 'react'

// Calls `callback` now and then every `intervalMs`, until the component unmounts
// or `enabled` turns false.
export function usePolling(callback: () => void, intervalMs: number, enabled = true) {
  const latest = useRef(callback)
  useEffect(() => {
    latest.current = callback
  })

  useEffect(() => {
    if (!enabled) return
    latest.current()
    const timer = setInterval(() => latest.current(), intervalMs)
    return () => clearInterval(timer)
  }, [intervalMs, enabled])
}
