import { useState } from 'react'
import type { DataSource } from '../types'

// ── Default data sources (matches architecture doc exactly) ──────────────────
const LIVE_SOURCES: DataSource[] = [
  {
    id: 'chartmetric',
    icon: '📊',
    label: 'Chartmetric',
    type: 'live',
    status: 'connected',
    detail: 'Connected',
  },
  {
    id: 'soundcharts',
    icon: '🔊',
    label: 'Soundcharts',
    type: 'live',
    status: 'pending',
    detail: 'Pending setup',
  },
  {
    id: 'youtube',
    icon: '▶️',
    label: 'YouTube API',
    type: 'live',
    status: 'connected',
    detail: 'Connected',
  },
  {
    id: 'instagram',
    icon: '📸',
    label: 'Instagram',
    type: 'live',
    status: 'pending',
    detail: 'Pending setup',
  },
  {
    id: 'lastfm',
    icon: '🎵',
    label: 'Last.fm',
    type: 'live',
    status: 'connected',
    detail: 'Connected',
  },
]

const MANUAL_SOURCES: DataSource[] = [
  {
    id: 'spotify-for-artists',
    icon: '🎵',
    label: 'Spotify for Artists',
    type: 'manual',
    status: 'uploaded',
    fileCount: 3,
    detail: '3 files uploaded',
  },
  {
    id: 'too-lost',
    icon: '💰',
    label: 'Too Lost',
    type: 'manual',
    status: 'uploaded',
    fileCount: 1,
    detail: '1 file uploaded',
  },
  {
    id: 'prs',
    icon: '📄',
    label: 'PRS Statements',
    type: 'manual',
    status: 'not-uploaded',
    detail: 'Not uploaded',
  },
  {
    id: 'tiktok',
    icon: '🎵',
    label: 'TikTok',
    type: 'manual',
    status: 'not-uploaded',
    detail: 'Not uploaded',
  },
]

// ── Status badge ─────────────────────────────────────────────────────────────
function StatusBadge({ status, detail }: { status: DataSource['status']; detail?: string }) {
  const map: Record<DataSource['status'], { cls: string; label: string }> = {
    connected:    { cls: 'badge-green', label: 'Connected' },
    uploaded:     { cls: 'badge-green', label: detail ?? 'Uploaded' },
    pending:      { cls: 'badge-amber', label: 'Pending' },
    'not-uploaded': { cls: 'badge-muted', label: 'Not uploaded' },
  }
  const { cls, label } = map[status]
  return <span className={`badge ${cls}`}>{label}</span>
}

// ── Rail icon (collapsed state) ───────────────────────────────────────────────
function RailIcon({ source, onClick }: { source: DataSource; onClick: () => void }) {
  const statusClass =
    source.status === 'connected' || source.status === 'uploaded'
      ? 'connected'
      : 'pending'
  return (
    <div
      className={`ds-rail-icon ${statusClass}`}
      onClick={onClick}
      title={source.label}
    >
      {source.icon}
    </div>
  )
}

// ── Main component ────────────────────────────────────────────────────────────
export function DataSourcesPanel() {
  const [collapsed, setCollapsed] = useState(false)

  const allSources = [...LIVE_SOURCES, ...MANUAL_SOURCES]

  return (
    <aside
      id="data-sources-panel"
      className={collapsed ? 'collapsed' : ''}
      aria-label="Data sources"
    >

      {/* ── Icon rail (collapsed) ──────────────────────────────────────── */}
      <div className="ds-icon-rail">
        {/* Expand button at top of rail */}
        <div
          className="ds-rail-icon"
          onClick={() => setCollapsed(false)}
          title="Expand data sources"
          style={{ fontSize: '14px' }}
        >
          ›
        </div>
        {allSources.map(src => (
          <RailIcon
            key={src.id}
            source={src}
            onClick={() => setCollapsed(false)}
          />
        ))}
      </div>

      {/* ── Full panel (expanded) ──────────────────────────────────────── */}
      <div className="ds-panel-content">

        {/* Header */}
        <div className="ds-header">
          <div>
            <div className="ds-header-title">Data sources</div>
            <div className="ds-header-sub">Your connected data</div>
          </div>
          <button
            className="ds-collapse-btn"
            onClick={() => setCollapsed(true)}
            title="Collapse panel"
            aria-label="Collapse data sources panel"
          >
            ‹
          </button>
        </div>

        {/* Scrollable source list */}
        <div className="ds-scroll">

          {/* Live APIs */}
          <div className="ds-section-label">Live APIs</div>
          {LIVE_SOURCES.map(src => (
            <div key={src.id} className="ds-item">
              <div className="ds-item-icon">{src.icon}</div>
              <div className="ds-item-info">
                <div className="ds-item-name">{src.label}</div>
                <div className="ds-item-detail">{src.detail}</div>
              </div>
              <StatusBadge status={src.status} detail={src.detail} />
            </div>
          ))}

          {/* Manual uploads */}
          <div className="ds-section-label" style={{ marginTop: '8px' }}>
            Manual uploads
          </div>
          {MANUAL_SOURCES.map(src => (
            <div key={src.id} className="ds-item">
              <div className="ds-item-icon">{src.icon}</div>
              <div className="ds-item-info">
                <div className="ds-item-name">{src.label}</div>
                <div className="ds-item-detail">{src.detail}</div>
              </div>
              <StatusBadge status={src.status} detail={src.detail} />
            </div>
          ))}

        </div>

        {/* Upload button */}
        <button
          className="ds-upload-btn"
          onClick={() => {
            // Pro feature — placeholder until upload flow is built
            alert('File uploads are a Pro feature. Create a free account to get early access.')
          }}
          aria-label="Upload a data file"
        >
          + Upload data file
        </button>

      </div>
    </aside>
  )
}
