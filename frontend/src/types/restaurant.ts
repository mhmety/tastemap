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
  price_level: string | null
  opening_hours: string | null
  operating_hours: Record<string, unknown> | null
  thumbnail: string | null
  google_place_id: string | null
  serpapi_data_id: string | null
  reviews_link: string | null
  photos_link: string | null
  user_review: string | null
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
  user_id: string | null
  rating: number
  comment: string | null
  author_name?: string | null
  profile_photo?: string | null
  likes?: number | null
  source?: 'google' | 'user'
  created_at: string
  updated_at: string
}

export interface RestaurantDetailResponse extends RestaurantApiItem {
  review_count: number
  menu_items: MenuItem[]
  reviews: Review[]
  photos?: string[] | null
}

export interface PaginatedRestaurantsResponse {
  items: RestaurantApiItem[]
  total: number
  limit: number
  offset: number
}
export type Restaurant = RestaurantApiItem
