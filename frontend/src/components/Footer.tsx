import type { JSX } from 'react'

export function Footer(): JSX.Element {
  return (
    <footer className="border-t border-slate-200/80 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-xs text-slate-500 sm:px-6 sm:flex-row sm:items-center sm:justify-between lg:px-8">
        <p>© 2026 TasteMap — Lezzet & Restoran Keşif Platformu</p>
        <p>FastAPI, PostgreSQL & React (TypeScript) ile geliştirilmiştir.</p>
      </div>
    </footer>
  )
}

