import { useEffect, useState } from 'react'
import './App.css'
import { OrderForm } from './OrderForm'
import { StaffDashboard } from './StaffDashboard'

type View = 'order' | 'staff'

// #/staff opens the staff dashboard; anything else is the customer order form.
const viewFromHash = (): View => (window.location.hash === '#/staff' ? 'staff' : 'order')

function App() {
  const [view, setView] = useState<View>(viewFromHash)

  useEffect(() => {
    const onHashChange = () => setView(viewFromHash())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  return (
    <>
      <header className="app-header">
        <h1>Food Order Queue</h1>
        <nav>
          <a href="#/" className={view === 'order' ? 'active' : ''}>Customer</a>
          <a href="#/staff" className={view === 'staff' ? 'active' : ''}>Staff</a>
        </nav>
      </header>
      <main>{view === 'staff' ? <StaffDashboard /> : <OrderForm />}</main>
    </>
  )
}

export default App
