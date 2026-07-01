'use client'

import { useEffect, useState } from 'react'

export function ErrorToast() {
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    const handler = (e: Event) => {
      const msg = (e as CustomEvent<string>).detail
      setMessage(msg)
      setTimeout(() => setMessage(null), 5000)
    }
    window.addEventListener('api-error', handler)
    return () => window.removeEventListener('api-error', handler)
  }, [])

  if (!message) return null

  return (
    <div
      role="alert"
      className="fixed bottom-6 right-6 z-50 bg-surface border border-line px-6 py-3 flex items-center gap-4 shadow-lg"
    >
      <span className="font-mono text-xs text-muted tracking-widest">ERROR</span>
      <span className="font-sans text-sm text-white">{message}</span>
      <button
        onClick={() => setMessage(null)}
        className="font-mono text-xs text-muted hover:text-white transition-colors ml-2"
        aria-label="Dismiss"
      >
        ✕
      </button>
    </div>
  )
}
