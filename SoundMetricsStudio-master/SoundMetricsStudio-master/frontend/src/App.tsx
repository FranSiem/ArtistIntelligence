import { useState } from 'react'
import type { ArtistContext } from './types'
import { ChatPanel } from './components/ChatPanel'
import { ArtistPanel } from './components/ArtistPanel'

export default function App() {
  const [artistContext, setArtistContext] = useState<ArtistContext | null>(null)

  return (
    <div id="app">
      <ChatPanel artistContext={artistContext} onClearContext={() => setArtistContext(null)} />
      <ArtistPanel onArtistContext={setArtistContext} />
    </div>
  )
}
