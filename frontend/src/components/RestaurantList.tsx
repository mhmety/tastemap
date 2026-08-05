import { Search } from 'lucide-react'
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
        <div className="mx-auto inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-50 text-slate-400">
          <Search size={22} />
        </div>
        <h2 className="text-xl font-semibold text-slate-900">No restaurants found</h2>
        <p className="mt-2 text-sm text-slate-600">
          Try a different search term or adjust pagination.
        </p>
      </div>
    )
  }

  return (
    <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {restaurants.map((restaurant) => (
        <RestaurantCard key={restaurant.id} restaurant={restaurant} />
      ))}
    </div>
  )
}
