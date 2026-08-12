import axios from 'axios'

interface PydanticErrorItem {
  type?: unknown
  loc?: unknown
  msg?: unknown
  input?: unknown
  ctx?: unknown
}

type FastApiDetailShape =
  | string
  | PydanticErrorItem[]
  | undefined

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isPydanticItem(value: unknown): value is PydanticErrorItem {
  return isRecord(value) && 'msg' in value
}

function normalizeDetail(detail: FastApiDetailShape, fallback: string): string {
  if (typeof detail === 'string' && detail.length > 0) {
    return detail
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .filter((item): item is PydanticErrorItem => isPydanticItem(item))
      .map((item) => item.msg)
      .filter((msg): msg is string => typeof msg === 'string' && msg.length > 0)

    if (messages.length === 1) {
      return messages[0]
    }

    if (messages.length > 1) {
      return messages.join('\n- ').replace(/^/, '- ')
    }
  }

  return fallback
}

export function normalizeApiErrorMessage(
  error: unknown,
  fallback: string = 'Something went wrong. Please try again.',
): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data

    if (typeof data === 'string' && data.length > 0) {
      return data
    }

    if (isRecord(data)) {
      if (typeof data.detail === 'string' && data.detail.length > 0) {
        return data.detail
      }

      if (Array.isArray(data.detail)) {
        return normalizeDetail(data.detail, fallback)
      }

      if (typeof data.message === 'string' && data.message.length > 0) {
        return data.message
      }

      if (typeof data.error === 'string' && data.error.length > 0) {
        return data.error
      }

      if (typeof data.msg === 'string' && data.msg.length > 0) {
        return data.msg
      }
    }

    if (typeof error.message === 'string' && error.message.length > 0) {
      return error.message
    }

    return fallback
  }

  if (error instanceof Error && typeof error.message === 'string' && error.message.length > 0) {
    return error.message
  }

  if (typeof error === 'string' && error.length > 0) {
    return error
  }

  return fallback
}
