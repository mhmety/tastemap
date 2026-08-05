import { ExternalLink, Globe } from 'lucide-react'
import type { JSX } from 'react'

import type { RestaurantDetailResponse } from '../types/restaurant'

interface RestaurantActionsProps {
  restaurant: RestaurantDetailResponse
}

export function RestaurantActions({
  restaurant,
}: RestaurantActionsProps): JSX.Element {
  const websiteUrl = restaurant.website?.trim() ? restaurant.website.trim() : null

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
      {websiteUrl ? (
        <a
          href={websiteUrl}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`Visit ${restaurant.name} website`}
          className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 transition duration-200 hover:-translate-y-0.5 hover:border-orange-200 hover:text-orange-600 hover:shadow-sm active:translate-y-0 sm:w-auto"
        >
          <Globe size={16} />
          Visit Website
          <ExternalLink size={16} className="text-slate-400" />
        </a>
      ) : null}
    </div>
  )
}
