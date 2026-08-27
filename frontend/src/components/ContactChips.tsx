import { Globe, Phone } from 'lucide-react'
import type { JSX } from 'react'

interface ContactChipsProps {
  websiteUrl: string | null
  phoneLabel: string | null
  phoneHref: string | null
}

export function ContactChips({ websiteUrl, phoneLabel, phoneHref }: ContactChipsProps): JSX.Element | null {
  const hasWebsite = Boolean(websiteUrl)
  const hasPhone = Boolean(phoneHref && phoneLabel)

  if (!hasWebsite && !hasPhone) return null

  return (
    <div
      className={`flex flex-col gap-3 sm:flex-row sm:items-stretch ${
        hasPhone && hasWebsite ? 'sm:justify-between' : hasWebsite ? 'sm:justify-end' : 'sm:justify-start'
      }`}
    >
      {hasPhone ? (
        <a
          href={phoneHref as string}
          className="flex h-11 w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-5 text-xs font-bold text-slate-700 shadow-xs transition duration-200 hover:-translate-y-0.5 hover:border-orange-200 hover:text-orange-600 hover:shadow-md active:translate-y-0 sm:w-auto"
        >
          <Phone size={14} className="text-slate-500" />
          {phoneLabel as string}
        </a>
      ) : null}

      {hasWebsite ? (
        <a
          href={websiteUrl as string}
          target="_blank"
          rel="noopener noreferrer"
          className="flex h-11 w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-5 text-xs font-bold text-slate-700 shadow-xs transition duration-200 hover:-translate-y-0.5 hover:border-orange-200 hover:text-orange-600 hover:shadow-md active:translate-y-0 sm:w-auto"
        >
          <Globe size={14} className="text-slate-500" />
          Web Sitesi
        </a>
      ) : null}
    </div>
  )
}

