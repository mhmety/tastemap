import type { JSX } from 'react'

import type { Restaurant } from '../types/restaurant'
import { RestaurantCard } from './RestaurantCard'

interface RestaurantListProps {
  restaurants: Restaurant[]
}

export function RestaurantList({ restaurants }: RestaurantListProps): JSX.Element {
  if (restaurants.length === 0) {
    return (
      <div className="rounded-[1.5rem] border border-slate-200 bg-white px-6 py-12 text-center shadow-sm">
        <h2 className="text-xl font-semibold text-slate-900">No restaurants found</h2>
        <p className="mt-2 text-sm text-slate-600">
          Try a different search term or move back to the previous page.
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
      {restaurants.map((restaurant) => (
        <RestaurantCard key={restaurant.id} restaurant={restaurant} />
      ))}
    </div>
  )
}
