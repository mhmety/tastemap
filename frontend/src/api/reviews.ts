import type { Review } from '../types/restaurant'
import { apiClient } from './client'

interface CreateRestaurantReviewRequest {
  rating: number
  comment?: string | null
}

interface CreateRestaurantReviewResponse extends Review {
  restaurant_id: string
}

export async function createRestaurantReview(
  restaurantId: string,
  payload: CreateRestaurantReviewRequest,
): Promise<CreateRestaurantReviewResponse> {
  const response = await apiClient.post<CreateRestaurantReviewResponse>(
    `/restaurants/${restaurantId}/reviews`,
    payload,
  )
  return response.data
}

