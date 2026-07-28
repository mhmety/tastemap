import { MapPin } from 'lucide-react'
import type { JSX } from 'react'
import { Link } from 'react-router-dom'

import type { Restaurant } from '../types/restaurant'
import { RatingBadge } from './RatingBadge'

interface RestaurantCardProps {
  restaurant: Restaurant
}

export function RestaurantCard({ restaurant }: RestaurantCardProps): JSX.Element {
  const description = restaurant.description ?? 'No description available for this restaurant yet.'

  return (
    <article className="group flex h-full flex-col rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-lg">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <h2 className="text-xl font-semibold text-slate-900">{restaurant.name}</h2>
          <p className="flex items-center gap-2 text-sm text-slate-600">
            <MapPin size={16} />
            {restaurant.city}, {restaurant.district}
          </p>
        </div>
        <RatingBadge rating={restaurant.average_rating} />
      </div>

      <p className="mt-4 text-sm leading-6 text-slate-600">{description}</p>
      <div className="mt-6">
        <Link
          to={`/restaurants/${restaurant.id}`}
          className="inline-flex items-center justify-center rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition group-hover:border-orange-200 group-hover:text-orange-600"
        >
          View Details
        </Link>
      </div>
    </article>
  )
}
