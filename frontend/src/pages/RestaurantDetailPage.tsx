import axios from 'axios'
import { ArrowLeft, Clock, MapPin, Star, Tag } from 'lucide-react'
import type { JSX } from 'react'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'

import { createRestaurantReview, deleteReview, updateReview } from '../api/reviews'
import { ContactChips } from '../components/ContactChips'
import { ErrorMessage } from '../components/ErrorMessage'
import { FavoriteButton } from '../components/FavoriteButton'
import { Loading } from '../components/Loading'
import { MenuList } from '../components/MenuList'
import { OperatingHoursModal } from '../components/OperatingHoursModal'
import { RestaurantPhotoCarousel } from '../components/RestaurantPhotoCarousel'
import { ReviewList } from '../components/ReviewList'
import { useAuth } from '../hooks/useAuth'
import { useFavorites } from '../hooks/useFavorites'
import { usePageTitle } from '../hooks/usePageTitle'
import { useRestaurantDetail } from '../hooks/useRestaurantDetail'
import { normalizeApiErrorMessage } from '../utils/apiError'
import { formatCategoryTr, formatOpeningHoursTr } from '../utils/localization'

function buildTelUrl(phone: string): string {
  const digitsOnly = phone.replace(/[^\d]/g, '')
  if (digitsOnly.length === 0) {
    return 'tel:'
  }

  if (digitsOnly.startsWith('90')) {
    return `tel:+${digitsOnly}`
  }

  if (digitsOnly.startsWith('0')) {
    return `tel:+90${digitsOnly.slice(1)}`
  }

  if (digitsOnly.length === 10) {
    return `tel:+90${digitsOnly}`
  }

  return `tel:+${digitsOnly}`
}

function buildGoogleMapsUrl(
  name: string,
  city: string,
  latitude: number | null,
  longitude: number | null,
): string {
  if (latitude !== null && longitude !== null) {
    const query = encodeURIComponent(`${latitude},${longitude}`)
    return `https://www.google.com/maps/search/?api=1&query=${query}`
  }

  const query = encodeURIComponent(`${name} ${city}`)
  return `https://www.google.com/maps/search/?api=1&query=${query}`
}

export function RestaurantDetailPage(): JSX.Element {
  const { id } = useParams<{ id: string }>()
  const { restaurant, isLoading, error, refetch, applyReviewCreated } = useRestaurantDetail(id)
  const location = useLocation()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const favorites = useFavorites()
  const reviewsRef = useRef<HTMLDivElement | null>(null)

  const [selectedRating, setSelectedRating] = useState<number>(0)
  const [hoverRating, setHoverRating] = useState<number>(0)
  const [comment, setComment] = useState<string>('')
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false)
  const [reviewError, setReviewError] = useState<string | null>(null)
  const [toastMessage, setToastMessage] = useState<string | null>(null)
  const [isHoursModalOpen, setIsHoursModalOpen] = useState<boolean>(false)

  const backTo = useMemo(() => {
    const state = location.state as { from?: string } | null
    if (state?.from && typeof state.from === 'string') return state.from
    return '/'
  }, [location.state])

  useEffect(() => {
    if (!toastMessage) return
    const timeout = window.setTimeout(() => setToastMessage(null), 2500)
    return () => window.clearTimeout(timeout)
  }, [toastMessage])

  const starsDisplayValue = hoverRating > 0 ? hoverRating : selectedRating

  const canSubmitReview = useMemo(
    () => selectedRating >= 1 && selectedRating <= 5 && !isSubmittingReview,
    [selectedRating, isSubmittingReview],
  )

  const submitReview = useCallback(async () => {
    if (!id) return
    if (!isAuthenticated) {
      setReviewError('Yorum yapabilmek için lütfen giriş yapın.')
      return
    }
    if (selectedRating < 1 || selectedRating > 5) return

    setIsSubmittingReview(true)
    setReviewError(null)
    try {
      const created = await createRestaurantReview(id, {
        rating: selectedRating,
        comment: comment.trim() ? comment.trim() : null,
      })

      applyReviewCreated({
        id: created.id,
        user_id: created.user_id,
        rating: created.rating,
        comment: created.comment,
        author_name: created.author_name,
        profile_photo: created.profile_photo,
        likes: created.likes,
        source: created.source,
        created_at: created.created_at,
        updated_at: created.updated_at,
      })

      setSelectedRating(0)
      setHoverRating(0)
      setComment('')
      setToastMessage('Yorumunuz başarıyla kaydedildi.')
      await refetch()
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        const status = error.response?.status
        if (status === 401) {
          setReviewError('Yorum yapmak için giriş yapmalısınız.')
        } else if (status === 409) {
          setReviewError('Bu restorana daha önce yorum yaptınız.')
        } else {
          setReviewError(
            normalizeApiErrorMessage(error, 'Yorum gönderilirken bir hata oluştu.')
          )
        }
      } else {
        setReviewError('Yorum gönderilirken bir hata oluştu.')
      }
    } finally {
      setIsSubmittingReview(false)
    }
  }, [applyReviewCreated, comment, id, isAuthenticated, refetch, selectedRating])

  const handleEditReview = useCallback(
    async (reviewId: string, rating: number, comment: string | null): Promise<void> => {
      await updateReview(reviewId, { rating, comment })
      setToastMessage('Yorumunuz başarıyla güncellendi.')
      await refetch()
    },
    [refetch],
  )

  const handleDeleteReview = useCallback(
    async (reviewId: string): Promise<void> => {
      await deleteReview(reviewId)
      setToastMessage('Yorumunuz başarıyla silindi.')
      await refetch()
    },
    [refetch],
  )


  usePageTitle(restaurant ? restaurant.name : 'Restoran Detayı')

  const handleToggleFavorite = (restaurantId: string): void => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }

    void favorites.toggleFavorite(restaurantId)
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
        <Loading label="Restoran detayları yükleniyor..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link
            to={backTo}
            className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 transition hover:text-orange-600"
          >
            <ArrowLeft size={16} />
            Restoranlara Dön
          </Link>
        </div>
        <ErrorMessage message={error} onRetry={() => void refetch()} />
      </div>
    )
  }

  if (!restaurant) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="rounded-[2rem] border border-slate-200 bg-white px-6 py-12 text-center shadow-sm">
          <h1 className="text-2xl font-bold text-slate-900">Restoran bulunamadı</h1>
          <p className="mt-2 text-sm text-slate-600">
            Aradığınız restoran bulunamadı veya sistemden kaldırılmış olabilir.
          </p>
          <Link
            to="/"
            className="mt-6 inline-flex items-center justify-center rounded-full bg-orange-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-orange-600"
          >
            Restoranları Keşfet
          </Link>
        </div>
      </div>
    )
  }

  const ratingValue = restaurant.rating ?? restaurant.average_rating
  const ratingText = ratingValue == null ? 'Değerlendirilmedi' : ratingValue.toFixed(1)
  const reviewCountText = restaurant.review_count == null ? null : restaurant.review_count.toLocaleString('tr-TR')

  const phoneValue = restaurant.phone?.trim() ? restaurant.phone.trim() : null
  const categoryValue = formatCategoryTr(restaurant.category)
  const priceValue = restaurant.price_level?.trim() ? restaurant.price_level.trim() : null
  const rawOpeningHours = restaurant.opening_hours?.trim() ? restaurant.opening_hours.trim() : null
  const openingHoursValue = formatOpeningHoursTr(rawOpeningHours)
  const descriptionValue = restaurant.description?.trim() ? restaurant.description.trim() : null

  const operatingHours = (() => {
    if (!restaurant.operating_hours) return null
    if (typeof restaurant.operating_hours !== 'object') return null
    if (Array.isArray(restaurant.operating_hours)) return null
    return restaurant.operating_hours as Record<string, unknown>
  })()

  const operatingHoursOrder: Array<{ key: string; label: string }> = [
    { key: 'monday', label: 'Pazartesi' },
    { key: 'tuesday', label: 'Salı' },
    { key: 'wednesday', label: 'Çarşamba' },
    { key: 'thursday', label: 'Perşembe' },
    { key: 'friday', label: 'Cuma' },
    { key: 'saturday', label: 'Cumartesi' },
    { key: 'sunday', label: 'Pazar' },
  ]

  const operatingHoursRows = (() => {
    if (!operatingHours) return null
    const rows = operatingHoursOrder
      .map(({ key, label }) => {
        const value = operatingHours[key]
        if (typeof value !== 'string') return { key, label, value: null }
        const trimmed = value.trim()
        return { key, label, value: trimmed.length > 0 ? trimmed : null }
      })
      .filter((row): row is { key: string; label: string; value: string } => row.value !== null)

    return rows.length > 0 ? rows : null
  })()

  const todayKey = (() => {
    const dayIndex = new Date().getDay()
    const keys = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'] as const
    return keys[dayIndex] ?? 'monday'
  })()

  const isOpen = (() => {
    if (!rawOpeningHours) return null
    const lowered = rawOpeningHours.toLowerCase()
    if (lowered.startsWith('open')) return true
    if (lowered.startsWith('closed')) return false
    return null
  })()

  const websiteUrl = restaurant.website?.trim() ? restaurant.website.trim() : null

  const googleMapsUrl = buildGoogleMapsUrl(
    restaurant.name,
    restaurant.city,
    restaurant.latitude,
    restaurant.longitude,
  )

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      {toastMessage ? (
        <div className="fixed bottom-6 right-6 z-50 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-800 shadow-xl animate-in slide-in-from-bottom-2">
          {toastMessage}
        </div>
      ) : null}

      <div className="mb-6">
        <Link
          to={backTo}
          className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 transition hover:text-orange-600"
        >
          <ArrowLeft size={16} />
          Restoranlara Dön
        </Link>
      </div>

      {/* Restoran Başlık Kartı */}
      <section className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
        <div className="relative">
          <FavoriteButton
            restaurantId={restaurant.id}
            isFavorite={favorites.isFavorite(restaurant.id)}
            loading={favorites.isUpdating(restaurant.id)}
            onToggle={handleToggleFavorite}
            className="absolute right-0 top-0 inline-flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:border-red-200 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-60"
          />

          <div className="grid gap-6 pr-12 lg:grid-cols-[320px_1fr]">
            <RestaurantPhotoCarousel
              name={restaurant.name}
              thumbnail={restaurant.thumbnail}
              photos={restaurant.photos}
            />

            <div className="space-y-4">
              <div className="space-y-2">
                <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
                  {restaurant.name}
                </h1>

                <div className="flex flex-wrap items-center gap-2 text-sm text-slate-700">
                  {categoryValue ? (
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700">
                      <Tag size={14} className="text-slate-500" />
                      {categoryValue}
                    </span>
                  ) : null}

                  {priceValue ? (
                    <span className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700">
                      {priceValue}
                    </span>
                  ) : null}

                  {openingHoursValue ? (
                    <button
                      type="button"
                      onClick={() => operatingHoursRows && setIsHoursModalOpen(true)}
                      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold transition ${
                        operatingHoursRows
                          ? 'cursor-pointer bg-slate-100 hover:bg-orange-50 hover:text-orange-700 active:scale-95'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                      title={operatingHoursRows ? 'Haftalık çalışma saatlerini görmek için tıklayın' : undefined}
                    >
                      <Clock
                        size={14}
                        className={
                          isOpen === true
                            ? 'text-emerald-600'
                            : isOpen === false
                              ? 'text-rose-600'
                              : 'text-slate-500'
                        }
                      />
                      <span className="line-clamp-1">{openingHoursValue}</span>
                      {operatingHoursRows ? (
                        <span className="text-[10px] text-slate-400 font-normal">▼</span>
                      ) : null}
                    </button>
                  ) : null}
                </div>
              </div>

              {/* Yorumlar ve Puan Butonu */}
              <button
                type="button"
                aria-label="Yorumlara git"
                className="group flex w-full cursor-pointer flex-col gap-1 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-left transition duration-200 hover:-translate-y-0.5 hover:border-orange-200 hover:shadow-sm active:translate-y-0"
                onClick={() => reviewsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
              >
                <div className="flex items-center gap-2 text-sm font-bold text-slate-800">
                  <Star size={18} className="fill-current text-amber-500" />
                  <span>{ratingText} / 5</span>
                </div>
                <div className="text-xs font-medium text-slate-500 group-hover:text-orange-600 transition">
                  {reviewCountText ? `${reviewCountText} değerlendirme · Yorumları görüntüle` : 'Yorumları görüntüle'}
                </div>
              </button>

              {/* Konum ve Google Maps Bağlantısı */}
              <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
                    <MapPin size={18} className="text-slate-500" />
                    <span className="truncate">
                      {restaurant.district} · {restaurant.city}
                    </span>
                  </div>
                  <a
                    href={googleMapsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`${restaurant.name} Google Haritalar'da Aç`}
                    className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-[#4285F4]/30 bg-white text-[#4285F4] transition duration-200 hover:-translate-y-0.5 hover:border-[#4285F4]/60 hover:bg-[#4285F4]/5 hover:shadow-sm active:translate-y-0"
                    title="Google Haritalar'da Aç"
                  >
                    <MapPin size={18} />
                  </a>
                </div>
              </div>

              {descriptionValue ? (
                <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                  <div className="text-xs font-bold uppercase tracking-wide text-slate-400">
                    Açıklama
                  </div>
                  <p className="mt-1.5 text-sm leading-6 text-slate-700">{descriptionValue}</p>
                </div>
              ) : null}

              <ContactChips
                websiteUrl={websiteUrl}
                phoneLabel={phoneValue}
                phoneHref={phoneValue ? buildTelUrl(phoneValue) : null}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Menü ve Yorumlar Bölümü */}
      <section className="mt-8 grid gap-8 lg:grid-cols-2 auto-rows-[minmax(0,1fr)]">
        <div className="h-0 min-h-full">
          <MenuList items={restaurant.menu_items} />
        </div>
        <div ref={reviewsRef} className="min-h-0 space-y-6">
          {/* Yorum Yap Kartı */}
          <div className="rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm">
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-slate-900">Yorum Yap</h3>
              <p className="text-xs text-slate-500">Restoran ve lezzet deneyiminizi paylaşın</p>
            </div>

            <div className="mt-4 flex items-center gap-2">
              {Array.from({ length: 5 }).map((_, index) => {
                const value = index + 1
                const isActive = value <= starsDisplayValue
                return (
                  <button
                    key={`review-star-${value}`}
                    type="button"
                    className="rounded-lg p-1 text-amber-500 transition hover:scale-110 active:scale-95"
                    aria-label={`${value} Yıldız`}
                    onMouseEnter={() => setHoverRating(value)}
                    onMouseLeave={() => setHoverRating(0)}
                    onClick={() => setSelectedRating(value)}
                    disabled={isSubmittingReview}
                  >
                    <Star size={24} className={isActive ? 'fill-current' : 'text-slate-200'} />
                  </button>
                )
              })}
            </div>

            <textarea
              className="mt-4 h-28 w-full resize-none rounded-2xl border border-slate-200 bg-slate-50/50 px-4 py-3 text-sm text-slate-800 shadow-inner outline-none transition focus:border-orange-400 focus:bg-white focus:ring-2 focus:ring-orange-100"
              placeholder="Yemekler, servis ve atmosfer nasıldı? Görüşlerinizi yazın..."
              value={comment}
              maxLength={1000}
              onChange={(event) => setComment(event.target.value)}
              disabled={isSubmittingReview}
            />

            {reviewError ? (
              <div className="mt-3 rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-600 whitespace-pre-wrap">
                {reviewError}
              </div>
            ) : null}

            <div className="mt-4 flex items-center justify-end">
              <button
                type="button"
                onClick={() => void submitReview()}
                disabled={!canSubmitReview}
                className="inline-flex items-center justify-center rounded-full bg-orange-500 px-6 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:bg-slate-200 disabled:text-slate-500"
              >
                {isSubmittingReview ? 'Gönderiliyor...' : 'Yorumu Gönder'}
              </button>
            </div>
          </div>

          <ReviewList
            reviews={restaurant.reviews}
            featuredReview={restaurant.user_review}
            onEditReview={handleEditReview}
            onDeleteReview={handleDeleteReview}
          />
        </div>
      </section>


      {/* Çalışma Saatleri Modalı */}
      {operatingHoursRows ? (
        <OperatingHoursModal
          isOpen={isHoursModalOpen}
          onClose={() => setIsHoursModalOpen(false)}
          restaurantName={restaurant.name}
          rows={operatingHoursRows}
          todayKey={todayKey}
        />
      ) : null}
    </div>
  )
}

