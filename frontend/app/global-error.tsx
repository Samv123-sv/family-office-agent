'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html lang="en">
      <body style={{ background: '#0B1426', margin: 0, fontFamily: 'monospace' }}>
        <div
          style={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '1.5rem',
            color: '#8899AA',
          }}
        >
          <p style={{ fontSize: '0.75rem', letterSpacing: '0.1em', textTransform: 'uppercase' }}>
            Application Error
          </p>
          <p style={{ fontSize: '0.875rem', maxWidth: '24rem', textAlign: 'center' }}>
            {error.message}
          </p>
          <button
            onClick={reset}
            style={{
              padding: '0.5rem 1.5rem',
              fontSize: '0.75rem',
              letterSpacing: '0.1em',
              border: '1px solid #1E2D45',
              background: 'transparent',
              color: '#8899AA',
              cursor: 'pointer',
              textTransform: 'uppercase',
            }}
          >
            Reload
          </button>
        </div>
      </body>
    </html>
  )
}
