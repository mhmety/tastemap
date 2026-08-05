import { UtensilsCrossed } from 'lucide-react'
import type { JSX } from 'react'

import type { MenuItem } from '../types/restaurant'

interface MenuListProps {
  items: MenuItem[]
}

export function MenuList({ items }: MenuListProps): JSX.Element {
  if (items.length === 0) {
    return (
      <div className="rounded-[1.5rem] border border-slate-100 bg-slate-50 px-6 py-10 text-center">
        <div className="mx-auto inline-flex h-12 w-12 items-center justify-center rounded-full bg-white text-slate-400 shadow-sm">
          <UtensilsCrossed size={20} />
        </div>
        <div className="mt-6 flex items-center gap-3 text-slate-400">
          <div className="h-px flex-1 bg-slate-200" />
          <span className="text-xs font-semibold uppercase tracking-wide">Menu</span>
          <div className="h-px flex-1 bg-slate-200" />
        </div>
        <p className="mt-4 text-sm font-semibold text-slate-700">Menu is being prepared.</p>
      </div>
    )
  }

  return (
    <div className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-center gap-2 text-slate-900">
        <UtensilsCrossed size={18} />
        <h3 className="text-lg font-semibold">Menu</h3>
      </div>
      <ul className="mt-4 space-y-4">
        {items.map((menuItem) => (
          <li key={menuItem.id} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p className="text-base font-semibold text-slate-900">{menuItem.name}</p>
                {menuItem.description ? (
                  <p className="mt-1 text-sm text-slate-600">{menuItem.description}</p>
                ) : null}
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-700 shadow-sm">
                    {menuItem.category}
                  </span>
                </div>
              </div>
              <span className="inline-flex rounded-full bg-orange-100 px-3 py-1 text-sm font-semibold text-orange-700">
                ${menuItem.price.toFixed(2)}
              </span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
