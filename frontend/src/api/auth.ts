import { apiClient } from './client'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserResponse {
  id: string
  username: string
  email: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export async function login(request: LoginRequest): Promise<TokenResponse> {
  const body = new URLSearchParams()
  body.set('username', request.email)
  body.set('password', request.password)

  const response = await apiClient.post<TokenResponse>('/auth/login', body, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })

  return response.data
}

export async function register(request: RegisterRequest): Promise<UserResponse> {
  const response = await apiClient.post<UserResponse>('/auth/register', request)
  return response.data
}
