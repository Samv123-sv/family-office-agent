'use client'

import Link from 'next/link'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div className="min-h-screen bg-navy flex flex-col items-center justify-center gap-6">
      <p className="font-mono text-xs text-muted tracking-widest uppercase">Dashboard Error</p>
      <p className="font-sans text-sm text-muted max-w-sm text-center leading-6">{error.message}</p>
      <div className="flex items-center gap-4">
        <button
          onClick={reset}
          className="px-6 py-2 text-xs font-mono tracking-widest uppercase border border-line text-muted hover:border-white hover:text-white transition-colors"
        >
          Retry
        </button>
        <Link
          href="/"
          className="px-6 py-2 text-xs font-mono tracking-widest uppercase border border-amber text-amber hover:bg-amber hover:text-navy transition-colors"
        >
          Home
        </Link>
      </div>
    </div>
  )
}
