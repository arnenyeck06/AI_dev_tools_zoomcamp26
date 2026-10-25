import { useState, type FormEvent } from 'react'
import { api, type Order } from './api'
import { usePolling } from './usePolling'

const MENU = ['Burger', 'Cheeseburger', 'Veggie wrap', 'Chicken sandwich', 'Fries', 'Salad', 'Milkshake', 'Soda']

const EMPTY = { customer_name: '', phone: '', item: MENU[0], quantity: 1, note: '' }

export function OrderForm() {
  const [form, setForm] = useState(EMPTY)
  const [ticket, setTicket] = useState<Order | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Keep the ticket's place in line up to date until the order is done.
  usePolling(
    () => {
      if (ticket) api.getOrder(ticket.id).then(setTicket).catch(() => {})
    },
    5000,
    ticket !== null && ticket.status !== 'done',
  )

  async function submit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      setTicket(await api.placeOrder({ ...form, note: form.note.trim() || undefined }))
      setForm(EMPTY)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  if (ticket) return <Ticket order={ticket} onNewOrder={() => setTicket(null)} />

  const set = (field: keyof typeof EMPTY) => (e: { target: { value: string } }) =>
    setForm({ ...form, [field]: field === 'quantity' ? Number(e.target.value) : e.target.value })

  return (
    <form className="card order-form" onSubmit={submit}>
      <h2>Place an order</h2>
      <label>
        Name
        <input required maxLength={80} value={form.customer_name} onChange={set('customer_name')} autoComplete="name" />
      </label>
      <label>
        Phone
        <input required minLength={7} maxLength={20} type="tel" value={form.phone} onChange={set('phone')} autoComplete="tel" />
      </label>
      <div className="row">
        <label className="grow">
          Item
          <select value={form.item} onChange={set('item')}>
            {MENU.map((item) => <option key={item}>{item}</option>)}
          </select>
        </label>
        <label className="qty">
          Qty
          <input required type="number" min={1} max={100} value={form.quantity} onChange={set('quantity')} />
        </label>
      </div>
      <label>
        <span>
          Note <span className="hint">(optional)</span>
        </span>
        <textarea maxLength={500} rows={2} value={form.note} onChange={set('note')} placeholder="No onions, extra sauce…" />
      </label>
      {error && <p className="error" role="alert">{error}</p>}
      <button type="submit" disabled={submitting}>{submitting ? 'Placing order…' : 'Place order'}</button>
    </form>
  )
}

function Ticket({ order, onNewOrder }: { order: Order; onNewOrder: () => void }) {
  const message = {
    waiting: order.position === 1 ? "You're next!" : `You're #${order.position} in line`,
    in_progress: 'Your order is being prepared',
    done: 'Your order is ready, please pick it up',
  }[order.status]

  return (
    <div className="card ticket" aria-live="polite">
      <p className="ticket-label">Ticket</p>
      <p className="ticket-number">#{order.id}</p>
      <p className={`ticket-status status-${order.status}`}>{message}</p>
      <p className="hint">
        {order.quantity} × {order.item} for {order.customer_name}
      </p>
      <button className="secondary" onClick={onNewOrder}>Place another order</button>
    </div>
  )
}
