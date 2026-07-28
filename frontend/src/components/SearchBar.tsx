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
      className="flex flex-col gap-3 rounded-[1.5rem] border border-slate-200 bg-white p-4 shadow-sm sm:flex-row"
      onSubmit={handleSubmit}
    >
      <label className="relative flex-1">
        <Search
          className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"
          size={18}
        />
        <input
          type="search"
          value={value}
          placeholder="Search by restaurant name or dish"
          className="w-full rounded-full border border-slate-200 py-3 pl-11 pr-4 text-sm text-slate-900 outline-none transition focus:border-orange-400"
          onChange={(event) => onChange(event.target.value)}
        />
      </label>
      <button
        type="submit"
        disabled={isLoading}
        className="rounded-full bg-orange-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-600 disabled:cursor-not-allowed disabled:bg-orange-300"
      >
        Search
      </button>
    </form>
  )
}
