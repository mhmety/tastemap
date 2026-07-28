import { LockKeyhole, Mail, UserRound } from 'lucide-react'
import type { JSX } from 'react'

import { usePageTitle } from '../hooks/usePageTitle'

export function RegisterPage(): JSX.Element {
  usePageTitle('Register')

  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-md rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm">
        <div className="space-y-3 text-center">
          <span className="inline-flex rounded-full bg-orange-100 px-4 py-1 text-sm font-medium text-orange-700">
            New Account
          </span>
          <h1 className="text-3xl font-semibold tracking-tight text-slate-900">Register</h1>
          <p className="text-sm leading-6 text-slate-600">
            This form establishes the screen structure only. Submission logic will be added when
            frontend authentication starts.
          </p>
        </div>

        <form className="mt-8 space-y-5">
          <label className="block">
            <span className="mb-2 flex items-center gap-2 text-sm font-medium text-slate-700">
              <UserRound size={16} />
              Username
            </span>
            <input
              type="text"
              placeholder="mehmetyildiz"
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-orange-400"
            />
          </label>

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
              placeholder="Create a password"
              className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-orange-400"
            />
          </label>

          <button
            type="button"
            className="w-full rounded-full bg-orange-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-600"
          >
            Register
          </button>
        </form>
      </div>
    </div>
  )
}
