import { LockKeyhole, Mail } from 'lucide-react'
import type { JSX } from 'react'

import { usePageTitle } from '../hooks/usePageTitle'

export function LoginPage(): JSX.Element {
  usePageTitle('Login')

  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-md rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm">
        <div className="space-y-3 text-center">
          <span className="inline-flex rounded-full bg-orange-100 px-4 py-1 text-sm font-medium text-orange-700">
            Account Access
          </span>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900">Login</h1>
          <p className="text-sm leading-6 text-slate-600">
            This form is intentionally UI-only for now. Backend authentication will be connected in
            a later sprint.
          </p>
        </div>

        <form className="mt-8 space-y-5">
          <label className="block">
            <span className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
              <Mail size={16} />
              Email
            </span>
            <input
              type="email"
              placeholder="mehmet@example.com"
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-orange-400"
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
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-orange-400"
            />
          </label>

          <button
            type="button"
            className="w-full rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  )
}
