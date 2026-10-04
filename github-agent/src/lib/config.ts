export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL as string // set in next.config.js from ports.json

export function authHeaders(token?: string | null): HeadersInit {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }
  return headers
}
