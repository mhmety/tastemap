import { MessageCircle, Star } from 'lucide-react'
import type { JSX } from 'react'

import type { Review } from '../types/restaurant'

interface ReviewListProps {
  reviews: Review[]
  featuredReview?: string | null
}

function formatRelativeDate(dateValue: string | null | undefined): string | null {
  if (!dateValue) return null
  const date = new Date(dateValue)
  if (Number.isNaN(date.getTime())) return null
  const diffMs = date.getTime() - Date.now()

  const seconds = Math.round(diffMs / 1000)
  const minutes = Math.round(seconds / 60)
  const hours = Math.round(minutes / 60)
  const days = Math.round(hours / 24)

  const rtf = new Intl.RelativeTimeFormat('tr', { numeric: 'auto' })
  if (Math.abs(days) >= 1) return rtf.format(days, 'day')
  if (Math.abs(hours) >= 1) return rtf.format(hours, 'hour')
  if (Math.abs(minutes) >= 1) return rtf.format(minutes, 'minute')
  return rtf.format(seconds, 'second')
}

function StarsRow({ rating }: { rating: number }): JSX.Element {
  const safeRating = Math.max(0, Math.min(5, Math.round(rating)))
  return (
    <div className="flex items-center gap-1 text-amber-500">
      {Array.from({ length: 5 }).map((_, index) => (
        <Star
          key={`star-${index}`}
          size={16}
          className={index < safeRating ? 'fill-current' : 'text-slate-200'}
        />
      ))}
    </div>
  )
}

function formatReviewerLabel(userId: string | null | undefined): string {
  if (!userId) return 'Değerlendirici'
  if (userId.length <= 10) return `Kullanıcı ${userId}`
  return `Kullanıcı ${userId.slice(0, 8)}…`
}

export function ReviewList({ reviews, featuredReview }: ReviewListProps): JSX.Element {
  const featuredValue = featuredReview?.trim() ? featuredReview.trim() : null
  const hasAnyReviews = reviews.length > 0

  if (!hasAnyReviews && !featuredValue) {
    return (
      <div className="rounded-[1.5rem] border border-slate-100 bg-slate-50 px-6 py-12 text-center">
        <div className="mx-auto inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-white text-slate-400 shadow-sm">
          <MessageCircle size={20} />
        </div>
        <h3 className="mt-6 text-lg font-semibold text-slate-900">Yorum Henüz Yok</h3>
        <p className="mt-2 text-sm text-slate-600">Deneyimi paylaşın.</p>
      </div>
    )
  }

  const items = hasAnyReviews
    ? reviews.map((review) => ({
      id: review.id,
      rating: review.rating,
      reviewer:
        review.source === 'google'
          ? (review.author_name?.trim() ? review.author_name.trim() : 'Google yorumcusu')
          : formatReviewerLabel(review.user_id),
      source: review.source ?? 'user',
      relativeDate: formatRelativeDate(review.created_at),
      text: review.comment?.trim() ? review.comment.trim() : null,
      isFeatured: false,
    }))
    : [
      {
        id: 'featured',
        rating: null as number | null,
        reviewer: 'Öne Çıkan Yorum',
        source: 'google' as const,
        relativeDate: null,
        text: featuredValue,
        isFeatured: true,
      },
    ]

  return (
    <div className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2 text-slate-900">
        <MessageCircle size={18} />
        <h3 className="text-lg font-semibold">Yorumlar</h3>
      </div>
      <div className="mt-4 max-h-[560px] overflow-y-auto pr-1 sm:max-h-[640px]">
        <ul className="space-y-4">
          {items.map((item) => (
            <li
              key={item.id}
              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition duration-200 hover:-translate-y-0.5 hover:border-orange-200 hover:shadow-md"
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <span className="text-sm font-semibold text-slate-900">{item.reviewer}</span>
                    {item.relativeDate ? (
                      <span className="text-sm text-slate-500">{item.relativeDate}</span>
                    ) : null}
                    <span
                      className={
                        item.source === 'google'
                          ? 'rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700'
                          : 'rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700'
                      }
                    >
                      {item.source === 'google' ? 'Google' : 'Lezzet Haritası'}
                    </span>
                    {item.isFeatured ? (
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                        Öne Çıkarılmış
                      </span>
                    ) : null}
                  </div>
                  {item.text ? (
                    <p className="text-sm leading-6 text-slate-700">{item.text}</p>
                  ) : (
                    <p className="text-sm leading-6 text-slate-500">Yorum sağlanmadı.</p>
                  )}
                </div>

                {item.rating != null ? <StarsRow rating={item.rating} /> : null}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
