import { useState, useEffect } from 'react'
import type { Page, Artist, ArtistContext } from './types'
import { LandingPage } from './components/LandingPage'
import { SignInPage } from './components/SignInPage'
import { SignUpPage } from './components/SignUpPage'
import { DataSourcesPanel } from './components/DataSourcesPanel'
import { ConversationPanel } from './components/ConversationPanel'
import { ReportBuilderPanel } from './components/ReportBuilderPanel'
import logo from './assets/Sound Metrics Studio-Final-01.png'
import { AccessGate } from './components/AccessGate'

const STORAGE_KEY = 'ai_access_granted'

export default function App() {
  const [accessGranted, setAccessGranted] = useState(
    () => localStorage.getItem(STORAGE_KEY) === '1'
  )
  const [page, setPage] = useState<Page>('landing')
  const [selectedArtist, setSelectedArtist] = useState<Artist | null>(null)
  const [artistContext, setArtistContext] = useState<ArtistContext | null>(null)
  
  if (!accessGranted) {
    return <AccessGate onGranted={() => setAccessGranted(true)} />
  }

  // ── Back button — push a history entry on navigation so the browser
  // back button returns to landing instead of exiting the app entirely
  useEffect(() => {
    function handlePopState() {
      goToLanding()
    }
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  // ── Navigation helpers ─────────────────────────────────────────────────────
  function goToLanding() {
    setPage('landing')
    setSelectedArtist(null)
    setArtistContext(null)
  }

  function handleSelectArtist(artist: Artist) {
    setSelectedArtist(artist)
    setArtistContext(null)
    setPage('conversation')
    // Push a history entry so the browser back button has somewhere to go
    window.history.pushState({ page: 'conversation' }, '')
  }

  function handleArtistContext(ctx: ArtistContext) {
    setArtistContext(ctx)
  }

  // ── Shared nav bar (used on conversation page) ─────────────────────────────
  const AppNav = () => (
    <nav id="nav-bar">
      <div className="nav-left" onClick={goToLanding}>
        <img src={logo} alt="Sound Metrics Studio" className="nav-logo-img" />
        <div className="nav-wordmark">
          <span className="nav-wordmark-title">Artist Intelligence</span>
          <span className="nav-wordmark-sub">Powered by Sound Metrics Studio</span>
        </div>
      </div>
      <div className="nav-right">
        {selectedArtist && (
          <span className="nav-artist-name">{selectedArtist.name}</span>
        )}
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => setPage('signin')}
        >
          Sign in
        </button>
        <button
          className="btn btn-primary btn-sm"
          onClick={() => setPage('signup')}
        >
          Get started free
        </button>
      </div>
    </nav>
  )

  // ── Page routing ───────────────────────────────────────────────────────────
  if (page === 'landing') {
    return (
      <LandingPage
        onSelectArtist={handleSelectArtist}
        onSignIn={() => setPage('signin')}
        onSignUp={() => setPage('signup')}
      />
    )
  }

  if (page === 'signin') {
    return (
      <SignInPage
        onBack={goToLanding}
        onSwitchToSignUp={() => setPage('signup')}
        onSignIn={() => setPage('landing')}
      />
    )
  }

  if (page === 'signup') {
    return (
      <SignUpPage
        onBack={goToLanding}
        onSwitchToSignIn={() => setPage('signin')}
        onSignUp={() => setPage('landing')}
      />
    )
  }

  // ── Conversation page (three-panel) ───────────────────────────────────────
  return (
    <div id="app-shell">
      <AppNav />
      <div id="app-body">
        <DataSourcesPanel />
        <ConversationPanel
          artist={selectedArtist}
          onArtistContext={handleArtistContext}
        />
        <ReportBuilderPanel artistContext={artistContext} />
      </div>
    </div>
  )
}

