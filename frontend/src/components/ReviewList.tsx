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
  if (!userId) return 'TasteMap Kullanıcısı'
  if (userId.length <= 10) return `Kullanıcı ${userId}`
  return `Kullanıcı ${userId.slice(0, 8)}…`
}

export function ReviewList({ reviews, featuredReview }: ReviewListProps): JSX.Element {
  const featuredValue = featuredReview?.trim() ? featuredReview.trim() : null
  const hasAnyReviews = reviews.length > 0

  if (!hasAnyReviews && !featuredValue) {
    return (
      <div className="rounded-[2rem] border border-slate-200 bg-white px-6 py-12 text-center shadow-sm">
        <div className="mx-auto inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-50 text-orange-600 shadow-sm">
          <MessageCircle size={24} />
        </div>
        <h3 className="mt-4 text-lg font-bold text-slate-900">Henüz Yorum Yapılmamış</h3>
        <p className="mt-1 text-xs text-slate-500 max-w-xs mx-auto">
          Bu mekan için ilk değerlendirmeyi ve deneyimi siz paylaşın!
        </p>
      </div>
    )
  }

  const items = hasAnyReviews
    ? reviews.map((review) => ({
      id: review.id,
      rating: review.rating,
      reviewer:
        review.source === 'google'
          ? (review.author_name?.trim() ? review.author_name.trim() : 'Google Kullanıcısı')
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
        reviewer: 'Öne Çıkan Değerlendirme',
        source: 'google' as const,
        relativeDate: null,
        text: featuredValue,
        isFeatured: true,
      },
    ]

  return (
    <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 text-slate-900">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-orange-50 text-orange-600">
            <MessageCircle size={18} />
          </div>
          <h3 className="text-lg font-bold">Müşteri Yorumları</h3>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          {items.length} yorum
        </span>
      </div>

      <div className="mt-4 max-h-[560px] overflow-y-auto pr-1 sm:max-h-[640px]">
        <ul className="space-y-3">
          {items.map((item) => (
            <li
              key={item.id}
              className="rounded-2xl border border-slate-100 bg-slate-50/60 p-4 transition duration-200 hover:bg-slate-50 hover:shadow-xs"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1">
                    <span className="text-xs font-bold text-slate-900">{item.reviewer}</span>
                    {item.relativeDate ? (
                      <span className="text-[11px] text-slate-400 font-medium">{item.relativeDate}</span>
                    ) : null}
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                        item.source === 'google'
                          ? 'bg-blue-50 text-blue-700'
                          : 'bg-emerald-50 text-emerald-700'
                      }`}
                    >
                      {item.source === 'google' ? 'Google' : 'TasteMap'}
                    </span>
                    {item.isFeatured ? (
                      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-bold text-amber-700">
                        Öne Çıkan
                      </span>
                    ) : null}
                  </div>

                  {item.text ? (
                    <p className="text-xs leading-5 text-slate-700">{item.text}</p>
                  ) : (
                    <p className="text-xs italic text-slate-400">Yorum metni belirtilmedi.</p>
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

