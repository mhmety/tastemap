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
  rating: number | null
  review_count: number | null
  category: string | null
  google_place_id: string | null
  thumbnail: string | null
  opening_hours: string | null
  average_rating: number | null
  created_at: string
  updated_at: string
}

export interface MenuItem {
  id: string
  name: string
  price: number
  category: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface Review {
  id: string
  user_id: string
  rating: number
  comment: string | null
  created_at: string
  updated_at: string
}

export interface RestaurantDetailResponse extends RestaurantApiItem {
  review_count: number
  menu_items: MenuItem[]
  reviews: Review[]
}

export interface PaginatedRestaurantsResponse {
  items: RestaurantApiItem[]
  total: number
  limit: number
  offset: number
}
export type Restaurant = RestaurantApiItem
