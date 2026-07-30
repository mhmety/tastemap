import type { JSX } from 'react'
import { Heart } from 'lucide-react'

interface FavoriteButtonProps {
  restaurantId: string
  isFavorite: boolean
  loading: boolean
  onToggle: (restaurantId: string) => void
  className?: string
}

export function FavoriteButton({
  restaurantId,
  isFavorite,
  loading,
  onToggle,
  className,
}: FavoriteButtonProps): JSX.Element {
  return (
    <button
      type="button"
      aria-label={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
      className={
        className ??
        'inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 transition hover:border-red-200 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-60'
      }
      disabled={loading}
      onClick={() => onToggle(restaurantId)}
    >
      <Heart
        size={18}
        className={isFavorite ? 'fill-red-600 text-red-600' : 'text-slate-500'}
      />
    </button>
  )
}
