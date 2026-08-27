import { LockKeyhole, Mail, UserRound } from 'lucide-react'
import type { JSX } from 'react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { useAuth } from '../hooks/useAuth'
import { usePageTitle } from '../hooks/usePageTitle'

export function RegisterPage(): JSX.Element {
  usePageTitle('Register')

  const navigate = useNavigate()
  const { register, isLoading, error, clearError } = useAuth()

  const [username, setUsername] = useState<string>('')
  const [email, setEmail] = useState<string>('')
  const [password, setPassword] = useState<string>('')
  const [formError, setFormError] = useState<string | null>(null)

  const handleSubmit = async (): Promise<void> => {
    setFormError(null)
    clearError()

    if (!username.trim() || !email.trim() || !password) {
      setFormError('Kullanıcı adı, e-posta ve parola gereklidir.')
      return
    }

    try {
      await register(username.trim(), email.trim(), password)
      navigate('/restaurants')
    } catch {
      return
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-md rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm">
        <div className="space-y-3 text-center">
          <span className="inline-flex rounded-full bg-orange-100 px-4 py-1 text-sm font-medium text-orange-700">
              Yeni Hesap
            </span>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900">Kayıt</h1>
          <p className="text-sm leading-6 text-slate-600">
              Hesap oluşturarak favori restoran listenizi başlatın.
            </p>
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
              <UserRound size={16} /> Kullanıcı adı
            </span>
            <input
              type="text"
              placeholder="mehmetyildiz"
              autoComplete="username"
              value={username}
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-orange-400"
              onChange={(event) => setUsername(event.target.value)}
            />
          </label>

          <label className="block">
            <span className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
              <Mail size={16} /> E-posta
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
              <LockKeyhole size={16} /> Parola
            </span>
            <input
              type="password"
              placeholder="Parola oluştur"
              autoComplete="new-password"
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
            className="w-full rounded-full bg-orange-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:bg-orange-300"
          >
            {isLoading ? 'Hesap oluşturuluyor...' : 'Kayıt'}
          </button>
        </form>
      </div>
    </div>
  )
}
