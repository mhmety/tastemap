import { Heart } from 'lucide-react'
import type { JSX } from 'react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { fetchRestaurantDetail } from '../api/restaurants'
import { ErrorMessage } from '../components/ErrorMessage'
import { Loading } from '../components/Loading'
import { RestaurantCard } from '../components/RestaurantCard'
import { useAuth } from '../hooks/useAuth'
import { useFavorites } from '../hooks/useFavorites'
import { usePageTitle } from '../hooks/usePageTitle'
import type { Restaurant } from '../types/restaurant'

export function FavoritesPage(): JSX.Element {
  usePageTitle('Favorilerim')

  const { isAuthenticated } = useAuth()
  const favorites = useFavorites()

  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [isLoadingRestaurants, setIsLoadingRestaurants] = useState<boolean>(true)
  const [restaurantError, setRestaurantError] = useState<string | null>(null)

  const favoriteRestaurantIds = useMemo(
    () => favorites.favorites.map((favorite) => favorite.restaurant_id),
    [favorites.favorites],
  )

  useEffect(() => {
    if (!isAuthenticated) {
      setRestaurants([])
      setIsLoadingRestaurants(false)
      setRestaurantError(null)
      return
    }

    if (favorites.isLoading) {
      setIsLoadingRestaurants(true)
      return
    }

    if (favoriteRestaurantIds.length === 0) {
      setRestaurants([])
      setIsLoadingRestaurants(false)
      setRestaurantError(null)
      return
    }

    let isCancelled = false

    const load = async (): Promise<void> => {
      setIsLoadingRestaurants(true)
      setRestaurantError(null)

      try {
        const data = await Promise.all(
          favoriteRestaurantIds.map(async (restaurantId) => fetchRestaurantDetail(restaurantId)),
        )

        if (isCancelled) return
        setRestaurants(data)
      } catch {
        if (isCancelled) return
        setRestaurantError('Favori restoranlar yüklenirken bir hata oluştu. Lütfen tekrar deneyin.')
        setRestaurants([])
      } finally {
        if (!isCancelled) {
          setIsLoadingRestaurants(false)
        }
      }
    }

    void load()

    return () => {
      isCancelled = true
    }
  }, [favoriteRestaurantIds, favorites.isLoading, isAuthenticated])

  const isLoading = favorites.isLoading || isLoadingRestaurants
  const error = favorites.error ?? restaurantError

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Favorilerim</h1>
        <p className="text-sm text-slate-500 sm:text-base">Kaydettiğiniz ve tekrar ziyaret etmek istediğiniz mekanlar.</p>
      </header>

      <section className="mt-8 space-y-6">
        {isLoading ? <Loading label="Favori mekanlarınız yükleniyor..." /> : null}

        {!isLoading && error ? (
          <ErrorMessage message={error} onRetry={() => void favorites.loadFavorites()} />
        ) : null}

        {!isLoading && !error && restaurants.length === 0 ? (
          <div className="rounded-[2rem] border border-slate-200 bg-white px-6 py-16 text-center shadow-sm">
            <div className="mx-auto inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-orange-50 text-orange-600">
              <Heart className="fill-orange-200" size={28} />
            </div>
            <h2 className="mt-5 text-2xl font-bold text-slate-900">
              Henüz favori restoranınız yok
            </h2>
            <p className="mt-2 text-sm text-slate-500 max-w-md mx-auto">
              Beğendiğiniz mekanların detay sayfasındaki kalp ikonuna tıklayarak favorilerinize ekleyebilirsiniz.
            </p>
            <div className="mt-6">
              <Link
                to="/"
                className="inline-flex items-center justify-center rounded-full bg-orange-500 px-6 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-orange-600 active:scale-95"
              >
                Mekanları Keşfet
              </Link>
            </div>
          </div>
        ) : null}

        {!isLoading && !error && restaurants.length > 0 ? (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {restaurants.map((restaurant) => (
              <RestaurantCard key={restaurant.id} restaurant={restaurant} />
            ))}
          </div>
        ) : null}
      </section>
    </div>
  )
}

