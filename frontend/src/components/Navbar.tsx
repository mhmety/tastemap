import { LogOut, Menu, Utensils, X } from 'lucide-react'
import type { JSX } from 'react'
import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'


import { useAuth } from '../hooks/useAuth'
import type { NavigationItem } from '../types/navigation'

const loggedOutNavigation: NavigationItem[] = [
  { label: 'Keşfet', to: '/' },
  { label: 'Giriş Yap', to: '/login' },
  { label: 'Kayıt Ol', to: '/register' },
]

const loggedInNavigation: NavigationItem[] = [
  { label: 'Keşfet', to: '/' },
  { label: 'Favorilerim', to: '/favorites' },
]

const baseLinkClass =
  'rounded-full px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-orange-50 hover:text-orange-600'

export function Navbar(): JSX.Element {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const navigate = useNavigate()
  const { isAuthenticated, logout } = useAuth()

  const navigationItems = isAuthenticated ? loggedInNavigation : loggedOutNavigation

  const handleLogout = (): void => {
    logout()
    setIsMenuOpen(false)
    navigate('/')
  }

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <NavLink
          className="flex items-center gap-3 text-slate-900 group"
          to="/"
          onClick={() => setIsMenuOpen(false)}
        >
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-orange-500 text-white shadow-sm transition group-hover:bg-orange-600 group-hover:scale-105">
            <Utensils size={18} />
          </span>
          <div className="flex flex-col">
            <span className="text-lg font-bold tracking-tight text-slate-900">TasteMap</span>
            <span className="text-xs text-slate-500 font-medium">Yemek Odaklı Restoran Keşfi</span>
          </div>
        </NavLink>

        <nav className="hidden items-center gap-2 md:flex">
          {navigationItems.map((item) => (
            <NavLink
              key={item.to}
              className={({ isActive }) =>
                `${baseLinkClass} ${isActive ? 'bg-orange-50 font-semibold text-orange-600' : ''}`
              }
              to={item.to}
            >
              {item.label}
            </NavLink>
          ))}
          {isAuthenticated ? (
            <button
              type="button"
              className={`${baseLinkClass} inline-flex items-center gap-2 text-rose-600 hover:bg-rose-50 hover:text-rose-700`}
              onClick={handleLogout}
            >
              <LogOut size={16} />
              Çıkış Yap
            </button>
          ) : null}
        </nav>

        <button
          type="button"
          className="inline-flex items-center justify-center rounded-xl border border-slate-200 p-2 text-slate-700 md:hidden"
          aria-label={isMenuOpen ? 'Menüyü kapat' : 'Menüyü aç'}
          onClick={() => setIsMenuOpen((current) => !current)}
        >
          {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {isMenuOpen ? (
        <nav className="border-t border-slate-200 bg-white px-4 py-4 md:hidden animate-in slide-in-from-top-2">
          <div className="mx-auto flex max-w-6xl flex-col gap-2">
            {navigationItems.map((item) => (
              <NavLink
                key={item.to}
                className={({ isActive }) =>
                  `rounded-xl px-4 py-2.5 text-sm font-medium transition ${
                    isActive ? 'bg-orange-50 font-semibold text-orange-600' : 'text-slate-700 hover:bg-slate-50'
                  }`
                }
                to={item.to}
                onClick={() => setIsMenuOpen(false)}
              >
                {item.label}
              </NavLink>
            ))}
            {isAuthenticated ? (
              <button
                type="button"
                className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-left text-sm font-medium text-rose-600 hover:bg-rose-50"
                onClick={handleLogout}
              >
                <LogOut size={16} />
                Çıkış Yap
              </button>
            ) : null}
          </div>
        </nav>
      ) : null}
    </header>
  )
}

