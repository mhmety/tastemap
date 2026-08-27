import { ChevronDown, UtensilsCrossed } from 'lucide-react'
import type { JSX } from 'react'
import { useMemo, useState } from 'react'

import type { MenuItem } from '../types/restaurant'

interface MenuListProps {
  items: MenuItem[]
}

const CATEGORY_LABEL_TR: Record<string, string> = {
  appetizers: 'Mezeler & Başlangıçlar',
  starters: 'Başlangıçlar',
  'starters & appetizers': 'Başlangıçlar ve Mezeler',
  mains: 'Ana Yemekler',
  'main dishes': 'Ana Yemekler',
  'main course': 'Ana Yemekler',
  'main courses': 'Ana Yemekler',
  entrees: 'Ana Yemekler',
  desserts: 'Tatlılar',
  dessert: 'Tatlılar',
  drinks: 'İçecekler',
  beverages: 'İçecekler',
  'hot drinks': 'Sıcak İçecekler',
  'cold drinks': 'Soğuk İçecekler',
  cocktails: 'Kokteyller',
  salads: 'Salatalar',
  salad: 'Salatalar',
  soups: 'Çorbalar',
  soup: 'Çorbalar',
  pizza: 'Pizzalar',
  pasta: 'Makarnalar',
  burgers: 'Burgerler',
  burger: 'Burgerler',
  sandwiches: 'Sandviçler',
  sandwich: 'Sandviçler',
  wraps: 'Dürümler',
  wrap: 'Dürümler',
  breakfast: 'Kahvaltılıklar',
  brunch: 'Brunch',
  seafood: 'Deniz Ürünleri',
  'fish & seafood': 'Balık ve Deniz Ürünleri',
  grill: 'Izgara & Kebap',
  grilled: 'Izgara Çeşitleri',
  kebabs: 'Kebaplar',
  kebab: 'Kebaplar',
  doner: 'Dönerler',
  pide: 'Pideler',
  lahmacun: 'Lahmacun',
  sides: 'Yan Lezzetler & Garnitür',
  'side dishes': 'Garnitürler',
  sauces: 'Soslar',
  bread: 'Ekmek & Hamur İşi',
  breads: 'Ekmekler',
  vegan: 'Vegan Lezzetler',
  vegetarian: 'Vejetaryen',
  'vegan & vegetarian': 'Vegan ve Vejetaryen',
  kids: 'Çocuk Menüsü',
  'kids menu': 'Çocuk Menüsü',
  'for kids': 'Çocuklar İçin',
  specials: 'Şefin Özel Lezzetleri',
  'chef specials': 'Şefin Özel Menüsü',
  sushi: 'Sushi',
  tapas: 'Tapas',
  meze: 'Mezeler',
  mezze: 'Mezeler',
  coffee: 'Kahveler',
  tea: 'Çaylar',
  bakery: 'Fırın & Pasta',
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
      <div className="h-full flex flex-col items-center justify-center rounded-[2rem] border border-slate-200 bg-white p-8 text-center shadow-sm">
        <div className="mx-auto inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-orange-50 text-orange-600 shadow-sm">
          <UtensilsCrossed size={24} />
        </div>
        <h3 className="mt-4 text-lg font-bold text-slate-900">Menü Henüz Eklenmemiş</h3>
        <p className="mt-1 text-xs text-slate-500 max-w-xs">
          Bu restoran için henüz dijital menü verisi sisteme yüklenmemiş.
        </p>
      </div>
    )
  }

  const toggleCategory = (categoryName: string): void => {
    setExpanded((prev) => ({ ...prev, [categoryName]: !prev[categoryName] }))
  }

  return (
    <div className="h-full flex flex-col min-h-0 rounded-[2rem] border border-slate-200 bg-white p-6 shadow-sm overflow-hidden sm:p-7">
      <div className="flex-shrink-0 flex items-center justify-between gap-2 border-b border-slate-100 pb-4 text-slate-900">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-orange-50 text-orange-600">
            <UtensilsCrossed size={18} />
          </div>
          <h3 className="text-lg font-bold">Restoran Menüsü</h3>
        </div>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          {items.length} çeşit yemek
        </span>
      </div>

      <div className="mt-4 flex-1 min-h-0 overflow-y-auto pr-1">
        <div className="space-y-3">
          {grouped.map((group) => {
            const isOpen = expanded[group.categoryName] === true
            return (
              <div key={group.categoryName} className="rounded-2xl border border-slate-100 bg-slate-50/70 overflow-hidden transition">
                <button
                  type="button"
                  className="w-full flex items-center justify-between gap-3 px-4 py-3.5 text-left transition hover:bg-slate-100/80"
                  onClick={() => toggleCategory(group.categoryName)}
                  aria-expanded={isOpen}
                >
                  <span className="text-sm font-bold text-slate-900">
                    {group.categoryLabel}
                  </span>
                  <span className="flex items-center gap-2 text-slate-500">
                    <span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-slate-600 shadow-xs">
                      {group.items.length}
                    </span>
                    <ChevronDown
                      size={18}
                      className={`transition-transform duration-200 ${isOpen ? 'rotate-180 text-orange-600' : ''}`}
                    />
                  </span>
                </button>
                {isOpen ? (
                  <ul className="border-t border-slate-200/60 p-2 space-y-2">
                    {group.items.map((menuItem) => (
                      <li
                        key={menuItem.id}
                        className="rounded-xl border border-slate-100 bg-white p-4 shadow-xs"
                      >
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                          <div>
                            <p className="text-sm font-bold text-slate-900">{menuItem.name}</p>
                            {menuItem.description ? (
                              <p className="mt-1 text-xs text-slate-500 leading-5">{menuItem.description}</p>
                            ) : null}
                          </div>
                          {menuItem.price > 0 ? (
                            <span className="inline-flex shrink-0 self-start rounded-full bg-orange-50 px-3 py-1 text-xs font-bold text-orange-700">
                              {formatMenuPrice(menuItem.price)}
                            </span>
                          ) : null}
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

