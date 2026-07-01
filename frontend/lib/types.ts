export interface ScoreSummary {
  total_score: number
  recommendation: 'PASS' | 'WATCH' | 'REACH_OUT' | null
  dimension_scores: {
    thesis_fit: number
    team_signals: number
    market_timing: number
    data_quality: number
  }
  scored_at: string
}

export interface CompanyListItem {
  id: string
  client_id: string
  name: string
  sector: string
  stage: string
  source: string
  source_url: string
  created_at: string
  score: ScoreSummary | null
}

export interface PaginatedDeals {
  items: CompanyListItem[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface CompanyDetail {
  id: string
  client_id: string
  name: string
  sector: string
  stage: string
  funding_total: number | null
  latest_round_size: number | null
  source: string
  source_url: string
  raw_data: Record<string, unknown>
  created_at: string
  score: {
    score_id: string
    total_score: number
    recommendation: string | null
    dimension_scores: Record<string, number>
    scoring_notes: string
    scored_at: string
  } | null
  memo: {
    memo_id: string
    content: string
    version: number
    generated_at: string
  } | null
}

export interface MemoResponse {
  memo_id: string
  company_id: string
  client_id: string
  content: string
  version: number
  generated_at: string
  cached: boolean
}

export interface ClientResponse {
  id: string
  name: string
  thesis_json: ThesisJson
  config_json: Record<string, unknown>
  created_at: string
}

export interface ThesisJson {
  sectors?: string[]
  stages?: string[]
  geography?: string[]
  check_size_min?: number
  check_size_max?: number
  keywords?: string[]
}

export interface PipelineJobResponse {
  job_id: string
  status: string
}

export interface DocumentRecord {
  id: string
  client_id: string
  company_id: string | null
  filename: string
  file_type: string
  uploaded_at: string
}

export interface AlertRecord {
  id: string
  client_id: string
  company_id: string
  channel: string
  message: string
  sent_at: string
}

export interface AlertConfig {
  alerts_enabled: boolean
  alert_threshold: number
  phone_number: string
  dashboard_url?: string
}
