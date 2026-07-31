import { ArrowLeft, Clock, Globe, MapPin, Phone, Star, Utensils } from 'lucide-react'
import type { JSX } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ErrorMessage } from '../components/ErrorMessage'
import { FavoriteButton } from '../components/FavoriteButton'
import { Loading } from '../components/Loading'
import { MenuList } from '../components/MenuList'
import { RatingBadge } from '../components/RatingBadge'
import { RestaurantActions } from '../components/RestaurantActions'
import { ReviewList } from '../components/ReviewList'
import { useAuth } from '../hooks/useAuth'
import { useFavorites } from '../hooks/useFavorites'
import { usePageTitle } from '../hooks/usePageTitle'
import { useRestaurantDetail } from '../hooks/useRestaurantDetail'

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

export function RestaurantDetailPage(): JSX.Element {
  const { id } = useParams<{ id: string }>()
  const { restaurant, isLoading, error, refetch } = useRestaurantDetail(id)
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const favorites = useFavorites()

  usePageTitle(restaurant ? restaurant.name : 'Restaurant Details')

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
        <Loading label="Loading restaurant details..." />
      </div>
    )
  }

  if (error) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="mb-6">
          <Link
            to="/restaurants"
            className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 transition hover:text-orange-600"
          >
            <ArrowLeft size={16} />
            Back to restaurants
          </Link>
        </div>
        <ErrorMessage message={error} onRetry={() => void refetch()} />
      </div>
    )
  }

  if (!restaurant) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="rounded-[1.5rem] border border-slate-200 bg-white px-6 py-12 text-center shadow-sm">
          <h1 className="text-2xl font-semibold text-slate-900">Restaurant not found</h1>
          <p className="mt-2 text-sm text-slate-600">
            The restaurant you are looking for does not exist or was removed.
          </p>
          <Link
            to="/restaurants"
            className="mt-6 inline-flex items-center justify-center rounded-full bg-orange-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-600"
          >
            Browse restaurants
          </Link>
        </div>
      </div>
    )
  }

  const rawDescription = restaurant.description?.trim() ?? ''
  const cityLower = restaurant.city.trim().toLowerCase()
  const looksLikeAddress =
    rawDescription.length > 0 &&
    (/\d/.test(rawDescription) || rawDescription.includes(',') || rawDescription.toLowerCase().includes(cityLower))

  const description = looksLikeAddress
    ? 'No description available.'
    : rawDescription || 'No description available.'

  const address = looksLikeAddress
    ? rawDescription
    : `${restaurant.district}, ${restaurant.city}`

  const ratingValue = restaurant.rating ?? null
  const reviewCountValue = restaurant.review_count
  const categoryValue = restaurant.category?.trim() ? restaurant.category.trim() : null
  const openingHoursValue = restaurant.opening_hours?.trim() ? restaurant.opening_hours.trim() : null
  const phoneValue = restaurant.phone?.trim() ? restaurant.phone.trim() : null
  const websiteValue = restaurant.website?.trim() ? restaurant.website.trim() : null
  const thumbnailValue = restaurant.thumbnail?.trim() ? restaurant.thumbnail.trim() : null

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="mb-6">
        <Link
          to="/restaurants"
          className="inline-flex items-center gap-2 text-sm font-semibold text-slate-600 transition hover:text-orange-600"
        >
          <ArrowLeft size={16} />
          Back to restaurants
        </Link>
      </div>

      <section className="rounded-[1.5rem] border border-slate-200 bg-white p-8 shadow-sm">
        <div className="relative">
          <FavoriteButton
            restaurantId={restaurant.id}
            isFavorite={favorites.isFavorite(restaurant.id)}
            loading={favorites.isUpdating(restaurant.id)}
            onToggle={handleToggleFavorite}
            className="absolute right-0 top-0 inline-flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:border-red-200 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-60"
          />

          <div className="grid gap-8 lg:grid-cols-12">
            <div className={thumbnailValue ? 'space-y-5 pr-12 lg:col-span-7' : 'space-y-5 pr-12 lg:col-span-12'}>
              <div className="space-y-2">
                <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
                  {restaurant.name}
                </h1>
                <p className="flex items-center gap-2 text-sm text-slate-600">
                  <MapPin size={16} />
                  {restaurant.city}, {restaurant.district}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <RatingBadge rating={restaurant.average_rating} />
                <div className="inline-flex items-center gap-2 rounded-full bg-slate-50 px-3 py-1 text-sm font-medium text-slate-700">
                  <Star size={16} className="text-orange-500" />
                  {ratingValue === null ? (
                    <span>No ratings yet</span>
                  ) : (
                    <span>
                      {ratingValue.toFixed(1)} ({reviewCountValue.toLocaleString()} reviews)
                    </span>
                  )}
                </div>
                {categoryValue ? (
                  <div className="inline-flex items-center gap-2 rounded-full bg-slate-50 px-3 py-1 text-sm font-medium text-slate-700">
                    <Utensils size={16} className="text-slate-500" />
                    <span>{categoryValue}</span>
                  </div>
                ) : null}
              </div>

              <p className="text-sm leading-7 text-slate-600">{description}</p>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                  <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                    <MapPin size={14} />
                    Address
                  </div>
                  <div className="mt-2 text-sm leading-6 text-slate-700 whitespace-pre-line">{address}</div>
                </div>

                {openingHoursValue ? (
                  <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3">
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <Clock size={14} />
                      Opening Hours
                    </div>
                    <div className="mt-2 text-sm leading-6 text-slate-700 whitespace-pre-line">{openingHoursValue}</div>
                  </div>
                ) : null}

                {phoneValue ? (
                  <a
                    href={buildTelUrl(phoneValue)}
                    className="rounded-2xl border border-slate-200 bg-white px-4 py-3 transition hover:border-orange-200 hover:text-orange-600"
                  >
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <Phone size={14} />
                      Phone
                    </div>
                    <div className="mt-2 text-sm font-semibold text-slate-700">{phoneValue}</div>
                  </a>
                ) : null}

                {websiteValue ? (
                  <a
                    href={websiteValue}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded-2xl border border-slate-200 bg-white px-4 py-3 transition hover:border-orange-200 hover:text-orange-600"
                  >
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
                      <Globe size={14} />
                      Website
                    </div>
                    <div className="mt-2 truncate text-sm font-semibold text-slate-700">{websiteValue}</div>
                  </a>
                ) : null}
              </div>

              <RestaurantActions restaurant={restaurant} />
            </div>

            {thumbnailValue ? (
              <div className="lg:col-span-5">
                <img
                  src={thumbnailValue}
                  alt={`${restaurant.name} thumbnail`}
                  className="h-64 w-full rounded-2xl border border-slate-200 object-cover shadow-sm sm:h-72"
                  loading="lazy"
                />
              </div>
            ) : null}
          </div>
        </div>
      </section>

      <section className="mt-10 grid gap-6 lg:grid-cols-2">
        <MenuList items={restaurant.menu_items} />
        <ReviewList reviews={restaurant.reviews} />
      </section>
    </div>
  )
}
