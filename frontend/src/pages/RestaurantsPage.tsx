import { ChevronLeft, ChevronRight, SlidersHorizontal } from 'lucide-react'
import type { JSX } from 'react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { ErrorMessage } from '../components/ErrorMessage'
import { RestaurantCardSkeleton } from '../components/RestaurantCardSkeleton'
import { RestaurantList } from '../components/RestaurantList'
import { SearchBar } from '../components/SearchBar'
import { usePageTitle } from '../hooks/usePageTitle'
import { useRestaurants } from '../hooks/useRestaurants'

const PAGE_SIZE = 6

export function RestaurantsPage(): JSX.Element {
  usePageTitle('Restaurants')

  const [searchParams, setSearchParams] = useSearchParams()

  const submittedSearch = (searchParams.get('search') ?? '').trim()
  const offset = Math.max(0, Number.parseInt(searchParams.get('offset') ?? '0', 10) || 0)

  const [searchInput, setSearchInput] = useState<string>(submittedSearch)
  const hasRestoredScrollRef = useRef(false)

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
    hasRestoredScrollRef.current = true
    window.scrollTo({ top: 0 })
    setSearchParams((current) => {
      const next = new URLSearchParams(current)
      const value = searchInput.trim()
      if (value) next.set('search', value)
      else next.delete('search')
      next.set('offset', '0')
      return next
    })
  }

  useEffect(() => {
    setSearchInput(submittedSearch)
  }, [submittedSearch])

  useEffect(() => {
    let rafId: number | null = null
    const onScroll = (): void => {
      if (rafId != null) return
      rafId = window.requestAnimationFrame(() => {
        rafId = null
        const currentState = window.history.state ?? {}
        const usr = typeof currentState.usr === 'object' && currentState.usr ? currentState.usr : {}
        window.history.replaceState(
          { ...currentState, usr: { ...usr, scrollY: window.scrollY } },
          '',
        )
      })
    }

    window.addEventListener('scroll', onScroll, { passive: true })
    return () => {
      if (rafId != null) window.cancelAnimationFrame(rafId)
      window.removeEventListener('scroll', onScroll)
    }
  }, [])

  useEffect(() => {
    if (isLoading) return
    if (hasRestoredScrollRef.current) return
    const scrollY = window.history.state?.usr?.scrollY
    if (typeof scrollY === 'number' && Number.isFinite(scrollY) && scrollY > 0) {
      hasRestoredScrollRef.current = true
      window.scrollTo({ top: scrollY })
    }
  }, [isLoading])

  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
      <section className="space-y-4">
<span className="inline-flex rounded-full bg-slate-100 px-4 py-1 text-sm font-medium text-slate-700">
              Keşif Sayfası Temeli
            </span>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-4xl font-semibold tracking-tight text-slate-900">
              Restoranlar
            </h1>
            <p className="mt-3 max-w-2xl text-lg text-slate-600">
              Gerçek TasteMap backend verilerini arama, sayfalama ve kart bazlı gezinleme ile keşfedin.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-600 shadow-sm">
            <SlidersHorizontal size={16} />
              Arama ve sayfalama canlı API ile desteklenir
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
          <h2 className="text-lg font-semibold text-slate-900">Sonuç Özeti</h2>
          <ul className="mt-4 space-y-3 text-sm text-slate-600">
            <li>Arama terimi: {submittedSearch || 'Tüm restoranlar'}</li>
            <li>Toplam eşleşme: {total}</li>
            <li>Sayfa boyutu: {PAGE_SIZE}</li>
            <li>Şu sayfa: {currentPage} / {totalPages}</li>
          </ul>
        </aside>

        <div className="space-y-6">
          {isLoading ? (
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: PAGE_SIZE }).map((_, index) => (
                <RestaurantCardSkeleton key={`restaurant-skeleton-${index}`} />
              ))}
            </div>
          ) : null}

          {!isLoading && error ? <ErrorMessage message={error} onRetry={() => void refetch()} /> : null}

          {!isLoading && !error ? <RestaurantList restaurants={restaurants} /> : null}

          <div className="flex flex-col gap-3 rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-slate-600">
              {restaurants.length} of {total} restoranı gösteriliyor
            </p>
            <div className="flex items-center gap-3">
              <button
                type="button"
                disabled={!hasPreviousPage || isLoading}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-orange-200 hover:text-orange-600 disabled:cursor-not-allowed disabled:opacity-50"
                onClick={() => {
                  hasRestoredScrollRef.current = true
                  window.scrollTo({ top: 0 })
                  setSearchParams((current) => {
                    const next = new URLSearchParams(current)
                    next.set('offset', String(Math.max(offset - PAGE_SIZE, 0)))
                    return next
                  })
                }}
              >
<ChevronLeft size={16} />
              Önceki
              </button>
              <button
                type="button"
                disabled={!hasNextPage || isLoading}
                className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-orange-200 hover:text-orange-600 disabled:cursor-not-allowed disabled:opacity-50"
                onClick={() => {
                  hasRestoredScrollRef.current = true
                  window.scrollTo({ top: 0 })
                  setSearchParams((current) => {
                    const next = new URLSearchParams(current)
                    next.set('offset', String(offset + PAGE_SIZE))
                    return next
                  })
                }}
              >
                Sonraki
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
