import type { FormEvent, JSX } from 'react'
import { Search } from 'lucide-react'

interface SearchBarProps {
  value: string
  isLoading: boolean
  onChange: (value: string) => void
  onSubmit: () => void
}

export function SearchBar({
  value,
  isLoading,
  onChange,
  onSubmit,
}: SearchBarProps): JSX.Element {
  const handleSubmit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault()
    onSubmit()
  }

  return (
    <form
      className="flex flex-col gap-2 rounded-2xl sm:rounded-full border border-slate-200/90 bg-white p-2 shadow-sm sm:flex-row sm:items-center focus-within:border-orange-400 focus-within:ring-2 focus-within:ring-orange-100 transition"
      onSubmit={handleSubmit}
    >
      <div className="relative flex-1">
        <Search
          className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
          size={20}
        />
        <input
          type="search"
          value={value}
          placeholder="Yemek, restoran veya mutfak türü ara (örn: Döner, Kadıköy, Baklava)..."
          className="w-full rounded-full bg-transparent py-3 pl-12 pr-4 text-sm font-medium text-slate-900 outline-none placeholder:text-slate-400"
          onChange={(event) => onChange(event.target.value)}
        />
      </div>
      <button
        type="submit"
        disabled={isLoading}
        className="rounded-full bg-orange-500 px-6 py-3 text-sm font-bold text-white shadow-sm transition hover:bg-orange-600 active:scale-95 disabled:cursor-not-allowed disabled:bg-orange-300 sm:px-8"
      >
        {isLoading ? 'Aranıyor...' : 'Ara'}
      </button>
    </form>
  )
}

