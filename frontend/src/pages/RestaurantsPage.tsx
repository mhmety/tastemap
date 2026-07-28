import { Building2, MapPin, SlidersHorizontal } from 'lucide-react'
import type { JSX } from 'react'

import { usePageTitle } from '../hooks/usePageTitle'

const placeholderCards = [
  { name: 'Burger House', city: 'Ankara', district: 'Cankaya' },
  { name: 'Pizza Atelier', city: 'Istanbul', district: 'Kadikoy' },
  { name: 'Ramen Stop', city: 'Izmir', district: 'Alsancak' },
]

export function RestaurantsPage(): JSX.Element {
  usePageTitle('Restaurants')

  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
      <section className="space-y-4">
        <span className="inline-flex rounded-full bg-slate-100 px-4 py-1 text-sm font-medium text-slate-700">
          Discovery Page Foundation
        </span>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-4xl font-semibold tracking-tight text-slate-900">
              Restaurants
            </h1>
            <p className="mt-3 max-w-2xl text-lg text-slate-600">
              This page is ready for future restaurant listings, search filters, and pagination.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm">
            <SlidersHorizontal size={16} />
            Filters and search will be connected in a later sprint
          </div>
        </div>
      </section>

      <section className="mt-10 grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Planned controls</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li>Search by restaurant name or dish</li>
            <li>Filter by city and district</li>
            <li>Sort by rating and created date</li>
            <li>Paginated restaurant browsing</li>
          </ul>
        </aside>

        <div className="grid gap-4">
          {placeholderCards.map((item) => (
            <article
              key={item.name}
              className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm"
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <div className="flex items-center gap-2 text-slate-900">
                    <Building2 size={18} />
                    <h2 className="text-xl font-semibold">{item.name}</h2>
                  </div>
                  <p className="mt-2 flex items-center gap-2 text-sm text-slate-600">
                    <MapPin size={16} />
                    {item.city}, {item.district}
                  </p>
                </div>
                <span className="inline-flex rounded-full bg-orange-50 px-3 py-1 text-sm font-medium text-orange-700">
                  UI placeholder
                </span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}
