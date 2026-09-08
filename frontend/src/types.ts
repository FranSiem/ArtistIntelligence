// ── Existing types (unchanged — backend contract) ────────────────────────────
export interface Message { role: 'user' | 'assistant'; content: string }
export interface ArtistContext { name: string; analysis: string; session_id: string }
export interface Artist { cm_id: number; name: string; image_url: string | null; genres: string[] | null }
export type AnalysisEvent =
  | { type: 'status'; text: string }
  | { type: 'token'; text: string }
  | { type: 'done'; artist_name: string; session_id: string }
  | { type: 'error'; text: string }

// ── Navigation ────────────────────────────────────────────────────────────────
export type Page = 'landing' | 'signin' | 'signup' | 'conversation'

// ── Data sources panel ────────────────────────────────────────────────────────
export type DataSourceStatus = 'connected' | 'pending' | 'uploaded' | 'not-uploaded'
export type DataSourceType = 'live' | 'manual'

export interface DataSource {
  id: string
  icon: string
  label: string
  type: DataSourceType
  status: DataSourceStatus
  /** For manual uploads: number of files uploaded */
  fileCount?: number
  /** Detail line shown under the label (e.g. "3 files uploaded", "Pending setup") */
  detail?: string
}

// ── Report builder panel ──────────────────────────────────────────────────────
export type ReportSectionStatus = 'done' | 'building' | 'pending' | 'locked'

export interface ReportSection {
  id: string
  icon: string
  title: string
  status: ReportSectionStatus
  summary: string
  selected: boolean
  /** Locked sections require an action (e.g. upload data) before they unlock */
  lockReason?: string
}
