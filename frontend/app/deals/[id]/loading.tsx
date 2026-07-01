export default function DealLoading() {
  return (
    <div className="min-h-screen bg-navy">
      {/* Header skeleton */}
      <header className="border-b border-line px-8 py-4">
        <div className="flex items-start justify-between">
          <div className="space-y-3">
            <div className="h-3 w-24 bg-surface animate-pulse" />
            <div className="h-7 w-56 bg-surface animate-pulse" />
            <div className="h-3 w-80 bg-surface animate-pulse" />
          </div>
          <div className="text-right space-y-2">
            <div className="h-10 w-14 bg-surface animate-pulse ml-auto" />
            <div className="h-5 w-24 bg-surface animate-pulse" />
          </div>
        </div>
      </header>

      <div className="flex divide-x divide-line">
        {/* Score sidebar skeleton */}
        <aside className="w-72 shrink-0 px-8 py-6 space-y-5">
          <div className="h-3 w-32 bg-surface animate-pulse" />
          {[...Array(4)].map((_, i) => (
            <div key={i} className="flex justify-between">
              <div className="h-4 w-24 bg-surface animate-pulse" />
              <div className="h-4 w-8 bg-surface animate-pulse" />
            </div>
          ))}
          <div className="border-t border-line pt-4 flex justify-between">
            <div className="h-4 w-10 bg-surface animate-pulse" />
            <div className="h-5 w-10 bg-surface animate-pulse" />
          </div>
          <div className="pt-6 border-t border-line space-y-2">
            <div className="h-3 w-28 bg-surface animate-pulse" />
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-3 w-full bg-surface animate-pulse" />
            ))}
          </div>
        </aside>

        {/* Memo skeleton */}
        <main className="flex-1 px-8 py-6">
          <div className="flex justify-between mb-6">
            <div className="h-3 w-32 bg-surface animate-pulse" />
            <div className="h-8 w-36 bg-surface animate-pulse" />
          </div>
          <div className="space-y-4 max-w-2xl">
            <div className="h-3 w-24 bg-surface animate-pulse" />
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-4 w-full bg-surface animate-pulse" />
            ))}
            <div className="h-3 w-24 bg-surface animate-pulse mt-8" />
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-4 bg-surface animate-pulse" style={{ width: `${85 - i * 5}%` }} />
            ))}
          </div>
        </main>
      </div>
    </div>
  )
}
