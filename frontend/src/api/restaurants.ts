import type { PaginatedRestaurantsResponse, RestaurantDetailResponse } from '../types/restaurant'
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

export async function fetchRestaurantDetail(
  restaurantId: string,
): Promise<RestaurantDetailResponse> {
  const response = await apiClient.get<RestaurantDetailResponse>(`/restaurants/${restaurantId}`)
  return response.data
}
