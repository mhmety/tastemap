import { LockKeyhole, Mail } from 'lucide-react'
import type { JSX } from 'react'
import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'
import { usePageTitle } from '../hooks/usePageTitle'

export function LoginPage(): JSX.Element {
  usePageTitle('Giriş Yap')

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
      setFormError('Lütfen e-posta adresinizi ve parolanızı girin.')
      return
    }

    try {
      await login(email.trim(), password)
      const fromPath = (location.state as { from?: string } | null)?.from || '/'
      navigate(fromPath)
    } catch {
      return
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-md rounded-[2.5rem] border border-slate-200 bg-white p-8 shadow-sm sm:p-10">
        <div className="space-y-3 text-center">
          <span className="inline-flex rounded-full bg-orange-100 px-4 py-1 text-xs font-bold text-orange-700">
            Hesap Girişi
          </span>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Hoş Geldiniz</h1>
          <p className="text-sm text-slate-500">
            Favori mekanlarınızı yönetmek ve yorum yapmak için giriş yapın.
          </p>
        </div>

        <form
          className="mt-8 space-y-4"
          onSubmit={(event) => {
            event.preventDefault()
            void handleSubmit()
          }}
        >
          <label className="block">
            <span className="mb-1.5 flex items-center gap-1.5 text-xs font-bold text-slate-700">
              <Mail size={14} className="text-slate-400" /> E-posta Adresi
            </span>
            <input
              type="email"
              placeholder="ornek@eposta.com"
              autoComplete="email"
              value={email}
              className="w-full rounded-2xl border border-slate-200 bg-slate-50/50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-orange-400 focus:bg-white focus:ring-2 focus:ring-orange-100"
              onChange={(event) => setEmail(event.target.value)}
            />
          </label>

          <label className="block">
            <span className="mb-1.5 flex items-center gap-1.5 text-xs font-bold text-slate-700">
              <LockKeyhole size={14} className="text-slate-400" /> Parola
            </span>
            <input
              type="password"
              placeholder="Parolanızı girin"
              autoComplete="current-password"
              value={password}
              className="w-full rounded-2xl border border-slate-200 bg-slate-50/50 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-orange-400 focus:bg-white focus:ring-2 focus:ring-orange-100"
              onChange={(event) => setPassword(event.target.value)}
            />
          </label>

          {formError ? (
            <p className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-600 whitespace-pre-wrap">
              {formError}
            </p>
          ) : null}

          {!formError && error ? (
            <p className="rounded-xl bg-rose-50 p-3 text-xs font-semibold text-rose-600 whitespace-pre-wrap">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-full bg-slate-900 py-3.5 text-sm font-bold text-white shadow-sm transition hover:bg-slate-800 active:scale-[0.99] disabled:cursor-not-allowed disabled:bg-slate-400"
          >
            {isLoading ? 'Giriş yapılıyor...' : 'Giriş Yap'}
          </button>
        </form>

        <div className="mt-6 text-center border-t border-slate-100 pt-6">
          <p className="text-xs text-slate-500">
            Hesabınız yok mu?{' '}
            <Link to="/register" className="font-bold text-orange-600 hover:text-orange-700">
              Hemen Kayıt Olun
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

