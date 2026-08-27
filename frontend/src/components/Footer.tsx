import type { JSX } from 'react'

export function Footer(): JSX.Element {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-8 text-sm text-slate-500 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <p>TasteMap Türkçe frontend, React, TypeScript ve TailwindCSS ile oluşturulmuştur.</p>
        <p>Yetkilendirme, restoran keşfi ve API entegrasyonu için hazır.</p>
      </div>
    </footer>
  )
}
