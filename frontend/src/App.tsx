import { useState } from 'react'
import type { Artist, ArtistContext } from './types'
import { ChatPanel } from './components/ChatPanel'
import { ArtistPanel } from './components/ArtistPanel'
import { LandingPage } from './components/LandingPage'
import logo from './assets/logo.png'

export default function App() {
  const [artistContext, setArtistContext] = useState<ArtistContext | null>(null)
  const [activeTab, setActiveTab] = useState<'artist' | 'chat'>('artist')
  const [selectedArtist, setSelectedArtist] = useState<Artist | null>(null)

  if (!selectedArtist) {
    return <LandingPage onSelectArtist={(artist) => setSelectedArtist(artist)} />
  }

  return (
    <div id="app-shell">
      <nav id="nav-bar">
        <div className="nav-logo" style={{ cursor: 'pointer' }} onClick={() => setSelectedArtist(null)}>
          <img src={logo} alt="SoundMetrics Studio" className="nav-logo-img" />
          <span className="nav-tagline">AI-powered music analytics</span>
        </div>
      </nav>

      <div id="mobile-tabs">
        <button
          className={`mobile-tab ${activeTab === 'artist' ? 'active' : ''}`}
          onClick={() => setActiveTab('artist')}
        >
          🎤 Artist
        </button>
        <button
          className={`mobile-tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          💬 Chat
        </button>
      </div>

      <div id="app-grid">
        <div className={`panel-wrapper ${activeTab === 'artist' ? 'tab-active' : ''}`}>
          <ArtistPanel
            onArtistContext={(ctx) => { setArtistContext(ctx); setActiveTab('chat') }}
            initialArtist={selectedArtist}
          />
        </div>
        <div className={`panel-wrapper ${activeTab === 'chat' ? 'tab-active' : ''}`}>
          <ChatPanel artistContext={artistContext} onClearContext={() => setArtistContext(null)} />
        </div>
      </div>
    </div>
  )
}
