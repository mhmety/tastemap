import { Check, Edit2, MessageCircle, Star, Trash2, X } from 'lucide-react'
import type { JSX } from 'react'
import { useState } from 'react'

import { useAuth } from '../hooks/useAuth'
import type { Review } from '../types/restaurant'

interface ReviewListProps {
  reviews: Review[]
  featuredReview?: string | null
  onEditReview?: (reviewId: string, rating: number, comment: string | null) => Promise<void>
  onDeleteReview?: (reviewId: string) => Promise<void>
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

function formatReviewerLabel(authorName: string | null | undefined, source: string): string {
  if (authorName && authorName.trim()) {
    return authorName.trim()
  }
  if (source === 'google') {
    return 'Google Kullanıcısı'
  }
  return 'Kullanıcı'
}

export function ReviewList({
  reviews,
  featuredReview,
  onEditReview,
  onDeleteReview,
}: ReviewListProps): JSX.Element {
  const { user } = useAuth()
  const featuredValue = featuredReview?.trim() ? featuredReview.trim() : null
  const hasAnyReviews = reviews.length > 0

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editRating, setEditRating] = useState<number>(5)
  const [editHoverRating, setEditHoverRating] = useState<number>(0)
  const [editComment, setEditComment] = useState<string>('')
  const [isSubmittingEdit, setIsSubmittingEdit] = useState<boolean>(false)
  const [editError, setEditError] = useState<string | null>(null)

  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState<boolean>(false)

  const startEdit = (review: Review): void => {
    setEditingId(review.id)
    setEditRating(review.rating)
    setEditHoverRating(0)
    setEditComment(review.comment ?? '')
    setEditError(null)
    setConfirmDeleteId(null)
  }

  const cancelEdit = (): void => {
    setEditingId(null)
    setEditError(null)
  }

  const handleSaveEdit = async (reviewId: string): Promise<void> => {
    if (!onEditReview) return
    if (editRating < 1 || editRating > 5) return

    setIsSubmittingEdit(true)
    setEditError(null)
    try {
      await onEditReview(reviewId, editRating, editComment.trim() ? editComment.trim() : null)
      setEditingId(null)
    } catch {
      setEditError('Yorum güncellenirken bir hata oluştu.')
    } finally {
      setIsSubmittingEdit(false)
    }
  }

  const handleDelete = async (reviewId: string): Promise<void> => {
    if (!onDeleteReview) return
    setIsDeleting(true)
    try {
      await onDeleteReview(reviewId)
      setConfirmDeleteId(null)
    } catch {
      // Hata durumunda onay kutusu açık kalabilir
    } finally {
      setIsDeleting(false)
    }
  }

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
          {reviews.length || (featuredValue ? 1 : 0)} yorum
        </span>
      </div>

      <div className="mt-4 max-h-[560px] overflow-y-auto pr-1 sm:max-h-[640px]">
        {hasAnyReviews ? (
          <ul className="space-y-3">
            {reviews.map((review) => {
              const isOwner = Boolean(user?.id && review.user_id && user.id === review.user_id)
              const isEditingThis = editingId === review.id
              const isConfirmingDelete = confirmDeleteId === review.id
              const reviewerName = formatReviewerLabel(review.author_name, review.source ?? 'user')
              const relativeDate = formatRelativeDate(review.created_at)
              const starsValue = editHoverRating > 0 ? editHoverRating : editRating

              if (isEditingThis) {
                return (
                  <li
                    key={review.id}
                    className="rounded-2xl border-2 border-orange-200 bg-orange-50/30 p-5 shadow-xs transition animate-in fade-in"
                  >
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-800">Yorumunuzu Düzenleyin</span>
                        <div className="flex items-center gap-1">
                          {Array.from({ length: 5 }).map((_, index) => {
                            const value = index + 1
                            const isActive = value <= starsValue
                            return (
                              <button
                                key={`edit-star-${value}`}
                                type="button"
                                className="p-0.5 text-amber-500 transition hover:scale-110"
                                onMouseEnter={() => setEditHoverRating(value)}
                                onMouseLeave={() => setEditHoverRating(0)}
                                onClick={() => setEditRating(value)}
                                disabled={isSubmittingEdit}
                              >
                                <Star size={20} className={isActive ? 'fill-current' : 'text-slate-300'} />
                              </button>
                            )
                          })}
                        </div>
                      </div>

                      <textarea
                        className="w-full resize-none rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-800 shadow-inner outline-none transition focus:border-orange-400 focus:ring-2 focus:ring-orange-100"
                        rows={3}
                        value={editComment}
                        maxLength={1000}
                        onChange={(e) => setEditComment(e.target.value)}
                        disabled={isSubmittingEdit}
                        placeholder="Yorumunuzu güncelleyin..."
                      />

                      {editError ? (
                        <p className="text-xs font-semibold text-rose-600">{editError}</p>
                      ) : null}

                      <div className="flex items-center justify-end gap-2 pt-1">
                        <button
                          type="button"
                          onClick={cancelEdit}
                          disabled={isSubmittingEdit}
                          className="inline-flex items-center gap-1 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                        >
                          <X size={14} />
                          İptal
                        </button>
                        <button
                          type="button"
                          onClick={() => void handleSaveEdit(review.id)}
                          disabled={isSubmittingEdit}
                          className="inline-flex items-center gap-1 rounded-full bg-orange-500 px-4 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-orange-600 disabled:bg-orange-300"
                        >
                          <Check size={14} />
                          {isSubmittingEdit ? 'Kaydediliyor...' : 'Kaydet'}
                        </button>
                      </div>
                    </div>
                  </li>
                )
              }

              return (
                <li
                  key={review.id}
                  className="rounded-2xl border border-slate-100 bg-slate-50/60 p-4 transition duration-200 hover:bg-slate-50 hover:shadow-xs"
                >
                  <div className="flex flex-col gap-3">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="space-y-1.5 flex-1">
                        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1">
                          <span className="text-xs font-bold text-slate-900">{reviewerName}</span>
                          {relativeDate ? (
                            <span className="text-[11px] text-slate-400 font-medium">{relativeDate}</span>
                          ) : null}
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                              review.source === 'google'
                                ? 'bg-blue-50 text-blue-700'
                                : 'bg-emerald-50 text-emerald-700'
                            }`}
                          >
                            {review.source === 'google' ? 'Google' : 'TasteMap'}
                          </span>
                          {isOwner ? (
                            <span className="rounded-full bg-orange-100 px-2 py-0.5 text-[10px] font-bold text-orange-800">
                              Sizin Yorumunuz
                            </span>
                          ) : null}
                        </div>

                        {review.comment ? (
                          <p className="text-xs leading-5 text-slate-700">{review.comment}</p>
                        ) : (
                          <p className="text-xs italic text-slate-400">Yorum metni belirtilmedi.</p>
                        )}
                      </div>

                      <div className="flex items-center gap-3 self-start sm:self-auto">
                        <StarsRow rating={review.rating} />
                      </div>
                    </div>

                    {/* Sahip İşlem Butonları (Düzenle / Sil) */}
                    {isOwner ? (
                      <div className="border-t border-slate-100 pt-2.5 mt-1 flex items-center justify-between">
                        {isConfirmingDelete ? (
                          <div className="flex w-full items-center justify-between rounded-xl bg-rose-50 px-3 py-2 text-xs animate-in fade-in">
                            <span className="font-semibold text-rose-800">Yorumu silmek istiyor musunuz?</span>
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                onClick={() => setConfirmDeleteId(null)}
                                disabled={isDeleting}
                                className="rounded-md bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600 border border-slate-200 hover:bg-slate-50"
                              >
                                Vazgeç
                              </button>
                              <button
                                type="button"
                                onClick={() => void handleDelete(review.id)}
                                disabled={isDeleting}
                                className="rounded-md bg-rose-600 px-2.5 py-1 text-[11px] font-bold text-white hover:bg-rose-700 disabled:bg-rose-300"
                              >
                                {isDeleting ? 'Siliniyor...' : 'Evet, Sil'}
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 ml-auto">
                            <button
                              type="button"
                              onClick={() => startEdit(review)}
                              className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1 text-[11px] font-bold text-slate-600 border border-slate-200 hover:border-orange-300 hover:text-orange-600 transition"
                            >
                              <Edit2 size={12} />
                              Düzenle
                            </button>
                            <button
                              type="button"
                              onClick={() => setConfirmDeleteId(review.id)}
                              className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1 text-[11px] font-bold text-slate-600 border border-slate-200 hover:border-rose-300 hover:text-rose-600 transition"
                            >
                              <Trash2 size={12} />
                              Sil
                            </button>
                          </div>
                        )}
                      </div>
                    ) : null}
                  </div>
                </li>
              )
            })}
          </ul>
        ) : featuredValue ? (
          <div className="rounded-2xl border border-slate-100 bg-slate-50/60 p-4">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-bold text-slate-900">Öne Çıkan Değerlendirme</span>
              <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-bold text-amber-700">
                Google
              </span>
            </div>
            <p className="mt-2 text-xs leading-5 text-slate-700">{featuredValue}</p>
          </div>
        ) : null}
      </div>
    </div>
  )
}


