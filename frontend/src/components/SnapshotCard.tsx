interface Props {
  text: string
  isStreaming: boolean
  artistName: string
}

export function SnapshotCard({ text, isStreaming, artistName }: Props) {
  return (
    <div className="snapshot-card">
      <div className="snapshot-card-label">
        {artistName} — Artist Snapshot
      </div>
      <div className="snapshot-card-text">
        {text}
        {isStreaming && <span className="streaming-cursor" />}
      </div>
    </div>
  )
}
