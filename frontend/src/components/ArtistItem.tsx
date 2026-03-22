import type { Artist } from '../types'

interface Props {
  artist: Artist
  onClick: (cmId: number) => void
}

export function ArtistItem({ artist, onClick }: Props) {
  const genres = Array.isArray(artist.genres)
    ? artist.genres.slice(0, 3)
    : artist.genres
      ? [artist.genres]
      : []

  const initial = artist.name.charAt(0).toUpperCase()

  return (
    <div className="artist-item" onClick={() => onClick(artist.cm_id)}>
      <div className="artist-avatar-wrap">
        {artist.image_url ? (
          <img
            className="artist-avatar"
            src={artist.image_url}
            onError={e => {
              const img = e.target as HTMLImageElement
              img.style.display = 'none'
              const fallback = img.nextElementSibling as HTMLElement
              if (fallback) fallback.style.display = 'flex'
            }}
            alt={artist.name}
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

      <span className="artist-arrow">›</span>
    </div>
  )
}
