export interface Message { role: 'user' | 'assistant'; content: string }
export interface ArtistContext { name: string; analysis: string }
export interface Artist { cm_id: number; name: string; image_url: string | null; genres: string[] | null }
export type AnalysisEvent =
  | { type: 'status'; text: string }
  | { type: 'token'; text: string }
  | { type: 'done'; artist_name: string }
  | { type: 'error'; text: string }
