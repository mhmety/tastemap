import { Clock, Image, MapPin, Star, Tag } from 'lucide-react'
import type { JSX } from 'react'
import { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

import type { Restaurant } from '../types/restaurant'
import { formatCategoryTr, formatOpeningHoursTr } from '../utils/localization'

interface RestaurantCardProps {
  restaurant: Restaurant
}

export function RestaurantCard({ restaurant }: RestaurantCardProps): JSX.Element {
  const [imageFailed, setImageFailed] = useState(false)
  const location = useLocation()

  const ratingText = useMemo(() => {
    if (restaurant.rating == null) return 'Değerlendirilmedi'
    return restaurant.rating.toFixed(1)
  }, [restaurant.rating])

  const reviewCountText = useMemo(() => {
    if (restaurant.review_count == null) return null
    return restaurant.review_count.toLocaleString('tr-TR')
  }, [restaurant.review_count])

  const categoryLabel = useMemo(() => {
    return formatCategoryTr(restaurant.category)
  }, [restaurant.category])

  const openingHoursText = useMemo(() => {
    return formatOpeningHoursTr(restaurant.opening_hours)
  }, [restaurant.opening_hours])

  const isOpen = useMemo(() => {
    if (!restaurant.opening_hours) return null
    const lowered = restaurant.opening_hours.toLowerCase()
    if (lowered.startsWith('open')) return true
    if (lowered.startsWith('closed')) return false
    return null
  }, [restaurant.opening_hours])

  return (
    <article className="group flex h-full flex-col overflow-hidden rounded-[2rem] border border-slate-200/80 bg-white shadow-sm transition duration-300 hover:-translate-y-1 hover:border-orange-200 hover:shadow-xl">
      <div className="relative h-44 w-full overflow-hidden bg-slate-100 sm:h-48">
        {restaurant.thumbnail && !imageFailed ? (
          <img
            src={restaurant.thumbnail}
            alt={restaurant.name}
            loading="lazy"
            referrerPolicy="no-referrer"
            className="h-full w-full object-cover transition duration-500 group-hover:scale-105"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 text-slate-400">
            <Image size={32} />
          </div>
        )}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-slate-950/20 via-transparent to-transparent opacity-0 transition duration-300 group-hover:opacity-100" />
      </div>

      <div className="flex flex-1 flex-col justify-between p-6">
        <div className="space-y-3">
          <div className="space-y-1">
            <h2 className="line-clamp-1 text-lg font-bold tracking-tight text-slate-900 group-hover:text-orange-600 transition">
              {restaurant.name}
            </h2>
            <p className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
              <MapPin size={14} className="text-slate-400 shrink-0" />
              <span className="truncate">
                {restaurant.district} · {restaurant.city}
              </span>
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-xs">
            {categoryLabel ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2.5 py-1 font-semibold text-slate-700">
                <Tag size={12} className="text-slate-400" />
                <span className="truncate max-w-[150px]">{categoryLabel}</span>
              </span>
            ) : null}

            {restaurant.price_level ? (
              <span className="rounded-full bg-slate-100 px-2.5 py-1 font-semibold text-slate-700">
                {restaurant.price_level}
              </span>
            ) : null}
          </div>

          <div className="space-y-1.5 pt-1">
            <div className="flex items-center gap-1.5 text-xs text-slate-700">
              <Star size={14} className="fill-current text-amber-500 shrink-0" />
              <span className="font-bold text-slate-900">{ratingText}</span>
              {reviewCountText ? (
                <span className="text-slate-400 font-medium">({reviewCountText} yorum)</span>
              ) : null}
            </div>

            {openingHoursText ? (
              <p className="flex items-center gap-1.5 text-xs text-slate-600 font-medium">
                <Clock
                  size={14}
                  className={`shrink-0 ${
                    isOpen === true
                      ? 'text-emerald-600'
                      : isOpen === false
                        ? 'text-rose-600'
                        : 'text-slate-400'
                  }`}
                />
                <span className="line-clamp-1">{openingHoursText}</span>
              </p>
            ) : null}
          </div>
        </div>

        <div className="mt-5 pt-3 border-t border-slate-100 flex items-center justify-between">
          <Link
            to={`/restaurants/${restaurant.id}`}
            state={{ from: `${location.pathname}${location.search}` }}
            className="w-full inline-flex items-center justify-center rounded-full bg-slate-50 py-2.5 text-xs font-bold text-slate-700 transition duration-200 hover:bg-orange-500 hover:text-white active:scale-[0.98]"
          >
            İncele
          </Link>
        </div>
      </div>
    </article>
  )
}

