'use client'

import { use, useEffect, useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import Link from 'next/link'
import { apiFetch, apiUpload } from '@/lib/api'
import type { CompanyDetail, DocumentRecord, MemoResponse } from '@/lib/types'

const DIMENSION_LABELS: Record<string, string> = {
  thesis_fit: 'Thesis Fit',
  team_signals: 'Team Signals',
  market_timing: 'Market Timing',
  data_quality: 'Data Quality',
}

function scoreColor(score: number) {
  if (score >= 8) return 'text-amber'
  if (score >= 6) return 'text-white'
  return 'text-muted'
}

function recColor(rec: string | null) {
  if (rec === 'REACH_OUT') return 'text-amber border-amber'
  if (rec === 'WATCH') return 'text-white border-line'
  return 'text-muted border-line'
}

function formatMemo(content: string) {
  // Split into paragraphs, detect ALL-CAPS headers
  return content.split('\n').map((line, i) => {
    const trimmed = line.trim()
    if (!trimmed) return <br key={i} />
    const isHeader = /^[A-Z][A-Z\s\-:]{3,}$/.test(trimmed)
    if (isHeader) {
      return (
        <p key={i} className="font-sans font-semibold text-xs tracking-widest text-muted mt-8 mb-2 uppercase">
          {trimmed}
        </p>
      )
    }
    return (
      <p key={i} className="font-serif text-base leading-8 text-white mb-0">
        {trimmed}
      </p>
    )
  })
}

export default function DealPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { getToken } = useAuth()
  const [deal, setDeal] = useState<CompanyDetail | null>(null)
  const [memo, setMemo] = useState<MemoResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [generatingMemo, setGeneratingMemo] = useState(false)
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [memoError, setMemoError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      try {
        const [data, docs] = await Promise.all([
          apiFetch<CompanyDetail>(`/api/deals/${id}`, getToken),
          apiFetch<DocumentRecord[]>(`/api/documents?company_id=${id}`, getToken),
        ])
        setDeal(data)
        setDocuments(docs)
        if (data.memo) {
          setMemo({
            memo_id: data.memo.memo_id,
            company_id: id,
            client_id: data.client_id,
            content: data.memo.content,
            version: data.memo.version,
            generated_at: data.memo.generated_at,
            cached: true,
          })
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load deal')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id, getToken])

  const generateMemo = async () => {
    setGeneratingMemo(true)
    setMemoError(null)
    try {
      const result = await apiFetch<MemoResponse>(
        `/api/deals/${id}/memo`,
        getToken,
        { method: 'POST' },
      )
      setMemo(result)
    } catch (e) {
      setMemoError(e instanceof Error ? e.message : 'Failed to generate memo')
    } finally {
      setGeneratingMemo(false)
    }
  }

  const uploadDocument = async (file: File) => {
    setUploading(true)
    setUploadError(null)
    try {
      const form = new FormData()
      form.append('file', file)
      form.append('company_id', id)
      const doc = await apiUpload<DocumentRecord>('/api/documents', getToken, form)
      setDocuments(prev => [doc, ...prev])
    } catch (e) {
      setUploadError(e instanceof Error ? e.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-navy flex items-center justify-center">
        <p className="font-mono text-xs text-muted tracking-widest">LOADING...</p>
      </div>
    )
  }

  if (error || !deal) {
    return (
      <div className="min-h-screen bg-navy flex flex-col items-center justify-center gap-4">
        <p className="font-mono text-xs text-muted">{error ?? 'Deal not found'}</p>
        <Link href="/dashboard" className="font-mono text-xs text-amber hover:underline">← DASHBOARD</Link>
      </div>
    )
  }

  const score = deal.score

  return (
    <div className="min-h-screen bg-navy">
      {/* Header */}
      <header className="border-b border-line px-8 py-4">
        <div className="flex items-start justify-between">
          <div>
            <Link href="/dashboard" className="font-mono text-xs text-muted hover:text-white transition-colors">
              ← DASHBOARD
            </Link>
            <h1 className="text-2xl font-semibold text-white mt-2">{deal.name}</h1>
            <div className="flex items-center gap-4 mt-1 font-mono text-xs text-muted">
              <span>{deal.sector}</span>
              <span>·</span>
              <span>{deal.stage}</span>
              <span>·</span>
              <span>{deal.source}</span>
              <span>·</span>
              <a
                href={deal.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted hover:text-amber transition-colors"
              >
                SOURCE ↗
              </a>
            </div>
          </div>
          {score && (
            <div className="text-right">
              <p className={`font-mono text-4xl font-semibold ${scoreColor(score.total_score)}`}>
                {score.total_score.toFixed(1)}
              </p>
              <p className={`font-mono text-xs tracking-widest mt-1 border px-2 py-0.5 inline-block ${recColor(score.recommendation)}`}>
                {score.recommendation ?? '—'}
              </p>
            </div>
          )}
        </div>
      </header>

      <div className="flex divide-x divide-line">
        {/* Left: score breakdown */}
        <aside className="w-72 shrink-0 px-8 py-6">
          <p className="font-mono text-xs text-muted tracking-widest uppercase mb-6">Score Breakdown</p>

          {score ? (
            <div className="space-y-5">
              {Object.entries(score.dimension_scores).map(([key, val]) => (
                <div key={key} className="flex items-center justify-between">
                  <span className="font-sans text-sm text-muted">{DIMENSION_LABELS[key] ?? key}</span>
                  <span className={`font-mono font-semibold ${scoreColor(val)}`}>
                    {typeof val === 'number' ? val.toFixed(1) : val}
                  </span>
                </div>
              ))}
              <div className="border-t border-line pt-4 flex items-center justify-between">
                <span className="font-sans text-sm font-semibold text-white">Total</span>
                <span className={`font-mono font-semibold text-lg ${scoreColor(score.total_score)}`}>
                  {score.total_score.toFixed(1)}
                </span>
              </div>

              {score.scoring_notes && (
                <div className="mt-6 pt-6 border-t border-line">
                  <p className="font-mono text-xs text-muted tracking-widest uppercase mb-3">Scoring Notes</p>
                  <p className="font-sans text-sm text-muted leading-6">{score.scoring_notes}</p>
                </div>
              )}
            </div>
          ) : (
            <p className="font-mono text-xs text-muted">NOT YET SCORED</p>
          )}
        </aside>

        {/* Right: memo */}
        <main className="flex-1 px-8 py-6">
          <div className="flex items-center justify-between mb-6">
            <p className="font-mono text-xs text-muted tracking-widest uppercase">
              Investment Memo
              {memo && (
                <span className="ml-3 text-muted">
                  v{memo.version} · {memo.cached ? 'CACHED' : 'FRESH'}
                </span>
              )}
            </p>
            <button
              onClick={generateMemo}
              disabled={generatingMemo}
              className="px-4 py-2 text-xs font-mono font-semibold tracking-widest uppercase border border-amber text-amber hover:bg-amber hover:text-navy transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {generatingMemo ? 'GENERATING...' : memo ? 'REGENERATE MEMO' : 'GENERATE MEMO'}
            </button>
          </div>

          {memoError && (
            <p className="font-mono text-xs text-muted mb-4 border border-line p-3">{memoError}</p>
          )}

          {generatingMemo && (
            <div className="py-12 text-center">
              <p className="font-mono text-xs text-muted tracking-widest animate-pulse">
                GENERATING MEMO — THIS MAY TAKE UP TO 30 SECONDS...
              </p>
            </div>
          )}

          {memo && !generatingMemo && (
            <article className="max-w-2xl leading-relaxed">
              {formatMemo(memo.content)}
            </article>
          )}

          {!memo && !generatingMemo && (
            <div className="py-12 text-center border border-line">
              <p className="font-mono text-xs text-muted tracking-widest">NO MEMO GENERATED YET</p>
              <p className="font-sans text-sm text-muted mt-2">Click "Generate Memo" to create an AI-powered investment analysis.</p>
            </div>
          )}

          {/* Documents */}
          <div className="mt-10 border-t border-line pt-8">
            <div className="flex items-center justify-between mb-4">
              <p className="font-mono text-xs text-muted tracking-widest uppercase">
                Client Documents
                {documents.length > 0 && (
                  <span className="ml-2 text-amber">{documents.length}</span>
                )}
              </p>
              <label className={`px-4 py-2 text-xs font-mono font-semibold tracking-widest uppercase border cursor-pointer transition-colors ${
                uploading
                  ? 'border-line text-muted opacity-50 cursor-not-allowed'
                  : 'border-line text-muted hover:border-white hover:text-white'
              }`}>
                {uploading ? 'UPLOADING...' : 'UPLOAD DOCUMENT'}
                <input
                  type="file"
                  accept=".pdf,.txt,.csv,.md"
                  className="sr-only"
                  disabled={uploading}
                  onChange={e => {
                    const file = e.target.files?.[0]
                    if (file) uploadDocument(file)
                    e.target.value = ''
                  }}
                />
              </label>
            </div>

            {uploadError && (
              <p className="font-mono text-xs text-muted mb-3 border border-line p-2">{uploadError}</p>
            )}

            {documents.length === 0 ? (
              <p className="font-sans text-sm text-muted">
                No documents uploaded. Upload a CIM, teaser, or notes to enrich memo generation.
              </p>
            ) : (
              <div className="space-y-2">
                {documents.map(doc => (
                  <div key={doc.id} className="flex items-center justify-between border border-line px-4 py-3">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs text-muted">{doc.file_type === 'application/pdf' ? 'PDF' : 'TXT'}</span>
                      <span className="font-mono text-sm text-white">{doc.filename}</span>
                    </div>
                    <span className="font-mono text-xs text-muted">
                      {new Date(doc.uploaded_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  )
}
