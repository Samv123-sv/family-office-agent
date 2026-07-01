export default function DashboardLoading() {
  return (
    <div className="min-h-screen bg-navy">
      {/* Header skeleton */}
      <header className="border-b border-line px-8 py-4 flex items-center justify-between">
        <div className="space-y-2">
          <div className="h-2.5 w-32 bg-surface animate-pulse" />
          <div className="h-5 w-48 bg-surface animate-pulse" />
        </div>
        <div className="h-8 w-28 bg-surface animate-pulse" />
      </header>

      {/* Filter bar skeleton */}
      <div className="border-b border-line px-8 py-3 flex items-center gap-6 bg-surface">
        <div className="h-8 w-32 bg-navy animate-pulse" />
        <div className="h-8 w-32 bg-navy animate-pulse" />
        <div className="h-8 w-48 bg-navy animate-pulse" />
        <div className="ml-auto flex gap-1">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-7 w-16 bg-navy animate-pulse" />
          ))}
        </div>
      </div>

      {/* Table skeleton */}
      <main className="px-8 py-6">
        <table className="w-full">
          <thead>
            <tr className="border-b border-line">
              {['Company', 'Sector', 'Stage', 'Score', 'Rec.', 'Source', 'Days'].map(h => (
                <th key={h} className="text-left py-2 pr-6">
                  <div className="h-2.5 w-12 bg-surface animate-pulse" />
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[...Array(8)].map((_, i) => (
              <tr key={i} className="border-b border-line">
                <td className="py-4 pr-6"><div className="h-4 w-36 bg-surface animate-pulse" /></td>
                <td className="py-4 pr-6"><div className="h-4 w-16 bg-surface animate-pulse" /></td>
                <td className="py-4 pr-6"><div className="h-4 w-16 bg-surface animate-pulse" /></td>
                <td className="py-4 pr-6"><div className="h-4 w-10 bg-surface animate-pulse" /></td>
                <td className="py-4 pr-6"><div className="h-4 w-20 bg-surface animate-pulse" /></td>
                <td className="py-4 pr-6"><div className="h-4 w-14 bg-surface animate-pulse" /></td>
                <td className="py-4"><div className="h-4 w-8 bg-surface animate-pulse" /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </main>
    </div>
  )
}
