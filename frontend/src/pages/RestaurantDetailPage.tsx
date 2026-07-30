import { ArrowLeft, MapPin } from 'lucide-react'
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

  const description = restaurant.description ?? 'No description available for this restaurant yet.'

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

      <section className="rounded-[1.5rem] border border-slate-200 bg-white p-8 shadow-sm">
        <div className="relative flex flex-col gap-6">
          <FavoriteButton
            restaurantId={restaurant.id}
            isFavorite={favorites.isFavorite(restaurant.id)}
            loading={favorites.isUpdating(restaurant.id)}
            onToggle={handleToggleFavorite}
            className="absolute right-0 top-0 inline-flex h-11 w-11 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:border-red-200 hover:text-red-600 disabled:cursor-not-allowed disabled:opacity-60"
          />

          <div className="space-y-3 pr-12">
            <h1 className="text-3xl font-semibold tracking-tight text-slate-900">
              {restaurant.name}
            </h1>
            <p className="flex items-center gap-2 text-sm text-slate-600">
              <MapPin size={16} />
              {restaurant.city}, {restaurant.district}
            </p>
            <p className="max-w-3xl text-sm leading-7 text-slate-600">{description}</p>
          </div>
          <div className="flex items-center gap-3">
            <RatingBadge rating={restaurant.average_rating} />
          </div>

          <RestaurantActions restaurant={restaurant} />
        </div>
      </section>

      <section className="mt-10 grid gap-6 lg:grid-cols-2">
        <MenuList items={restaurant.menu_items} />
        <ReviewList reviews={restaurant.reviews} />
      </section>
    </div>
  )
}
