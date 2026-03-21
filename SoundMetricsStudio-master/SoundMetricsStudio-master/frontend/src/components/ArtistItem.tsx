import type { Artist } from '../types'

interface Props {
  artist: Artist
  onClick: (cmId: number) => void
}

export function ArtistItem({ artist, onClick }: Props) {
  const genres = Array.isArray(artist.genres)
    ? artist.genres.slice(0, 3).join(', ')
    : (artist.genres ?? '')

  return (
    <div className="artist-item" onClick={() => onClick(artist.cm_id)}>
      <img
        className="artist-avatar"
        src={artist.image_url ?? ''}
        onError={e => { (e.target as HTMLImageElement).src = '' }}
        alt=""
      />
      <div className="artist-info">
        <div className="artist-name">{artist.name}</div>
        <div className="artist-genres">{genres}</div>
      </div>
    </div>
  )
}
