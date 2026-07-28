import type { JSX } from 'react'
import { MessageCircle } from 'lucide-react'

import type { Review } from '../types/restaurant'
import { RatingBadge } from './RatingBadge'

interface ReviewListProps {
  reviews: Review[]
}

export function ReviewList({ reviews }: ReviewListProps): JSX.Element {
  if (reviews.length === 0) {
    return (
      <div className="rounded-[1.5rem] border border-slate-200 bg-white px-6 py-10 text-center shadow-sm">
        <h3 className="text-lg font-semibold text-slate-900">No reviews yet</h3>
        <p className="mt-2 text-sm text-slate-600">Be the first to leave feedback for this restaurant.</p>
      </div>
    )
  }

  return (
    <div className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2 text-slate-900">
        <MessageCircle size={18} />
        <h3 className="text-lg font-semibold">Reviews</h3>
      </div>
      <ul className="mt-4 space-y-4">
        {reviews.map((review) => (
          <li key={review.id} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="space-y-1">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  User: {review.user_id}
                </p>
                {review.comment ? (
                  <p className="text-sm leading-6 text-slate-700">{review.comment}</p>
                ) : (
                  <p className="text-sm leading-6 text-slate-500">No comment provided.</p>
                )}
              </div>
              <RatingBadge rating={review.rating} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
