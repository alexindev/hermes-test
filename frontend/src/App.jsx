import { useState, useEffect } from 'react'

function App() {
  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [orders, setOrders] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsRes, usersRes, ordersRes, catsRes] = await Promise.all([
          fetch('/api/stats'),
          fetch('/api/users?limit=10'),
          fetch('/api/orders?limit=10'),
          fetch('/api/categories'),
        ])

        if (!statsRes.ok || !usersRes.ok || !ordersRes.ok || !catsRes.ok) {
          throw new Error('Failed to fetch data')
        }

        setStats(await statsRes.json())
        setUsers(await usersRes.json())
        setOrders(await ordersRes.json())
        setCategories(await catsRes.json())
        setLoading(false)
      } catch (err) {
        setError(err.message)
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  if (loading) return <div className="app">Loading...</div>
  if (error) return <div className="app error">Error: {error}</div>

  return (
    <div className="app">
      <header className="header">
        <h1>🚀 Hermes Test</h1>
        <p className="subtitle">FastAPI + React + PostgreSQL</p>
      </header>

      {/* Stats */}
      {stats && (
        <section className="stats">
          <div className="stat-card">
            <span className="stat-value">{stats.users}</span>
            <span className="stat-label">Users</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.orders}</span>
            <span className="stat-label">Orders</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.products}</span>
            <span className="stat-label">Products</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{stats.categories}</span>
            <span className="stat-label">Categories</span>
          </div>
        </section>
      )}

      {/* Categories */}
      {categories.length > 0 && (
        <section className="section">
          <h2>📂 Categories ({categories.length})</h2>
          <div className="tags">
            {categories.map((c) => (
              <span key={c.id} className="tag">{c.name}</span>
            ))}
          </div>
        </section>
      )}

      {/* Users */}
      <section className="section">
        <h2>👥 Recent Users</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Name</th>
              <th>Region</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>{u.email}</td>
                <td>{u.full_name}</td>
                <td>{u.region}</td>
                <td>{new Date(u.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* Orders */}
      <section className="section">
        <h2>📦 Recent Orders</h2>
        <table className="table">
          <thead>
            <tr>
              <th>User ID</th>
              <th>Status</th>
              <th>Amount</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id}>
                <td>{o.user_id.slice(0, 8)}...</td>
                <td><span className={`badge badge-${o.status.toLowerCase().replace(/\s+/g, '-')}`}>{o.status}</span></td>
                <td>{o.total_amount.toLocaleString()} ₽</td>
                <td>{new Date(o.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  )
}

export default App
