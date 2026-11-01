// Client for the FastAPI backend. Requests go to /api, which Vite proxies to the backend.

export type OrderStatus = 'waiting' | 'in_progress' | 'done'

export interface NewOrder {
  customer_name: string
  phone: string
  item: string
  quantity: number
  note?: string
}

export type Severity = 'low' | 'medium' | 'high'

export interface Flag {
  source: 'rule' | 'ai'
  reason: string
  severity: Severity
}

export interface Order extends NewOrder {
  id: number
  status: OrderStatus
  created_at: string
  position: number | null
  flags: Flag[]
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(errorMessage(body) ?? `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

// FastAPI sends {detail: "..."} or, for validation errors, {detail: [{loc, msg}, ...]}.
function errorMessage(body: unknown): string | null {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: unknown[]; msg?: string }) => `${d.loc?.at(-1) ?? 'field'}: ${d.msg}`)
      .join('; ')
  }
  return null
}

export const api = {
  placeOrder: (order: NewOrder) =>
    request<Order>('/orders', { method: 'POST', body: JSON.stringify(order) }),
  getOrder: (id: number) => request<Order>(`/orders/${id}`),
  listOrders: () => request<Order[]>('/orders'),
  serveNext: () => request<Order>('/orders/next', { method: 'POST' }),
  completeOrder: (id: number) => request<Order>(`/orders/${id}/done`, { method: 'POST' }),
}

// The backend stores UTC times without a zone suffix; treat them as UTC.
export function parseTime(value: string): Date {
  return new Date(/Z|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`)
}

export function minutesSince(value: string, now = Date.now()): number {
  return Math.max(0, Math.floor((now - parseTime(value).getTime()) / 60000))
}
