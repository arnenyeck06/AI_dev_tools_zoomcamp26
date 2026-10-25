import { useState } from 'react'
import { api, minutesSince, type Order, type OrderStatus } from './api'
import { usePolling } from './usePolling'

const COLUMNS: { status: OrderStatus; title: string }[] = [
  { status: 'waiting', title: 'Waiting' },
  { status: 'in_progress', title: 'In progress' },
  { status: 'done', title: 'Done' },
]

export function StaffDashboard() {
  const [orders, setOrders] = useState<Order[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const refresh = () =>
    api.listOrders().then(
      (list) => {
        setOrders(list)
        setError(null)
      },
      (e: Error) => setError(`Can't reach the API: ${e.message}`),
    )
  usePolling(refresh, 3000)

  async function act(action: () => Promise<unknown>) {
    setBusy(true)
    try {
      await action()
      setError(null)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
      refresh()
    }
  }

  const byStatus = (status: OrderStatus) => orders.filter((o) => o.status === status)
  const waiting = byStatus('waiting')
  const averageWait = waiting.length
    ? Math.round(waiting.reduce((sum, o) => sum + minutesSince(o.created_at), 0) / waiting.length)
    : 0

  return (
    <div className="dashboard">
      <div className="toolbar">
        <div className="stats">
          <Stat label="Waiting" value={waiting.length} />
          <Stat label="In progress" value={byStatus('in_progress').length} />
          <Stat label="Done" value={byStatus('done').length} />
          <Stat label="Avg wait" value={`${averageWait} min`} />
        </div>
        <button onClick={() => act(api.serveNext)} disabled={busy || waiting.length === 0}>
          Serve next
        </button>
      </div>
      {error && <p className="error" role="alert">{error}</p>}

      <div className="columns">
        {COLUMNS.map(({ status, title }) => {
          // Waiting and in progress are oldest first (FIFO); done shows the most recent.
          const list = status === 'done' ? byStatus(status).reverse().slice(0, 10) : byStatus(status)
          return (
            <section key={status} className={`column column-${status}`}>
              <h3>
                {title} <span className="count">{byStatus(status).length}</span>
              </h3>
              {list.length === 0 && <p className="hint empty">No orders</p>}
              {list.map((order) => (
                <OrderCard
                  key={order.id}
                  order={order}
                  onDone={() => act(() => api.completeOrder(order.id))}
                  busy={busy}
                />
              ))}
            </section>
          )
        })}
      </div>
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat">
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  )
}

function OrderCard({ order, onDone, busy }: { order: Order; onDone: () => void; busy: boolean }) {
  return (
    <article className="order-card">
      <header>
        <span className="ticket-id">#{order.id}</span>
        {order.position !== null && <span className="position">{order.position === 1 ? 'Next' : `#${order.position} in line`}</span>}
        <span className="age">{minutesSince(order.created_at)} min</span>
      </header>
      <p className="order-item">
        {order.quantity} × {order.item}
      </p>
      <p className="hint">
        {order.customer_name} · {order.phone}
      </p>
      {order.note && <p className="note">“{order.note}”</p>}
      {order.status === 'in_progress' && (
        <button className="small" onClick={onDone} disabled={busy}>
          Mark done
        </button>
      )}
    </article>
  )
}
