import { Clock, X } from 'lucide-react'
import type { JSX } from 'react'
import { useEffect } from 'react'

import { formatDailyHoursTr, formatDayNameTr } from '../utils/localization'

interface OperatingHoursRow {
  key: string
  label: string
  value: string
}

interface OperatingHoursModalProps {
  isOpen: boolean
  onClose: () => void
  restaurantName: string
  rows: OperatingHoursRow[]
  todayKey?: string
}

export function OperatingHoursModal({
  isOpen,
  onClose,
  restaurantName,
  rows,
  todayKey,
}: OperatingHoursModalProps): JSX.Element | null {
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (event: KeyboardEvent): void => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    // Scroll kilidi
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', handleKeyDown)

    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
      role="dialog"
      aria-modal="true"
      aria-labelledby="operating-hours-title"
    >
      {/* Arka Plan Karartma (Backdrop) */}
      <div
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity animate-in fade-in"
        onClick={onClose}
      />

      {/* Modal Kutusu */}
      <div className="relative w-full max-w-md overflow-hidden rounded-[2rem] border border-slate-100 bg-white p-6 shadow-2xl transition-all sm:p-7 animate-in zoom-in-95">
        {/* Başlık ve Kapat Butonu */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-orange-50 text-orange-600">
              <Clock size={22} />
            </div>
            <div>
              <h2 id="operating-hours-title" className="text-xl font-bold tracking-tight text-slate-900">
                Çalışma Saatleri
              </h2>
              <p className="text-xs font-medium text-slate-500 line-clamp-1">{restaurantName}</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Kapat"
            className="inline-flex h-9 w-9 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          >
            <X size={20} />
          </button>
        </div>

        {/* Günler Listesi */}
        <div className="mt-6 divide-y divide-slate-100 rounded-2xl border border-slate-100 bg-slate-50/70 p-2">
          {rows.map((row) => {
            const isToday = Boolean(todayKey) && row.key.toLowerCase() === todayKey?.toLowerCase()
            const localizedDay = formatDayNameTr(row.key)
            const localizedHours = formatDailyHoursTr(row.value)

            return (
              <div
                key={row.key}
                className={`flex items-center justify-between gap-4 px-4 py-3 text-sm transition ${
                  isToday
                    ? 'rounded-xl bg-orange-100/70 font-semibold text-orange-950 shadow-xs'
                    : 'text-slate-700'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span>{localizedDay}</span>
                  {isToday ? (
                    <span className="rounded-full bg-orange-500 px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide text-white">
                      Bugün
                    </span>
                  ) : null}
                </div>
                <span className={`text-right ${isToday ? 'font-bold text-orange-950' : 'text-slate-600'}`}>
                  {localizedHours}
                </span>
              </div>
            )
          })}
        </div>

        {/* Alt Kapat Butonu */}
        <div className="mt-6 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="w-full rounded-full bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 active:scale-[0.99] sm:w-auto"
          >
            Kapat
          </button>
        </div>
      </div>
    </div>
  )
}
