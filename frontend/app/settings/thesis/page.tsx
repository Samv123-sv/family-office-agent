'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import Link from 'next/link'
import { apiFetch } from '@/lib/api'
import type { AlertConfig, AlertRecord, ClientResponse, ThesisJson } from '@/lib/types'

const SECTOR_OPTIONS = ['SaaS', 'FinTech', 'AI/ML', 'HealthTech', 'CleanTech', 'DeepTech', 'Marketplace', 'Other']
const STAGE_OPTIONS = ['Pre-Seed', 'Seed', 'Series A', 'Series B', 'Series C+']
const GEO_OPTIONS = ['US', 'Europe', 'LATAM', 'Asia', 'Global']

const DEFAULT_ALERT_CONFIG: AlertConfig = {
  alerts_enabled: false,
  alert_threshold: 7.5,
  phone_number: '',
}

export default function ThesisSettingsPage() {
  const { getToken } = useAuth()
  const [client, setClient] = useState<ClientResponse | null>(null)
  const [thesis, setThesis] = useState<ThesisJson>({})
  const [alertConfig, setAlertConfig] = useState<AlertConfig>(DEFAULT_ALERT_CONFIG)
  const [recentAlerts, setRecentAlerts] = useState<AlertRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const [data, alerts] = await Promise.all([
          apiFetch<ClientResponse>('/api/thesis', getToken),
          apiFetch<AlertRecord[]>('/api/alerts?limit=10', getToken),
        ])
        setClient(data)
        setThesis(data.thesis_json ?? {})
        const cfg = data.config_json as Partial<AlertConfig>
        setAlertConfig({
          alerts_enabled: cfg.alerts_enabled ?? false,
          alert_threshold: cfg.alert_threshold ?? 7.5,
          phone_number: cfg.phone_number ?? '',
        })
        setRecentAlerts(alerts)
      } catch (e) {
        setError(e instanceof Error ? e.message : 'Failed to load settings')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [getToken])

  const toggleItem = (field: keyof ThesisJson, value: string) => {
    setThesis(prev => {
      const current = (prev[field] as string[] | undefined) ?? []
      const next = current.includes(value)
        ? current.filter(v => v !== value)
        : [...current, value]
      return { ...prev, [field]: next }
    })
    setSaved(false)
  }

  const setNumber = (field: 'check_size_min' | 'check_size_max', value: string) => {
    const num = value === '' ? undefined : Number(value)
    setThesis(prev => ({ ...prev, [field]: num }))
    setSaved(false)
  }

  const setKeywords = (value: string) => {
    const kws = value.split(',').map(k => k.trim()).filter(Boolean)
    setThesis(prev => ({ ...prev, keywords: kws }))
    setSaved(false)
  }

  const save = async () => {
    setSaving(true)
    setError(null)
    try {
      const merged_config = {
        ...(client?.config_json ?? {}),
        alerts_enabled: alertConfig.alerts_enabled,
        alert_threshold: alertConfig.alert_threshold,
        phone_number: alertConfig.phone_number,
      }
      await apiFetch<ClientResponse>('/api/thesis', getToken, {
        method: 'PUT',
        body: JSON.stringify({ thesis_json: thesis, config_json: merged_config }),
      })
      setSaved(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-navy flex items-center justify-center">
        <p className="font-mono text-xs text-muted tracking-widest">LOADING...</p>
      </div>
    )
  }

  const sectors = thesis.sectors ?? []
  const stages = thesis.stages ?? []
  const geography = thesis.geography ?? []

  return (
    <div className="min-h-screen bg-navy">
      {/* Header */}
      <header className="border-b border-line px-8 py-4 flex items-center justify-between">
        <div>
          <Link href="/dashboard" className="font-mono text-xs text-muted hover:text-white transition-colors">
            ← DASHBOARD
          </Link>
          <h1 className="text-lg font-semibold text-white mt-2">Investment Thesis</h1>
          {client?.created_at && (
            <p className="font-mono text-xs text-muted mt-0.5">
              Client: {client.name} · Last updated: {new Date(client.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </p>
          )}
        </div>
        <div className="flex items-center gap-4">
          {saved && <span className="font-mono text-xs text-amber tracking-widest">SAVED ✓</span>}
          {error && <span className="font-mono text-xs text-muted">{error}</span>}
          <button
            onClick={save}
            disabled={saving}
            className="px-6 py-2 text-xs font-mono font-semibold tracking-widest uppercase border border-amber text-amber hover:bg-amber hover:text-navy transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'SAVING...' : 'SAVE SETTINGS'}
          </button>
        </div>
      </header>

      <main className="px-8 py-8 max-w-3xl space-y-10">
        {/* Sectors */}
        <section>
          <p className="font-mono text-xs text-muted tracking-widest uppercase mb-4">Sectors</p>
          <div className="flex flex-wrap gap-2">
            {SECTOR_OPTIONS.map(s => (
              <button
                key={s}
                onClick={() => toggleItem('sectors', s)}
                className={`px-4 py-2 text-xs font-mono tracking-wider border transition-colors ${
                  sectors.includes(s)
                    ? 'border-amber text-amber bg-amber/10'
                    : 'border-line text-muted hover:border-white hover:text-white'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </section>

        {/* Stages */}
        <section>
          <p className="font-mono text-xs text-muted tracking-widest uppercase mb-4">Stage Range</p>
          <div className="flex flex-wrap gap-2">
            {STAGE_OPTIONS.map(s => (
              <button
                key={s}
                onClick={() => toggleItem('stages', s)}
                className={`px-4 py-2 text-xs font-mono tracking-wider border transition-colors ${
                  stages.includes(s)
                    ? 'border-amber text-amber bg-amber/10'
                    : 'border-line text-muted hover:border-white hover:text-white'
                }`}
              >
                {s}
              </button>
            ))}
          </div>
        </section>

        {/* Geography */}
        <section>
          <p className="font-mono text-xs text-muted tracking-widest uppercase mb-4">Geography</p>
          <div className="flex flex-wrap gap-2">
            {GEO_OPTIONS.map(g => (
              <button
                key={g}
                onClick={() => toggleItem('geography', g)}
                className={`px-4 py-2 text-xs font-mono tracking-wider border transition-colors ${
                  geography.includes(g)
                    ? 'border-amber text-amber bg-amber/10'
                    : 'border-line text-muted hover:border-white hover:text-white'
                }`}
              >
                {g}
              </button>
            ))}
          </div>
        </section>

        {/* Check size */}
        <section>
          <p className="font-mono text-xs text-muted tracking-widest uppercase mb-4">Check Size</p>
          <div className="flex items-center gap-6">
            <div className="flex flex-col gap-1">
              <label className="font-mono text-xs text-muted">MINIMUM ($)</label>
              <input
                type="number"
                value={thesis.check_size_min ?? ''}
                onChange={e => setNumber('check_size_min', e.target.value)}
                placeholder="500000"
                className="bg-surface border border-line text-white font-mono text-sm px-3 py-2 w-36 focus:outline-none focus:border-amber"
              />
            </div>
            <span className="text-muted font-mono text-sm mt-4">—</span>
            <div className="flex flex-col gap-1">
              <label className="font-mono text-xs text-muted">MAXIMUM ($)</label>
              <input
                type="number"
                value={thesis.check_size_max ?? ''}
                onChange={e => setNumber('check_size_max', e.target.value)}
                placeholder="5000000"
                className="bg-surface border border-line text-white font-mono text-sm px-3 py-2 w-36 focus:outline-none focus:border-amber"
              />
            </div>
          </div>
        </section>

        {/* Keywords */}
        <section>
          <p className="font-mono text-xs text-muted tracking-widest uppercase mb-4">Keywords</p>
          <p className="font-sans text-xs text-muted mb-3">Comma-separated terms that signal strong thesis alignment.</p>
          <textarea
            value={(thesis.keywords ?? []).join(', ')}
            onChange={e => setKeywords(e.target.value)}
            rows={3}
            placeholder="AI, machine learning, automation, B2B SaaS..."
            className="w-full bg-surface border border-line text-white font-mono text-sm px-4 py-3 focus:outline-none focus:border-amber resize-none placeholder:text-muted/40"
          />
        </section>

        {/* Alert Preferences */}
        <section className="border border-line p-6 space-y-6">
          <div className="flex items-center justify-between">
            <p className="font-mono text-xs text-muted tracking-widest uppercase">Deal Alerts</p>
            <button
              onClick={() => {
                setAlertConfig(prev => ({ ...prev, alerts_enabled: !prev.alerts_enabled }))
                setSaved(false)
              }}
              className={`px-4 py-1.5 text-xs font-mono tracking-wider border transition-colors ${
                alertConfig.alerts_enabled
                  ? 'border-amber text-amber bg-amber/10'
                  : 'border-line text-muted hover:border-white hover:text-white'
              }`}
            >
              {alertConfig.alerts_enabled ? 'ALERTS ON' : 'ALERTS OFF'}
            </button>
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="font-mono text-xs text-muted">SCORE THRESHOLD</label>
              <span className="font-mono text-xs text-amber">{alertConfig.alert_threshold.toFixed(1)}</span>
            </div>
            <input
              type="range"
              min={5}
              max={10}
              step={0.5}
              value={alertConfig.alert_threshold}
              onChange={e => {
                setAlertConfig(prev => ({ ...prev, alert_threshold: Number(e.target.value) }))
                setSaved(false)
              }}
              className="w-full accent-amber"
              disabled={!alertConfig.alerts_enabled}
            />
            <div className="flex justify-between font-mono text-xs text-muted/50">
              <span>5.0</span>
              <span>Only fires on REACH_OUT</span>
              <span>10.0</span>
            </div>
          </div>

          <div className="flex flex-col gap-1">
            <label className="font-mono text-xs text-muted">PHONE NUMBER</label>
            <input
              type="tel"
              value={alertConfig.phone_number}
              onChange={e => {
                setAlertConfig(prev => ({ ...prev, phone_number: e.target.value }))
                setSaved(false)
              }}
              placeholder="+15551234567"
              disabled={!alertConfig.alerts_enabled}
              className="bg-surface border border-line text-white font-mono text-sm px-3 py-2 w-56 focus:outline-none focus:border-amber disabled:opacity-40"
            />
            <p className="font-mono text-xs text-muted/60">E.164 format. Receives SMS when score ≥ threshold.</p>
          </div>
        </section>

        {/* Thesis Preview */}
        {(sectors.length > 0 || stages.length > 0) && (
          <section className="border border-line p-6">
            <p className="font-mono text-xs text-muted tracking-widest uppercase mb-4">Thesis Preview</p>
            <p className="font-serif text-base text-white leading-8">
              Targeting{' '}
              {sectors.length > 0 ? sectors.join(', ') : 'any sector'}{' '}
              companies at the{' '}
              {stages.length > 0 ? stages.join(' / ') : 'any stage'}{' '}
              stage
              {geography.length > 0 ? ` in ${geography.join(', ')}` : ''}.
              {thesis.check_size_min || thesis.check_size_max ? (
                <> Check size ${(thesis.check_size_min ?? 0).toLocaleString()} – ${(thesis.check_size_max ?? 0).toLocaleString()}.</>
              ) : null}
              {thesis.keywords?.length ? (
                <> Key signals: {thesis.keywords.join(', ')}.</>
              ) : null}
            </p>
          </section>
        )}

        {/* Recent Alerts */}
        {recentAlerts.length > 0 && (
          <section>
            <p className="font-mono text-xs text-muted tracking-widest uppercase mb-4">Recent Alerts</p>
            <div className="space-y-2">
              {recentAlerts.map(alert => (
                <div key={alert.id} className="border border-line p-4 flex items-start gap-4">
                  <span className="font-mono text-xs text-muted whitespace-nowrap mt-0.5">
                    {new Date(alert.sent_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                  <p className="font-mono text-xs text-white leading-5">{alert.message}</p>
                </div>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
