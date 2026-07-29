import type { JSX } from 'react'

import { usePageTitle } from '../hooks/usePageTitle'

export function FavoritesPage(): JSX.Element {
  usePageTitle('Favorites')

  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="rounded-[1.5rem] border border-slate-200 bg-white px-6 py-12 text-center shadow-sm">
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900">Favorites</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">
          Favorites will be connected in a future sprint.
        </p>
      </div>
    </div>
  )
}

