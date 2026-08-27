import type { Review } from '../types/restaurant'
import { apiClient } from './client'

interface CreateRestaurantReviewRequest {
  rating: number
  comment?: string | null
}

interface CreateRestaurantReviewResponse extends Review {
  restaurant_id: string
}

interface UpdateReviewRequest {
  rating?: number
  comment?: string | null
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

export async function updateReview(
  reviewId: string,
  payload: UpdateReviewRequest,
): Promise<Review> {
  const response = await apiClient.put<Review>(`/reviews/${reviewId}`, payload)
  return response.data
}

export async function deleteReview(reviewId: string): Promise<void> {
  await apiClient.delete(`/reviews/${reviewId}`)
}


