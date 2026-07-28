import { useCallback, useEffect, useState } from 'react'
import axios from 'axios'

import { fetchRestaurantDetail } from '../api/restaurants'
import type { RestaurantDetailResponse } from '../types/restaurant'

interface UseRestaurantDetailResult {
  restaurant: RestaurantDetailResponse | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
}

const DEFAULT_ERROR_MESSAGE = 'Unable to load restaurant details right now. Please try again.'

function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    return error.response?.data?.detail ?? DEFAULT_ERROR_MESSAGE
  }

  return DEFAULT_ERROR_MESSAGE
}

export function useRestaurantDetail(restaurantId: string | undefined): UseRestaurantDetailResult {
  const [restaurant, setRestaurant] = useState<RestaurantDetailResponse | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const loadRestaurant = useCallback(async (): Promise<void> => {
    if (!restaurantId) {
      setRestaurant(null)
      setIsLoading(false)
      setError('Restaurant identifier is missing.')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const data = await fetchRestaurantDetail(restaurantId)
      setRestaurant(data)
    } catch (error: unknown) {
      setError(getErrorMessage(error))
      setRestaurant(null)
    } finally {
      setIsLoading(false)
    }
  }, [restaurantId])

  useEffect(() => {
    void loadRestaurant()
  }, [loadRestaurant])

  return {
    restaurant,
    isLoading,
    error,
    refetch: loadRestaurant,
  }
}
