import axios from 'axios'
import { useCallback, useEffect, useState } from 'react'

import { fetchRestaurants } from '../api/restaurants'
import type { PaginatedRestaurantsResponse, Restaurant } from '../types/restaurant'

interface UseRestaurantsOptions {
  search: string
  limit: number
  offset: number
}

interface UseRestaurantsResult {
  restaurants: Restaurant[]
  total: number
  limit: number
  offset: number
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

const DEFAULT_ERROR_MESSAGE = 'Unable to load restaurants right now. Please try again.'

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? DEFAULT_ERROR_MESSAGE
  }

  return DEFAULT_ERROR_MESSAGE
}

export function useRestaurants(options: UseRestaurantsOptions): UseRestaurantsResult {
  const { search, limit, offset } = options

  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [pagination, setPagination] = useState<PaginatedRestaurantsResponse>({
    items: [],
    total: 0,
    limit,
    offset,
  })
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const loadRestaurants = useCallback(async (): Promise<void> => {
    setIsLoading(true)
    setError(null)

    try {
      const data = await fetchRestaurants({
        search: search || undefined,
        limit,
        offset,
      })

      setPagination(data)
      setRestaurants(data.items)
    } catch (error: unknown) {
      setError(getErrorMessage(error))
      setRestaurants([])
    } finally {
      setIsLoading(false)
    }
  }, [limit, offset, search])

  useEffect(() => {
    void loadRestaurants()
  }, [loadRestaurants])

  return {
    restaurants,
    total: pagination.total,
    limit: pagination.limit,
    offset: pagination.offset,
    isLoading,
    error,
    refetch: loadRestaurants,
  }
}
