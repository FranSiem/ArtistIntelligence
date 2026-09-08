import type { Artist } from '../types'

interface Props {
  artist: Artist
  onClick: (cmId: number) => void
}

export function ArtistItem({ artist, onClick }: Props) {
  const initial = artist.name.charAt(0).toUpperCase()
  const genres = Array.isArray(artist.genres)
    ? artist.genres.slice(0, 3)
    : typeof artist.genres === 'string'
      ? [artist.genres]
      : []

  return (
    <div
      className="artist-item"
      onClick={() => onClick(artist.cm_id)}
      role="button"
      tabIndex={0}
      onKeyDown={e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onClick(artist.cm_id)
        }
      }}
      aria-label={`Select ${artist.name}`}
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
              const fallback = img.nextElementSibling as HTMLElement
              if (fallback) fallback.style.display = 'flex'
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
              <span key={g} className="genre-chip">{g}</span>
            ))}
          </div>
        )}
      </div>

      <span className="artist-arrow" aria-hidden="true">›</span>
    </div>
  )
}
