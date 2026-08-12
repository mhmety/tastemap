import { LockKeyhole, Mail } from 'lucide-react'
import type { JSX } from 'react'
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'
import { usePageTitle } from '../hooks/usePageTitle'

export function LoginPage(): JSX.Element {
  usePageTitle('Login')

  const navigate = useNavigate()
  const location = useLocation()
  const { login, isLoading, error, clearError } = useAuth()

  const [email, setEmail] = useState<string>('')
  const [password, setPassword] = useState<string>('')
  const [formError, setFormError] = useState<string | null>(null)

  const handleSubmit = async (): Promise<void> => {
    setFormError(null)
    clearError()

    if (!email.trim() || !password) {
      setFormError('Email and password are required.')
      return
    }

    try {
      await login(email.trim(), password)
      navigate('/restaurants')
    } catch {
      return
    }
  }

  const fromPath = (location.state as { from?: string } | null)?.from

  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-md rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm">
        <div className="space-y-3 text-center">
          <span className="inline-flex rounded-full bg-orange-100 px-4 py-1 text-sm font-medium text-orange-700">
            Account Access
          </span>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900">Login</h1>
          <p className="text-sm leading-6 text-slate-600">
            Sign in to access your favorites and continue exploring restaurants.
          </p>
          {fromPath ? (
            <p className="text-xs font-medium text-slate-500">
              Please log in to continue.
            </p>
          ) : null}
        </div>

        <form
          className="mt-8 space-y-5"
          onSubmit={(event) => {
            event.preventDefault()
            void handleSubmit()
          }}
        >
          <label className="block">
            <span className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
              <Mail size={16} />
              Email
            </span>
            <input
              type="email"
              placeholder="mehmet@example.com"
              autoComplete="email"
              value={email}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-orange-400"
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>

          <label className="block">
            <span className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
              <LockKeyhole size={16} />
              Password
            </span>
            <input
              type="password"
              placeholder="Enter your password"
              autoComplete="current-password"
              value={password}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-orange-400"
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>

          {formError ? (
            <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700 whitespace-pre-wrap">{formError}</p>
          ) : null}

          {!formError && error ? (
            <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700 whitespace-pre-wrap">{error}</p>
          ) : null}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-500"
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  )
}
