import { ChevronLeft, ChevronRight, Sparkles } from 'lucide-react'
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
  usePageTitle('Restoran & Yemek Keşfi')

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

  const handleClearSearch = (): void => {
    setSearchInput('')
    setSearchParams((current) => {
      const next = new URLSearchParams(current)
      next.delete('search')
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
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Hero Keşif Başlığı */}
      <section className="space-y-4 rounded-[2rem] border border-slate-200/80 bg-gradient-to-br from-orange-50/50 via-white to-white p-6 sm:p-10 shadow-xs">
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-orange-100 px-3.5 py-1 text-xs font-bold text-orange-700">
            <Sparkles size={14} />
            Yemek Odaklı Keşif Motoru
          </span>
        </div>

        <div className="space-y-2">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            Ne Yemek İstersiniz?
          </h1>
          <p className="max-w-2xl text-base text-slate-600 sm:text-lg">
            Mekan ismi aramak yerine doğrudan canınızın çektiği yemeği veya mutfağı arayın; en lezzetli restoranları keşfedin.
          </p>
        </div>

        {/* Arama Çubuğu */}
        <div className="pt-2">
          <SearchBar
            value={searchInput}
            isLoading={isLoading}
            onChange={setSearchInput}
            onSubmit={handleSearchSubmit}
          />
        </div>
      </section>

      {/* İçerik Bölümü: Filtre / Özet & Restoran Kartları */}
      <section className="mt-8 grid gap-8 lg:grid-cols-[260px_1fr]">
        {/* Sol Özet / Filtre Paneli */}
        <aside className="h-fit rounded-[2rem] border border-slate-200/80 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <h2 className="text-base font-bold text-slate-900">Arama Özeti</h2>
            {submittedSearch ? (
              <button
                type="button"
                onClick={handleClearSearch}
                className="text-xs font-semibold text-orange-600 hover:text-orange-700"
              >
                Temizle
              </button>
            ) : null}
          </div>

          <ul className="mt-4 space-y-3 text-xs text-slate-600">
            <li className="flex flex-col gap-0.5">
              <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px]">Arama</span>
              <span className="font-bold text-slate-800 line-clamp-1">
                {submittedSearch ? `"${submittedSearch}"` : 'Tüm Restoranlar'}
              </span>
            </li>
            <li className="flex flex-col gap-0.5">
              <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px]">Toplam Mekan</span>
              <span className="font-bold text-slate-800">{total} restoran</span>
            </li>
            <li className="flex flex-col gap-0.5">
              <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px]">Sayfa</span>
              <span className="font-bold text-slate-800">
                {currentPage} / {totalPages}
              </span>
            </li>
          </ul>
        </aside>

        {/* Sağ Restoran Listesi */}
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

          {/* Sayfalama Kontrolleri */}
          {!isLoading && !error && restaurants.length > 0 ? (
            <div className="flex flex-col gap-3 rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
              <p className="text-xs font-medium text-slate-500">
                Toplam <span className="font-bold text-slate-800">{total}</span> restorandan{' '}
                <span className="font-bold text-slate-800">
                  {offset + 1}–{Math.min(offset + restaurants.length, total)}
                </span>{' '}
                arası gösteriliyor
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={!hasPreviousPage || isLoading}
                  className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-bold text-slate-700 transition hover:border-orange-200 hover:text-orange-600 disabled:cursor-not-allowed disabled:opacity-40"
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
                  className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-bold text-slate-700 transition hover:border-orange-200 hover:text-orange-600 disabled:cursor-not-allowed disabled:opacity-40"
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
          ) : null}
        </div>
      </section>
    </div>
  )
}

