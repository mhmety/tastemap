import { ChevronLeft, ChevronRight, SlidersHorizontal } from 'lucide-react'
import type { JSX } from 'react'
import { useMemo, useState } from 'react'

import { ErrorMessage } from '../components/ErrorMessage'
import { Loading } from '../components/Loading'
import { RestaurantList } from '../components/RestaurantList'
import { SearchBar } from '../components/SearchBar'
import { usePageTitle } from '../hooks/usePageTitle'
import { useRestaurants } from '../hooks/useRestaurants'

const PAGE_SIZE = 6

export function RestaurantsPage(): JSX.Element {
  usePageTitle('Restaurants')

  const [searchInput, setSearchInput] = useState<string>('')
  const [submittedSearch, setSubmittedSearch] = useState<string>('')
  const [offset, setOffset] = useState<number>(0)

  const { restaurants, total, limit, isLoading, error, refetch } = useRestaurants({
    search: submittedSearch,
    limit: PAGE_SIZE,
    offset,
  })

  const currentPage = useMemo(() => Math.floor(offset / PAGE_SIZE) + 1, [offset])
  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total])
  const hasPreviousPage = offset > 0
  const hasNextPage = offset + limit < total

  const handleSearchSubmit = (): void => {
    setOffset(0)
    setSubmittedSearch(searchInput.trim())
  }

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
              Browse real restaurant data from the TasteMap backend with search, pagination, and
              responsive card-based browsing.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm">
            <SlidersHorizontal size={16} />
            Search and pagination are powered by the live API
          </div>
        </div>
      </section>

      <section className="mt-8">
        <SearchBar
          value={searchInput}
          isLoading={isLoading}
          onChange={setSearchInput}
          onSubmit={handleSearchSubmit}
        />
      </section>

      <section className="mt-10 grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">Results overview</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li>Search term: {submittedSearch || 'All restaurants'}</li>
            <li>Total matches: {total}</li>
            <li>Page size: {PAGE_SIZE}</li>
            <li>
              Current page: {currentPage} / {totalPages}
            </li>
          </ul>
        </aside>

        <div className="space-y-6">
          {isLoading ? <Loading /> : null}

          {!isLoading && error ? <ErrorMessage message={error} onRetry={() => void refetch()} /> : null}

          {!isLoading && !error ? <RestaurantList restaurants={restaurants} /> : null}

          <div className="flex flex-col gap-3 rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-slate-600">
              Showing {restaurants.length} of {total} restaurants
            </p>
            <div className="flex items-center gap-3">
              <button
                type="button"
                disabled={!hasPreviousPage || isLoading}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-orange-200 hover:text-orange-600 disabled:cursor-not-allowed disabled:opacity-50"
                onClick={() => setOffset((currentOffset) => Math.max(currentOffset - PAGE_SIZE, 0))}
              >
                <ChevronLeft size={16} />
                Previous
              </button>
              <button
                type="button"
                disabled={!hasNextPage || isLoading}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-orange-200 hover:text-orange-600 disabled:cursor-not-allowed disabled:opacity-50"
                onClick={() => setOffset((currentOffset) => currentOffset + PAGE_SIZE)}
              >
                Next
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
