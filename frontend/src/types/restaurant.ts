export interface ReviewSummary {
  averageRating: number | null
  reviewCount: number
}

export interface RestaurantApiItem {
  id: string
  name: string
  city: string
  district: string
  latitude: number | null
  longitude: number | null
  website: string | null
  phone: string | null
  description: string | null
  average_rating: number | null
  created_at: string
  updated_at: string
}

export interface PaginatedRestaurantsResponse {
  items: RestaurantApiItem[]
  total: number
  limit: number
  offset: number
}
export type Restaurant = RestaurantApiItem
