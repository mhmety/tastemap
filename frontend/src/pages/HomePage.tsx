import { ArrowRight, MapPinned, Search, Star } from 'lucide-react'
import type { JSX } from 'react'
import { Link } from 'react-router-dom'

import { usePageTitle } from '../hooks/usePageTitle'

const highlights = [
  {
    icon: Search,
    title: 'Explore by craving',
    description: 'Start with a dish, neighborhood, or cuisine and discover places worth visiting.',
  },
  {
    icon: Star,
    title: 'Collect favorites',
    description: 'Save the restaurants you want to revisit once authentication is connected.',
  },
  {
    icon: MapPinned,
    title: 'Plan food routes',
    description: 'Build a clear browsing experience for city-based restaurant discovery.',
  },
]

export function HomePage(): JSX.Element {
  usePageTitle('Home')

  return (
    <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:px-8">
      <section className="grid gap-10 rounded-[2rem] border border-slate-200 bg-white p-8 shadow-sm lg:grid-cols-[1.2fr_0.8fr] lg:p-12">
        <div className="space-y-6">
          <span className="inline-flex rounded-full bg-orange-100 px-4 py-1 text-sm font-medium text-orange-700">
            TasteMap Frontend Foundation
          </span>
          <div className="space-y-4">
            <h1 className="text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
              Discover food first, then the places behind it.
            </h1>
            <p className="max-w-2xl text-lg text-slate-600">
              This first frontend sprint sets up the navigation, shared layout, routing, and API
              client structure for the TasteMap experience.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              className="inline-flex items-center justify-center gap-2 rounded-full bg-orange-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-orange-600"
              to="/restaurants"
            >
              Browse Restaurants
              <ArrowRight size={16} />
            </Link>
            <Link
              className="inline-flex items-center justify-center rounded-full border border-slate-200 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-orange-200 hover:text-orange-600"
              to="/register"
            >
              Create an Account
            </Link>
          </div>
        </div>

        <div className="rounded-[1.5rem] bg-slate-50 p-6">
          <div className="space-y-4">
            <div className="rounded-2xl border border-white bg-white p-4 shadow-sm">
              <p className="text-sm font-medium text-slate-500">Frontend stack</p>
              <p className="mt-2 text-lg font-semibold text-slate-900">
                Vite, React, TypeScript, Router, Axios, TailwindCSS, Lucide
              </p>
            </div>
            <div className="rounded-2xl border border-dashed border-orange-200 bg-orange-50 p-4 text-sm text-orange-800">
              Authentication forms and business logic are intentionally left unconnected in this
              sprint so the project can focus on structure first.
            </div>
          </div>
        </div>
      </section>

      <section className="mt-12 grid gap-6 md:grid-cols-3">
        {highlights.map((item) => {
          const Icon = item.icon

          return (
            <article
              key={item.title}
              className="rounded-[1.5rem] border border-slate-200 bg-white p-6 shadow-sm"
            >
              <span className="inline-flex rounded-2xl bg-slate-100 p-3 text-slate-700">
                <Icon size={20} />
              </span>
              <h2 className="mt-4 text-xl font-semibold text-slate-900">{item.title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">{item.description}</p>
            </article>
          )
        })}
      </section>
    </div>
  )
}
