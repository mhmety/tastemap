import { Menu, Search, X } from 'lucide-react'
import type { JSX } from 'react'
import { useState } from 'react'
import { NavLink } from 'react-router-dom'

import type { NavigationItem } from '../types/navigation'

const navigationItems: NavigationItem[] = [
  { label: 'Home', to: '/' },
  { label: 'Restaurants', to: '/restaurants' },
  { label: 'Login', to: '/login' },
  { label: 'Register', to: '/register' },
]

const baseLinkClass =
  'rounded-full px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-orange-50 hover:text-orange-600'

export function Navbar(): JSX.Element {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <NavLink
          className="flex items-center gap-3 text-slate-900"
          to="/"
          onClick={() => setIsMenuOpen(false)}
        >
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-orange-500 text-white shadow-sm">
            <Search size={18} />
          </span>
          <div className="flex flex-col">
            <span className="text-lg font-semibold tracking-tight">TasteMap</span>
            <span className="text-xs text-slate-500">Discover food worth trying</span>
          </div>
        </NavLink>

        <nav className="hidden items-center gap-2 md:flex">
          {navigationItems.map((item) => (
            <NavLink
              key={item.to}
              className={({ isActive }) =>
                `${baseLinkClass} ${isActive ? 'bg-orange-100 text-orange-700' : ''}`
              }
              to={item.to}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <button
          type="button"
          className="inline-flex items-center justify-center rounded-xl border border-slate-200 p-2 text-slate-700 md:hidden"
          aria-label={isMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
          onClick={() => setIsMenuOpen((current) => !current)}
        >
          {isMenuOpen ? <X size={18} /> : <Menu size={18} />}
        </button>
      </div>

      {isMenuOpen ? (
        <nav className="border-t border-slate-200 bg-white px-4 py-3 md:hidden">
          <div className="mx-auto flex max-w-6xl flex-col gap-2">
            {navigationItems.map((item) => (
              <NavLink
                key={item.to}
                className={({ isActive }) =>
                  `${baseLinkClass} ${isActive ? 'bg-orange-100 text-orange-700' : ''}`
                }
                to={item.to}
                onClick={() => setIsMenuOpen(false)}
              >
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>
      ) : null}
    </header>
  )
}
