import type { JSX, ReactNode } from 'react'
import { useCallback, useMemo, useState } from 'react'

import { login as loginApi, register as registerApi } from '../api/auth'
import { normalizeApiErrorMessage } from '../utils/apiError'
import { AuthContext, type AuthContextValue, type AuthUser } from './auth-context'

const DEFAULT_ERROR_MESSAGE = 'Authentication failed. Please try again.'

function decodeJwtSubject(token: string): string | null {
  try {
    const [, payload] = token.split('.')
    if (!payload) return null

    const padded = payload.replace(/-/g, '+').replace(/_/g, '/')
    const json = atob(padded.padEnd(padded.length + ((4 - (padded.length % 4)) % 4), '='))
    const parsed = JSON.parse(json) as { sub?: string }

    return parsed.sub ?? null
  } catch {
    return null
  }
}

function getInitialUser(): AuthUser | null {
  const token = localStorage.getItem('access_token')
  if (!token) return null

  return { id: decodeJwtSubject(token) }
}

export function AuthProvider({ children }: { children: ReactNode }): JSX.Element {
  const [user, setUser] = useState<AuthUser | null>(() => getInitialUser())
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const clearError = useCallback(() => {
    setError(null)
  }, [])

  const login = useCallback(async (email: string, password: string): Promise<void> => {
    setIsLoading(true)
    setError(null)

    try {
      const tokenResponse = await loginApi({ email, password })
      localStorage.setItem('access_token', tokenResponse.access_token)
      setUser({ id: decodeJwtSubject(tokenResponse.access_token) })
    } catch (error: unknown) {
      setError(normalizeApiErrorMessage(error, DEFAULT_ERROR_MESSAGE))
      localStorage.removeItem('access_token')
      setUser(null)
      throw error
    } finally {
      setIsLoading(false)
    }
  }, [])

  const register = useCallback(
    async (username: string, email: string, password: string): Promise<void> => {
      setIsLoading(true)
      setError(null)

      try {
        await registerApi({ username, email, password })
        const tokenResponse = await loginApi({ email, password })
        localStorage.setItem('access_token', tokenResponse.access_token)
        setUser({ id: decodeJwtSubject(tokenResponse.access_token) })
      } catch (error: unknown) {
        setError(normalizeApiErrorMessage(error, DEFAULT_ERROR_MESSAGE))
        localStorage.removeItem('access_token')
        setUser(null)
        throw error
      } finally {
        setIsLoading(false)
      }
    },
    [],
  )

  const logout = useCallback(() => {
    localStorage.removeItem('access_token')
    setUser(null)
    setError(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(localStorage.getItem('access_token')),
      isLoading,
      error,
      login,
      register,
      logout,
      clearError,
    }),
    [error, isLoading, login, logout, register, user, clearError],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
