import { ExternalLink, Globe, MapPin } from 'lucide-react'
import type { JSX } from 'react'

import type { RestaurantDetailResponse } from '../types/restaurant'

interface RestaurantActionsProps {
  restaurant: RestaurantDetailResponse
}

function buildGoogleMapsUrl(name: string, city: string): string {
  const query = encodeURIComponent(`${name} ${city}`)
  return `https://www.google.com/maps/search/?api=1&query=${query}`
}

export function RestaurantActions({ restaurant }: RestaurantActionsProps): JSX.Element {
  const googleMapsUrl = buildGoogleMapsUrl(restaurant.name, restaurant.city)
  const websiteUrl = restaurant.website?.trim() ? restaurant.website.trim() : null

  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
      <a
        href={googleMapsUrl}
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`Open ${restaurant.name} in Google Maps`}
        className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 transition hover:border-orange-200 hover:text-orange-600 sm:w-auto"
      >
        <MapPin size={16} />
        Open in Google Maps
        <ExternalLink size={16} className="text-slate-400" />
      </a>

      {websiteUrl ? (
        <a
          href={websiteUrl}
          target="_blank"
          rel="noopener noreferrer"
          aria-label={`Visit ${restaurant.name} website`}
          className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-5 text-sm font-semibold text-slate-700 transition hover:border-orange-200 hover:text-orange-600 sm:w-auto"
        >
          <Globe size={16} />
          Visit Website
          <ExternalLink size={16} className="text-slate-400" />
        </a>
      ) : null}
    </div>
  )
}
