import type { JSX } from 'react'

export function RestaurantCardSkeleton(): JSX.Element {
  return (
    <article className="flex h-full animate-pulse flex-col overflow-hidden rounded-[1.5rem] border border-slate-200 bg-white shadow-sm">
      <div className="h-40 w-full bg-slate-100 sm:h-44" />
      <div className="flex flex-1 flex-col gap-4 p-5">
        <div className="space-y-3">
          <div className="h-6 w-3/4 rounded bg-slate-100" />
          <div className="h-4 w-1/2 rounded bg-slate-100" />
        </div>
        <div className="space-y-2">
          <div className="h-4 w-2/3 rounded bg-slate-100" />
          <div className="h-4 w-1/3 rounded bg-slate-100" />
        </div>
        <div className="mt-auto h-10 w-32 rounded-full bg-slate-100" />
      </div>
    </article>
  )
}

