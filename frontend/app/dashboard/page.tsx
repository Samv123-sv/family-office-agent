'use client'

import { useEffect, useState, useCallback } from 'react'
import { useAuth } from '@clerk/nextjs'
import Link from 'next/link'
import { apiFetch } from '@/lib/api'
import type { PaginatedDeals, ClientResponse, PipelineJobResponse } from '@/lib/types'

const SECTORS = ['SaaS', 'FinTech', 'AI/ML', 'HealthTech', 'CleanTech', 'DeepTech', 'Marketplace']
const STAGES = ['Pre-Seed', 'Seed', 'Series A', 'Series B', 'Series C+']
const RECS = ['', 'PASS', 'WATCH', 'REACH_OUT'] as const

function recColor(rec: string | null) {
  if (rec === 'REACH_OUT') return 'text-amber'
  if (rec === 'WATCH') return 'text-white'
  return 'text-muted'
}

function scoreColor(score: number | null) {
  if (score === null) return 'text-muted'
  if (score >= 8) return 'text-amber'
  if (score >= 6) return 'text-white'
  return 'text-muted'
}

function daysSince(iso: string) {
  const ms = Date.now() - new Date(iso).getTime()
  return Math.floor(ms / 86_400_000)
}

export default function DashboardPage() {
  const { getToken } = useAuth()
  const [client, setClient] = useState<ClientResponse | null>(null)
  const [deals, setDeals] = useState<PaginatedDeals | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sector, setSector] = useState('')
  const [stage, setStage] = useState('')
  const [minScore, setMinScore] = useState(0)
  const [recommendation, setRecommendation] = useState('')
  const [page, setPage] = useState(1)
  const [pipelineJob, setPipelineJob] = useState<{ id: string; status: string } | null>(null)

  const fetchDeals = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ page: String(page), limit: '20' })
      if (sector) params.set('sector', sector)
      if (stage) params.set('stage', stage)
      if (minScore > 0) params.set('min_score', String(minScore))
      if (recommendation) params.set('recommendation', recommendation)
      const data = await apiFetch<PaginatedDeals>(`/api/deals?${params}`, getToken)
      setDeals(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load deals')
    } finally {
      setLoading(false)
    }
  }, [getToken, sector, stage, minScore, recommendation, page])

  useEffect(() => {
    const load = async () => {
      try {
        const c = await apiFetch<ClientResponse>('/api/thesis', getToken)
        setClient(c)
      } catch {
        // client info is non-critical
      }
    }
    load()
  }, [getToken])

  useEffect(() => {
    fetchDeals()
  }, [fetchDeals])

  const runPipeline = async () => {
    try {
      const job = await apiFetch<PipelineJobResponse>('/api/pipeline/run', getToken, { method: 'POST' })
      setPipelineJob({ id: job.job_id, status: 'QUEUED' })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start pipeline')
    }
  }

  return (
    <div className="min-h-screen bg-navy">
      {/* Header */}
      <header className="border-b border-line px-8 py-4 flex items-center justify-between">
        <div>
          <p className="text-xs text-muted font-mono uppercase tracking-widest mb-1">Deal Flow Intelligence</p>
          <h1 className="text-lg font-semibold text-white">
            {client?.name ?? '—'}
          </h1>
        </div>
        <div className="flex items-center gap-6">
          {pipelineJob && (
            <span className="font-mono text-xs text-muted">
              JOB {pipelineJob.id.slice(0, 8).toUpperCase()} · {pipelineJob.status}
            </span>
          )}
          <button
            onClick={runPipeline}
            className="px-4 py-2 text-xs font-mono font-semibold tracking-widest uppercase border border-amber text-amber hover:bg-amber hover:text-navy transition-colors"
          >
            Run Pipeline
          </button>
        </div>
      </header>

      {/* Filter bar */}
      <div className="border-b border-line px-8 py-3 flex items-center gap-6 bg-surface">
        <select
          value={sector}
          onChange={e => { setSector(e.target.value); setPage(1) }}
          className="bg-navy border border-line text-sm text-white font-mono px-3 py-1.5 focus:outline-none focus:border-amber"
        >
          <option value="">All Sectors</option>
          {SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <select
          value={stage}
          onChange={e => { setStage(e.target.value); setPage(1) }}
          className="bg-navy border border-line text-sm text-white font-mono px-3 py-1.5 focus:outline-none focus:border-amber"
        >
          <option value="">All Stages</option>
          {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-muted">MIN SCORE</span>
          <input
            type="range"
            min={0}
            max={10}
            step={0.5}
            value={minScore}
            onChange={e => { setMinScore(Number(e.target.value)); setPage(1) }}
            className="w-24"
          />
          <span className="font-mono text-sm text-white w-6">{minScore > 0 ? minScore : '—'}</span>
        </div>

        <div className="flex items-center gap-1 ml-auto">
          {RECS.map(r => (
            <button
              key={r}
              onClick={() => { setRecommendation(r); setPage(1) }}
              className={`px-3 py-1 text-xs font-mono tracking-wider border transition-colors ${
                recommendation === r
                  ? 'border-amber text-amber bg-amber/10'
                  : 'border-line text-muted hover:border-white hover:text-white'
              }`}
            >
              {r || 'ALL'}
            </button>
          ))}
        </div>
      </div>

      {/* Deal table */}
      <main className="px-8 py-6">
        {error && (
          <div className="border border-line p-4 mb-4 font-mono text-sm text-muted">{error}</div>
        )}

        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-line">
              {['Company', 'Sector', 'Stage', 'Score', 'Rec.', 'Source', 'Days'].map(h => (
                <th key={h} className="text-left py-2 pr-6 font-mono text-xs text-muted tracking-widest uppercase">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="py-12 text-center font-mono text-muted text-xs tracking-widest">
                  LOADING...
                </td>
              </tr>
            ) : deals?.items.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center font-mono text-muted text-xs tracking-widest">
                  NO DEALS MATCH CURRENT FILTERS
                </td>
              </tr>
            ) : (
              deals?.items.map(deal => (
                <tr
                  key={deal.id}
                  className="border-b border-line hover:bg-surface cursor-pointer transition-colors group"
                >
                  <td className="py-3 pr-6">
                    <Link href={`/deals/${deal.id}`} className="block w-full">
                      <span className="font-semibold text-white group-hover:text-amber transition-colors">
                        {deal.name}
                      </span>
                    </Link>
                  </td>
                  <td className="py-3 pr-6 text-muted font-mono text-xs">{deal.sector}</td>
                  <td className="py-3 pr-6 text-muted font-mono text-xs">{deal.stage}</td>
                  <td className="py-3 pr-6">
                    <span className={`font-mono font-semibold ${scoreColor(deal.score?.total_score ?? null)}`}>
                      {deal.score?.total_score.toFixed(1) ?? '—'}
                    </span>
                  </td>
                  <td className="py-3 pr-6">
                    <span className={`font-mono text-xs tracking-wider ${recColor(deal.score?.recommendation ?? null)}`}>
                      {deal.score?.recommendation ?? '—'}
                    </span>
                  </td>
                  <td className="py-3 pr-6 text-muted font-mono text-xs">{deal.source}</td>
                  <td className="py-3 font-mono text-xs text-muted">{daysSince(deal.created_at)}d</td>
                </tr>
              ))
            )}
          </tbody>
        </table>

        {/* Pagination */}
        {deals && deals.pages > 1 && (
          <div className="flex items-center gap-4 mt-6 font-mono text-xs text-muted">
            <button
              disabled={page <= 1}
              onClick={() => setPage(p => p - 1)}
              className="disabled:opacity-30 hover:text-white transition-colors"
            >
              ← PREV
            </button>
            <span>PAGE {page} OF {deals.pages}</span>
            <button
              disabled={page >= deals.pages}
              onClick={() => setPage(p => p + 1)}
              className="disabled:opacity-30 hover:text-white transition-colors"
            >
              NEXT →
            </button>
          </div>
        )}

        {deals && (
          <p className="mt-4 font-mono text-xs text-muted">
            {deals.total} {deals.total === 1 ? 'COMPANY' : 'COMPANIES'}
          </p>
        )}
      </main>
    </div>
  )
}
