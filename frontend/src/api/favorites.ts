import { apiClient } from './client'

export interface FavoriteResponse {
  id: string
  user_id: string
  restaurant_id: string
  created_at: string
}

export interface FavoriteCreateRequest {
  restaurant_id: string
}

export async function fetchMyFavorites(): Promise<FavoriteResponse[]> {
  const response = await apiClient.get<FavoriteResponse[]>('/favorites/me')
  return response.data
}

export async function createFavorite(
  request: FavoriteCreateRequest,
): Promise<FavoriteResponse> {
  const response = await apiClient.post<FavoriteResponse>('/favorites', request)
  return response.data
}

export async function deleteFavorite(favoriteId: string): Promise<void> {
  await apiClient.delete(`/favorites/${favoriteId}`)
}
