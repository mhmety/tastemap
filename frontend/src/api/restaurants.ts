import type { PaginatedRestaurantsResponse } from '../types/restaurant'
import { apiClient } from './client'

interface FetchRestaurantsParams {
  limit: number
  offset: number
  search?: string
}

export async function fetchRestaurants(
  params: FetchRestaurantsParams,
): Promise<PaginatedRestaurantsResponse> {
  const response = await apiClient.get<PaginatedRestaurantsResponse>('/restaurants', {
    params,
  })

  return response.data
}
