'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="min-h-screen bg-navy flex flex-col items-center justify-center gap-6">
      <p className="font-mono text-xs text-muted tracking-widest uppercase">Unexpected Error</p>
      <p className="font-sans text-sm text-muted max-w-sm text-center leading-6">{error.message}</p>
      <button
        onClick={reset}
        className="px-6 py-2 text-xs font-mono font-semibold tracking-widest uppercase border border-line text-muted hover:border-white hover:text-white transition-colors"
      >
        Try Again
      </button>
    </div>
  )
}
