const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

function handleErrorResponse(res: Response): never {
  throw new Error(`${res.status}`)
}

function dispatchApiError(res: Response, text: string) {
  if (typeof window === 'undefined') return
  if (res.status === 401) {
    window.location.href = '/'
  }
  if (res.status >= 500) {
    window.dispatchEvent(
      new CustomEvent('api-error', { detail: `Server error (${res.status}) — please try again` }),
    )
  }
}

export async function apiFetch<T>(
  path: string,
  getToken: () => Promise<string | null>,
  options: RequestInit = {},
): Promise<T> {
  const token = await getToken()
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    dispatchApiError(res, text)
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export async function apiUpload<T>(
  path: string,
  getToken: () => Promise<string | null>,
  body: FormData,
): Promise<T> {
  const token = await getToken()
  // Do not set Content-Type — browser sets it with the multipart boundary automatically
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    dispatchApiError(res, text)
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}
