import type { JSX } from 'react'

export function Footer(): JSX.Element {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm text-slate-500 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <p>TasteMap frontend foundation built with React, TypeScript, and TailwindCSS.</p>
        <p>Ready for authentication, restaurant discovery, and API integration.</p>
      </div>
    </footer>
  )
}
