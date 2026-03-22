import { useRef, type KeyboardEvent } from 'react'
import type { Artist } from '../types'
import { useArtistSearch } from '../hooks/useArtistSearch'
import logo from '../assets/logo.png'

interface Props {
  onSelectArtist: (artist: Artist) => void
}

export function LandingPage({ onSelectArtist }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const { results, isLoading, error, search } = useArtistSearch()

  function handleSearch() {
    const q = inputRef.current?.value.trim()
    if (q) search(q)
  }

  function handleKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter') handleSearch()
  }

  function handleSuggestion(name: string) {
    if (inputRef.current) inputRef.current.value = name
    search(name)
  }

  const suggestions = ['Taylor Swift', 'Francesca & The Apostrophe', 'The Weeknd', 'Mia Dae', 'Drake', 'One Nice Boi', 'Billie Eilish', 'Cocco Bea']
  const hasResults = results.length > 0

  return (
    <div id="landing">
      <div id="landing-inner">
        <img src={logo} alt="SoundMetrics Studio" id="landing-logo" />
        <h1 id="landing-title">Discover Artist Insights with AI</h1>
        <p id="landing-sub">
          Search for a musician and get AI-powered overview on their presence industry-wide to create a next steps strategy.
        </p>

        <div id="landing-search-row">
          <span className="landing-search-icon">🔍</span>
          <input
            ref={inputRef}
            id="landing-input"
            type="text"
            placeholder="Search for a musician or artist…"
            onKeyDown={handleKey}
            autoFocus
          />
          <button id="landing-btn" onClick={handleSearch} disabled={isLoading}>
            {isLoading ? 'Searching…' : 'Search'}
          </button>
        </div>

        {!hasResults && !isLoading && (
          <p id="landing-suggestions">
            Try searching:{' '}
            {suggestions.map((s, i) => (
              <span key={s}>
                <button className="suggestion-chip" onClick={() => handleSuggestion(s)}>{s}</button>
                {i < suggestions.length - 1 && ', '}
              </span>
            ))}
          </p>
        )}

        {error && <p className="landing-error">Search failed: {error}</p>}

        {hasResults && (
          <div id="landing-results">
            <div className="results-label">{results.length} result{results.length !== 1 ? 's' : ''}</div>
            {results.map(artist => {
              const initial = artist.name.charAt(0).toUpperCase()
              const genres = Array.isArray(artist.genres) ? artist.genres.slice(0, 3) : []
              return (
                <div key={artist.cm_id} className="landing-artist-item" onClick={() => onSelectArtist(artist)}>
                  <div className="artist-avatar-wrap">
                    {artist.image_url ? (
                      <img
                        className="artist-avatar"
                        src={artist.image_url}
                        alt={artist.name}
                        onError={e => {
                          const img = e.target as HTMLImageElement
                          img.style.display = 'none'
                          const fb = img.nextElementSibling as HTMLElement
                          if (fb) fb.style.display = 'flex'
                        }}
                      />
                    ) : null}
                    <div className="artist-avatar-fallback" style={{ display: artist.image_url ? 'none' : 'flex' }}>
                      {initial}
                    </div>
                  </div>
                  <div className="artist-info">
                    <div className="artist-name" style={{ color: '#0d0d14' }}>{artist.name}</div>
                    {genres.length > 0 && (
                      <div className="artist-genres">
                        {genres.map(g => (
                          <span key={g} className="genre-chip landing-genre-chip">{g}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  <span className="artist-arrow" style={{ color: '#aaa' }}>›</span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
