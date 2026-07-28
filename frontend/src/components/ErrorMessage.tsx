import type { JSX } from 'react'
import { AlertCircle } from 'lucide-react'

interface ErrorMessageProps {
  message: string
  onRetry?: () => void
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps): JSX.Element {
  return (
    <div className="rounded-[1.5rem] border border-red-200 bg-red-50 p-6 shadow-sm">
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 text-red-500" size={20} />
        <div className="space-y-3">
          <div>
            <h2 className="text-base font-semibold text-red-900">Something went wrong</h2>
            <p className="mt-1 text-sm text-red-700">{message}</p>
          </div>
          {onRetry ? (
            <button
              type="button"
              className="rounded-full bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-700"
              onClick={onRetry}
            >
              Try Again
            </button>
          ) : null}
        </div>
      </div>
    </div>
  )
}
