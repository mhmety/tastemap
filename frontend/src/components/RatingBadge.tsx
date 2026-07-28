import type { JSX } from 'react'
import { Star } from 'lucide-react'

interface RatingBadgeProps {
  rating: number | null
}

function formatRating(rating: number | null): string {
  return rating === null ? 'Unrated' : `${rating.toFixed(1)}/5`
}

export function RatingBadge({ rating }: RatingBadgeProps): JSX.Element {
  return (
    <div className="inline-flex min-w-[92px] items-center justify-center gap-2 whitespace-nowrap rounded-full bg-orange-50 px-3 py-1 text-sm font-medium text-orange-700">
      <Star size={16} className="fill-current" />
      <span>{formatRating(rating)}</span>
    </div>
  )
}
