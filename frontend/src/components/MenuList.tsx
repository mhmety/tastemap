import { ChevronDown, UtensilsCrossed } from 'lucide-react'
import type { JSX } from 'react'
import { useMemo, useState } from 'react'

import type { MenuItem } from '../types/restaurant'

interface MenuListProps {
  items: MenuItem[]
}

const CATEGORY_LABEL_TR: Record<string, string> = {
  appetizers: 'Mezeler',
  starters: 'Başlangıçlar',
  'starters & appetizers': 'Başlangıçlar ve Mezeler',
  mains: 'Ana Yemekler',
  'main dishes': 'Ana Yemekler',
  'main course': 'Ana Yemekler',
  'main courses': 'Ana Yemekler',
  entrees: 'Ana Yemekler',
  desserts: 'Tatlılar',
  drinks: 'İçecekler',
  beverages: 'İçecekler',
  'hot drinks': 'Sıcak İçecekler',
  'cold drinks': 'Soğuk İçecekler',
  cocktails: 'Kokteyller',
  salads: 'Salatalar',
  soups: 'Çorbalar',
  pizza: 'Pizza',
  pasta: 'Makarna',
  burgers: 'Burgerler',
  sandwiches: 'Sandviçler',
  wraps: 'Dürümler',
  breakfast: 'Kahvaltı',
  brunch: 'Brunch',
  seafood: 'Deniz Ürünleri',
  'fish & seafood': 'Balık ve Deniz Ürünleri',
  grill: 'Izgara',
  grilled: 'Izgara Ürünleri',
  kebabs: 'Kebaplar',
  kebab: 'Kebaplar',
  sides: 'Yan Ürünler',
  'side dishes': 'Yan Ürünler',
  sauces: 'Soslar',
  bread: 'Ekmek',
  breads: 'Ekmekler',
  vegan: 'Vegan',
  vegetarian: 'Vejetaryen',
  'vegan & vegetarian': 'Vegan ve Vejetaryen',
  kids: 'Çocuk Menüsü',
  'kids menu': 'Çocuk Menüsü',
  'for kids': 'Çocuklar İçin',
  specials: 'Özel Lezzetler',
  'chef specials': 'Şefin Özel Ürünleri',
  sushi: 'Sushi',
  tapas: 'Tapas',
  meze: 'Mezeler',
  mezze: 'Mezeler',
}

function getCategoryLabelTr(category: string): string {
  const trimmed = category.trim()
  const key = trimmed.toLowerCase()
  if (CATEGORY_LABEL_TR[key]) return CATEGORY_LABEL_TR[key]
  if (CATEGORY_LABEL_TR[trimmed]) return CATEGORY_LABEL_TR[trimmed]
  return trimmed
}

/**
 * Menü fiyatını formatla.
 * Veritabanında tüm fiyatlar doğrudan TRY olarak kayıtlıdır.
 * Herhangi bir kur dönüşümü UYGULANMAZ.
 */
function formatMenuPrice(price: number): string {
  if (price <= 0) return ''
  const rounded = Math.round(price)
  return `₺${rounded.toLocaleString('tr-TR')}`
}

export function MenuList({ items }: MenuListProps): JSX.Element {
  const grouped = useMemo(() => {
    if (items.length === 0) return []
    const groups = new Map<string, MenuItem[]>()
    for (const item of items) {
      const key = item.category?.trim() || 'Diğer'
      if (!groups.has(key)) groups.set(key, [])
      groups.get(key)!.push(item)
    }
    return Array.from(groups.entries()).map(([categoryName, categoryItems]) => ({
      categoryName,
      categoryLabel: getCategoryLabelTr(categoryName),
      items: categoryItems,
    }))
  }, [items])

  const [expanded, setExpanded] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {}
    if (grouped.length > 0) initial[grouped[0].categoryName] = true
    return initial
  })

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
        <p className="mt-4 text-sm font-semibold text-slate-700">Menü henüz hazırlanmadı.</p>
      </div>
    )
  }

  const toggleCategory = (categoryName: string): void => {
    setExpanded((prev) => ({ ...prev, [categoryName]: !prev[categoryName] }))
  }

  return (
    <div className="h-full flex flex-col min-h-0 rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm overflow-hidden">
      <div className="flex-shrink-0 flex items-center gap-2 text-slate-900">
        <UtensilsCrossed size={18} />
        <h3 className="text-lg font-semibold">Menü</h3>
      </div>
      <div className="mt-4 flex-1 min-h-0 overflow-y-auto pr-1">
        <div className="space-y-4">
          {grouped.map((group) => {
            const isOpen = expanded[group.categoryName] === true
            return (
              <div key={group.categoryName} className="rounded-2xl border border-slate-100 bg-slate-50 overflow-hidden">
                <button
                  type="button"
                  className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left transition hover:bg-slate-100/60"
                  onClick={() => toggleCategory(group.categoryName)}
                  aria-expanded={isOpen}
                >
                  <span className="text-sm font-semibold text-slate-900">
                    {group.categoryLabel}
                  </span>
                  <span className="flex items-center gap-2 text-slate-500">
                    <span className="text-xs font-medium text-slate-500">{group.items.length}</span>
                    <ChevronDown
                      size={18}
                      className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                    />
                  </span>
                </button>
                {isOpen ? (
                  <ul className="border-t border-slate-200/70 px-2 py-2 space-y-2">
                    {group.items.map((menuItem) => (
                      <li
                        key={menuItem.id}
                        className="rounded-xl border border-slate-100 bg-white p-4"
                      >
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                          <div>
                            <p className="text-base font-semibold text-slate-900">{menuItem.name}</p>
                            {menuItem.description ? (
                              <p className="mt-1 text-sm text-slate-600">{menuItem.description}</p>
                            ) : null}
                          </div>
                          <span className="inline-flex rounded-full bg-orange-100 px-3 py-1 text-sm font-semibold text-orange-700">
                            {formatMenuPrice(menuItem.price)}
                          </span>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
