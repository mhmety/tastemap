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
      <div className="rounded-[2rem] border border-slate-200/80 bg-white px-6 py-16 text-center shadow-sm">
        <div className="mx-auto inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-50 text-orange-600">
          <Search size={24} />
        </div>
        <h2 className="mt-4 text-xl font-bold text-slate-900">Restoran Bulunamadı</h2>
        <p className="mt-2 text-sm text-slate-500 max-w-md mx-auto">
          Aradığınız kriterlere uygun mekan bulunamadı. Farklı bir yemek veya anahtar kelime aramayı deneyebilirsiniz.
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

