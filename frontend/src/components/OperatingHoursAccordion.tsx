import { ChevronDown, Clock } from 'lucide-react';
import type { JSX } from 'react';
import { useState } from 'react';

interface OperatingHoursAccordionProps {
  rows: Array<{ label: string; value: string }>
  todayValue?: string | null
  todayLabel?: string
}

export function OperatingHoursAccordion({
  rows,
  todayValue,
  todayLabel,
}: OperatingHoursAccordionProps): JSX.Element {
  const [isOpen, setIsOpen] = useState<boolean>(false)
  const todayText = todayValue?.trim() ? todayValue.trim() : null
  const todayStatusLabel = (() => {
    if (!todayText) return 'Open today'
    const lowered = todayText.toLowerCase()
    if (lowered === 'closed' || lowered.startsWith('closed')) return 'Closed today'
    return 'Open today'
  })()

  return (
    <section className="mt-6 rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm">
      <button
        type="button"
        className="flex w-full items-start justify-between gap-4 text-left"
        onClick={() => setIsOpen((current) => !current)}
      >
        <div className="space-y-1">
          <div className="text-lg font-semibold text-slate-900">Opening hours</div>
          {todayText ? (
            <div className="flex items-start gap-3 text-sm text-slate-600">
              <div className="mt-0.5 inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-2xl bg-slate-50 text-slate-500">
                <Clock size={18} />
              </div>
              <div>
                <div className="font-semibold text-slate-700">{todayStatusLabel}</div>
                <div className="text-slate-600">{todayText}</div>
              </div>
            </div>
          ) : null}
          <div className="text-sm font-semibold text-orange-600">{isOpen ? 'Hide weekly schedule' : '▼ Weekly Schedule'}</div>
        </div>
        <ChevronDown
          size={20}
          className={`shrink-0 text-slate-500 transition-transform duration-300 ${isOpen ? 'rotate-180' : 'rotate-0'
            }`}
        />
      </button>

      <div
        className={`grid transition-[grid-template-rows,opacity] duration-300 ${isOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'
          }`}
      >
        <div className="overflow-hidden">
          <div className="mt-4 divide-y divide-slate-100">
            {rows.map((row) => {
              const isToday = Boolean(todayLabel) && row.label.toLowerCase() === todayLabel?.toLowerCase()
              return (
                <div
                  key={row.label}
                  className={`flex items-start justify-between gap-4 py-3 text-sm ${isToday ? 'rounded-xl bg-slate-50 px-3' : ''
                    }`}
                >
                  <span className={`font-semibold ${isToday ? 'text-slate-900' : 'text-slate-700'}`}>
                    {row.label}
                  </span>
                  <span className={`text-right ${isToday ? 'text-slate-700' : 'text-slate-600'}`}>{row.value}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </section>
  )
}
