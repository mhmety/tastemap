import { useCallback, useEffect, useState } from 'react'

import { fetchRestaurantDetail } from '../api/restaurants'
import type { RestaurantDetailResponse, Review } from '../types/restaurant'
import { normalizeApiErrorMessage } from '../utils/apiError'

interface UseRestaurantDetailResult {
  restaurant: RestaurantDetailResponse | null
  isLoading: boolean
  error: string | null
  refetch: () => Promise<void>
  applyReviewCreated: (review: Review) => void
}

const DEFAULT_ERROR_MESSAGE = 'Unable to load restaurant details right now. Please try again.'

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
      setError(normalizeApiErrorMessage(error, DEFAULT_ERROR_MESSAGE))
      setRestaurant(null)
    } finally {
      setIsLoading(false)
    }
  }, [restaurantId])

  useEffect(() => {
    void loadRestaurant()
  }, [loadRestaurant])

  const applyReviewCreated = useCallback((review: Review) => {
    setRestaurant((current) => {
      if (!current) return current
      if (current.reviews.some((item) => item.id === review.id)) return current

      const nextReviews = [review, ...current.reviews]
      const ratings = nextReviews
        .map((item) => item.rating)
        .filter((value): value is number => typeof value === 'number' && value >= 1 && value <= 5)

      const average =
        ratings.length > 0
          ? Math.round((ratings.reduce((sum, value) => sum + value, 0) / ratings.length) * 10) / 10
          : null

      return {
        ...current,
        reviews: nextReviews,
        review_count: nextReviews.length,
        rating: average,
        average_rating: average,
      }
    })
  }, [])

  return {
    restaurant,
    isLoading,
    error,
    refetch: loadRestaurant,
    applyReviewCreated,
  }
}
