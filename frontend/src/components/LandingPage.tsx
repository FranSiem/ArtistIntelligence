import { useRef, type KeyboardEvent } from 'react'
import type { Artist } from '../types'
import { useArtistSearch } from '../hooks/useArtistSearch'
import logo from '../assets/Sound Metrics Studio-Final-01.png'

interface Props {
  onSelectArtist: (artist: Artist) => void
  onSignIn: () => void
  onSignUp: () => void
}

export function LandingPage({ onSelectArtist, onSignIn, onSignUp }: Props) {
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

  const suggestions = [
    'Francesca & The Apostrophe',
    'FLO',
    'Jorja Smith',
    'Central Cee',
  ]

  const hasResults = results.length > 0

  return (
    <div id="landing">

      {/* ── Nav ─────────────────────────────────────────────────────────── */}
      <nav id="landing-nav">
        <div className="landing-nav-logo">
          <img src={logo} alt="Sound Metrics Studio" className="landing-nav-logo-img" />
          <span className="landing-nav-logo-text">Artist Intelligence</span>
        </div>
        <div className="landing-nav-actions">
          <button className="btn btn-secondary btn-sm" onClick={onSignIn}>
            Sign in
          </button>
          <button className="btn btn-primary btn-sm" onClick={onSignUp}>
            Get started free
          </button>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────────────────── */}
      <section id="landing-hero">
        <div className="hero-eyebrow">
          ✦ Public insights are always free — no card, no catch
        </div>

        <h1 className="hero-title">
          Know your audience.<br />Own your next move.
        </h1>

        <p className="hero-sub">
          Search any artist and get AI-powered insights from across streaming,
          social, and chart data. Sign up to unlock deeper analysis with your own data.
        </p>

        {/* Search */}
        <div id="landing-search-wrap">
          <div id="landing-search-row">
            <span id="landing-search-icon">🔍</span>
            <input
              ref={inputRef}
              id="landing-input"
              type="text"
              placeholder="Search for a musician or artist…"
              onKeyDown={handleKey}
              autoFocus
            />
            <button
              id="landing-search-btn"
              className="btn btn-primary btn-sm"
              onClick={handleSearch}
              disabled={isLoading}
            >
              {isLoading ? 'Searching…' : 'Analyse'}
            </button>
          </div>
        </div>

        {/* Suggestions */}
        {!hasResults && !isLoading && (
          <div id="landing-suggestions">
            <span className="suggestion-label">Try:</span>
            {suggestions.map(s => (
              <button
                key={s}
                className="suggestion-chip"
                onClick={() => handleSuggestion(s)}
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Error */}
        {error && <p className="landing-error">Search failed: {error}</p>}

        {/* Results */}
        {hasResults && (
          <div id="landing-results">
            <div className="results-label">
              {results.length} result{results.length !== 1 ? 's' : ''}
            </div>
            {results.map(artist => {
              const initial = artist.name.charAt(0).toUpperCase()
              const genres = Array.isArray(artist.genres) ? artist.genres.slice(0, 3) : []
              return (
                <div
                  key={artist.cm_id}
                  className="landing-artist-item"
                  onClick={() => onSelectArtist(artist)}
                >
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
                    <div
                      className="artist-avatar-fallback"
                      style={{ display: artist.image_url ? 'none' : 'flex' }}
                    >
                      {initial}
                    </div>
                  </div>
                  <div className="artist-info">
                    <div className="artist-name">{artist.name}</div>
                    {genres.length > 0 && (
                      <div className="artist-genres">
                        {genres.map(g => (
                          <span key={g} className="genre-chip landing-genre-chip">{g}</span>
                        ))}
                      </div>
                    )}
                  </div>
                  <span className="artist-arrow">›</span>
                </div>
              )
            })}
          </div>
        )}
      </section>

      {/* ── How it works ────────────────────────────────────────────────── */}
      <section id="landing-how">
        <p className="section-eyebrow">How it works</p>
        <h2 className="section-title">Start free. Go deeper when you're ready.</h2>
        <p className="section-sub">
          Public insights are always free. Your free account saves your searches
          and puts you first in line for Pro.
        </p>

        <div className="tier-grid">
          {/* Free tier */}
          <div className="tier-card">
            <span className="tier-badge tier-badge-free">Always free</span>
            <div className="tier-name">Public insights</div>
            <p className="tier-desc">
              Search any artist and get a market placement overview plus up to 3
              personalised next steps. Create a free account to save your searches
              and be first to know when Pro launches.
            </p>
            <ul className="tier-features">
              {[
                'Market placement overview from public data',
                'Up to 3 AI-generated next steps for your career',
                'Ask follow-up questions freely — no account needed',
                'Search any artist, not just yourself',
                'Create a free account to save searches and get early access to Pro',
              ].map(f => (
                <li key={f} className="tier-feature">
                  <span className="tier-feature-check">✓</span>
                  {f}
                </li>
              ))}
            </ul>
            <button className="btn btn-navy btn-full" onClick={handleSearch}>
              Start searching — always free
            </button>
          </div>

          {/* Pro tier */}
          <div className="tier-card featured">
            <span className="tier-badge tier-badge-pro">Pro — founding artist pricing coming soon</span>
            <div className="tier-name">Full Artist Intelligence</div>
            <p className="tier-desc">
              Upload your private data for deeper, personalised analysis. Get a full
              Artist Insights Report you can shape yourself, and book a strategy
              session with the SMS team.
            </p>
            <ul className="tier-features">
              {[
                'Everything in Free, always',
                'Deep personalised insights using your own data',
                'Upload Spotify for Artists, Too Lost, PRS, TikTok',
                "Downloadable Artist Insights Report — you choose what's in it",
                'Strategy consultation with Sound Metrics Studio team',
              ].map(f => (
                <li key={f} className="tier-feature">
                  <span className="tier-feature-check">✓</span>
                  {f}
                </li>
              ))}
            </ul>
            <button className="btn btn-primary btn-full" onClick={onSignUp}>
              Create free account
            </button>
          </div>
        </div>
      </section>

      {/* ── Steps ───────────────────────────────────────────────────────── */}
      <section id="landing-steps">
        <p className="section-eyebrow">The process</p>
        <h2 className="section-title">From search to strategy in minutes.</h2>
        <p className="section-sub" style={{ marginBottom: '40px' }}>
          No setup. No credit card. Start with a search.
        </p>

        <div className="steps-grid">
          {[
            {
              n: '1',
              title: 'Search your artist name',
              desc: 'Type any artist name and Artist Intelligence pulls live data from Chartmetric, Soundcharts, and YouTube — no account needed.',
              tier: 'free',
              label: 'Free',
            },
            {
              n: '2',
              title: 'Ask questions, explore the data',
              desc: 'Receive up to 3 AI-generated next steps for your career, then keep asking questions freely. Create a free account to save your results.',
              tier: 'free',
              label: 'Free',
            },
            {
              n: '3',
              title: 'Upload your private data',
              desc: 'Sign up and connect your Spotify for Artists exports, distributor statements, and royalty data. Your files are stored securely — only you can see them.',
              tier: 'pro',
              label: 'Pro account',
            },
            {
              n: '4',
              title: 'Download your Artist Insights Report',
              desc: 'Build a personalised report — choose which sections to include, download it, and book a strategy session with the Sound Metrics Studio team.',
              tier: 'pro',
              label: 'Pro account',
            },
          ].map(step => (
            <div key={step.n} className="step-card">
              <div className="step-number">{step.n}</div>
              <div className="step-title">{step.title}</div>
              <p className="step-desc">{step.desc}</p>
              <span className={`step-tier step-tier-${step.tier}`}>{step.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer id="landing-footer">
        <div className="footer-logo">
          <img src={logo} alt="Sound Metrics Studio" className="footer-logo-img" />
          <span className="footer-logo-text">Sound Metrics Studio</span>
        </div>
        <p style={{ fontSize: '13px', color: 'rgba(255,255,255,0.45)', fontStyle: 'italic' }}>
          Own your journey, the data was always yours.
        </p>
        <div className="footer-links">
          <a href="#">Privacy policy</a>
          <a href="#">Terms of use</a>
          <a href="#">Contact</a>
          <a href="https://soundmetricsstudio.com" target="_blank" rel="noopener noreferrer">
            soundmetricsstudio.com
          </a>
        </div>
      </footer>

    </div>
  )
}
