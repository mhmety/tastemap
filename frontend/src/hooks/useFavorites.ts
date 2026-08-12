import { useCallback, useEffect, useMemo, useState } from 'react'

import { createFavorite, deleteFavorite, fetchMyFavorites, type FavoriteResponse } from '../api/favorites'
import { normalizeApiErrorMessage } from '../utils/apiError'
import { useAuth } from './useAuth'

interface UseFavoritesResult {
  favorites: FavoriteResponse[]
  isLoading: boolean
  error: string | null
  loadFavorites: () => Promise<void>
  isFavorite: (restaurantId: string) => boolean
  addFavorite: (restaurantId: string) => Promise<void>
  removeFavorite: (restaurantId: string) => Promise<void>
  toggleFavorite: (restaurantId: string) => Promise<void>
  isUpdating: (restaurantId: string) => boolean
}

const DEFAULT_ERROR_MESSAGE = 'Unable to update favorites right now. Please try again.'

export function useFavorites(): UseFavoritesResult {
  const { isAuthenticated } = useAuth()

  const [favorites, setFavorites] = useState<FavoriteResponse[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [updatingIds, setUpdatingIds] = useState<Set<string>>(() => new Set())

  const favoritesByRestaurantId = useMemo(() => {
    const map = new Map<string, FavoriteResponse>()
    for (const favorite of favorites) {
      map.set(favorite.restaurant_id, favorite)
    }
    return map
  }, [favorites])

  const isUpdating = useCallback(
    (restaurantId: string): boolean => updatingIds.has(restaurantId),
    [updatingIds],
  )

  const loadFavorites = useCallback(async (): Promise<void> => {
    if (!isAuthenticated) {
      setFavorites([])
      setError(null)
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const data = await fetchMyFavorites()
      setFavorites(data)
    } catch (error: unknown) {
      setError(normalizeApiErrorMessage(error, DEFAULT_ERROR_MESSAGE))
      setFavorites([])
    } finally {
      setIsLoading(false)
    }
  }, [isAuthenticated])

  useEffect(() => {
    void loadFavorites()
  }, [loadFavorites])

  const isFavorite = useCallback(
    (restaurantId: string): boolean => favoritesByRestaurantId.has(restaurantId),
    [favoritesByRestaurantId],
  )

  const addFavorite = useCallback(
    async (restaurantId: string): Promise<void> => {
      if (!isAuthenticated) return
      if (favoritesByRestaurantId.has(restaurantId)) return

      const optimisticFavorite: FavoriteResponse = {
        id: `optimistic-${restaurantId}`,
        user_id: 'optimistic',
        restaurant_id: restaurantId,
        created_at: new Date().toISOString(),
      }

      setFavorites((current) => [optimisticFavorite, ...current])
      setUpdatingIds((current) => new Set([...current, restaurantId]))

      try {
        const created = await createFavorite({ restaurant_id: restaurantId })
        setFavorites((current) => [
          created,
          ...current.filter((favorite) => favorite.id !== optimisticFavorite.id),
        ])
      } catch (error: unknown) {
        setFavorites((current) => current.filter((favorite) => favorite.id !== optimisticFavorite.id))
        setError(normalizeApiErrorMessage(error, DEFAULT_ERROR_MESSAGE))
        throw error
      } finally {
        setUpdatingIds((current) => {
          const next = new Set(current)
          next.delete(restaurantId)
          return next
        })
      }
    },
    [favoritesByRestaurantId, isAuthenticated],
  )

  const removeFavorite = useCallback(
    async (restaurantId: string): Promise<void> => {
      if (!isAuthenticated) return

      const favorite = favoritesByRestaurantId.get(restaurantId)
      if (!favorite) return

      setFavorites((current) => current.filter((item) => item.restaurant_id !== restaurantId))
      setUpdatingIds((current) => new Set([...current, restaurantId]))

      try {
        await deleteFavorite(favorite.id)
      } catch (error: unknown) {
        setFavorites((current) => [favorite, ...current])
        setError(normalizeApiErrorMessage(error, DEFAULT_ERROR_MESSAGE))
        throw error
      } finally {
        setUpdatingIds((current) => {
          const next = new Set(current)
          next.delete(restaurantId)
          return next
        })
      }
    },
    [favoritesByRestaurantId, isAuthenticated],
  )

  const toggleFavorite = useCallback(
    async (restaurantId: string): Promise<void> => {
      if (isFavorite(restaurantId)) {
        await removeFavorite(restaurantId)
        return
      }

      await addFavorite(restaurantId)
    },
    [addFavorite, isFavorite, removeFavorite],
  )

  return {
    favorites,
    isLoading,
    error,
    loadFavorites,
    isFavorite,
    addFavorite,
    removeFavorite,
    toggleFavorite,
    isUpdating,
  }
}

