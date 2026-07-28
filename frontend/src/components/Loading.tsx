import type { JSX } from 'react'
import { LoaderCircle } from 'lucide-react'

interface LoadingProps {
  label?: string
}

export function Loading({ label = 'Loading restaurants...' }: LoadingProps): JSX.Element {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-[1.5rem] border border-slate-200 bg-white px-6 py-12 text-center shadow-sm">
      <LoaderCircle className="animate-spin text-orange-500" size={28} />
      <p className="text-sm font-medium text-slate-600">{label}</p>
    </div>
  )
}
