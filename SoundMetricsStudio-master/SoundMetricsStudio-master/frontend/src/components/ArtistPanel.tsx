import { useRef, type KeyboardEvent } from 'react'
import { marked } from 'marked'
import type { ArtistContext } from '../types'
import { useArtistSearch } from '../hooks/useArtistSearch'
import { useAnalysisStream } from '../hooks/useAnalysisStream'
import { ArtistItem } from './ArtistItem'

interface Props {
  onArtistContext: (ctx: ArtistContext) => void
}

export function ArtistPanel({ onArtistContext }: Props) {
  const searchRef = useRef<HTMLInputElement>(null)
  const { results, isLoading, error, search } = useArtistSearch()
  const { analysisText, status, isAnalyzing, analyze } = useAnalysisStream(onArtistContext)

  function doSearch() {
    search(searchRef.current?.value ?? '')
  }

  function handleSearchKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') doSearch()
  }

  const hasAnalysis = analysisText.length > 0

  return (
    <div className="panel" id="artist-panel">
      <div className="panel-header">
        <h2>Artist Intelligence</h2>
        <p>Search and select an artist for a strategic analysis</p>

      </div>

      <div id="search-row">
        <input
          ref={searchRef}
          type="text"
          id="search-input"
          placeholder="Search artists…"
          onKeyDown={handleSearchKey}
        />
        <button className="btn" onClick={doSearch} disabled={isLoading}>
          Search
        </button>
      </div>

      <div id="artist-results">
        {isLoading && <span style={{ color: 'var(--text-dim)', fontSize: '12px' }}>Searching…</span>}
        {error && <span className="error-text">Search failed: {error}</span>}
        {!isLoading && results.map(a => (
          <ArtistItem key={a.cm_id} artist={a} onClick={analyze} />
        ))}
        {!isLoading && !error && results.length === 0 && searchRef.current?.value && (
          <span style={{ color: 'var(--text-dim)', fontSize: '12px' }}>No results found.</span>
        )}
      </div>

      <div id="status-bar">
        {status && (
          <>
            {isAnalyzing && <div className="spinner" />}
            <span>{status}</span>
          </>
        )}
      </div>

      <div id="analysis-area">
        {!hasAnalysis && (
          <div id="analysis-placeholder">
            Search for an artist and click their name to generate a strategic analysis.
          </div>
        )}
        {hasAnalysis && (
          <div
            id="analysis-content"
            dangerouslySetInnerHTML={{ __html: marked.parse(analysisText) as string }}
          />
        )}
      </div>
    </div>
  )
}
