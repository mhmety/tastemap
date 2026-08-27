import { Clock, Image, MapPin, Star, Tag } from 'lucide-react'
import type { JSX } from 'react'
import { useMemo, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'

import type { Restaurant } from '../types/restaurant'

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
    return restaurant.review_count.toLocaleString()
  }, [restaurant.review_count])

  const openingHoursText = useMemo(() => {
    if (!restaurant.opening_hours) return null
    return restaurant.opening_hours
  }, [restaurant.opening_hours])

  const isOpen = useMemo(() => {
    if (!openingHoursText) return null
    const lowered = openingHoursText.toLowerCase()
    if (lowered.startsWith('open')) return true
    if (lowered.startsWith('closed')) return false
    return null
  }, [openingHoursText])

  return (
    <article className="group flex h-full flex-col overflow-hidden rounded-[1.5rem] border border-slate-100 bg-white shadow-sm transition duration-200 hover:-translate-y-1 hover:border-slate-200 hover:shadow-xl">
      <div className="relative h-40 w-full bg-slate-50 sm:h-44">
        {restaurant.thumbnail && !imageFailed ? (
          <img
            src={restaurant.thumbnail}
            alt={restaurant.name}
            loading="lazy"
            referrerPolicy="no-referrer"
            className="h-full w-full object-cover"
            onError={() => setImageFailed(true)}
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100 text-slate-400">
            <Image size={28} />
          </div>
        )}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-slate-900/15 via-transparent to-transparent opacity-0 transition duration-200 group-hover:opacity-100" />
      </div>

      <div className="flex flex-1 flex-col gap-4 p-5">
        <div className="space-y-2">
          <h2 className="line-clamp-2 text-lg font-semibold text-slate-900">{restaurant.name}</h2>
          <p className="flex items-center gap-2 text-sm text-slate-600">
            <MapPin size={16} />
            <span className="truncate">
              {restaurant.district} · {restaurant.city}
            </span>
          </p>
        </div>

        <div className="space-y-2">
          {restaurant.category ? (
            <p className="flex items-center gap-2 text-sm font-medium text-slate-700">
              <Tag size={16} className="text-slate-500" />
              <span className="truncate">{restaurant.category}</span>
            </p>
          ) : null}

          <div className="flex flex-wrap items-center gap-3 text-sm text-slate-700">
            <span className="inline-flex items-center gap-2">
              <Star size={16} className="text-amber-500" fill="currentColor" />
              <span className="font-semibold">{ratingText}</span>
              {reviewCountText ? (
                <span className="text-slate-500">({reviewCountText})</span>
              ) : null}
            </span>

            {restaurant.price_level ? (
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                {restaurant.price_level}
              </span>
            ) : null}
          </div>

          {openingHoursText ? (
            <p className="flex items-center gap-2 text-sm text-slate-600">
              <Clock size={16} className={isOpen === true ? 'text-emerald-600' : isOpen === false ? 'text-rose-600' : 'text-slate-500'} />
              <span className="line-clamp-1">{openingHoursText}</span>
            </p>
          ) : null}
        </div>

        <div className="mt-auto">
          <Link
            to={`/restaurants/${restaurant.id}`}
            state={{ from: `${location.pathname}${location.search}` }}
            className="inline-flex items-center justify-center rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition duration-200 group-hover:-translate-y-0.5 group-hover:border-orange-200 group-hover:text-orange-600 group-hover:shadow-sm active:translate-y-0"
          >
            Detaylar
          </Link>
        </div>
      </div>
    </article>
  )
}
