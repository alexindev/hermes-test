import { useState, useEffect } from 'react'

const API = '/api'

export default function App() {
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [sellers, setSellers] = useState([])
  const [orders, setOrders] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      fetch(`${API}/products/`).then(r => r.json()),
      fetch(`${API}/products/categories`).then(r => r.json()),
      fetch(`${API}/products/sellers`).then(r => r.json()),
      fetch(`${API}/orders/`).then(r => r.json()),
      fetch(`${API}/users/`).then(r => r.json()),
    ])
      .then(([products, categories, sellers, orders, users]) => {
        setProducts(products)
        setCategories(categories)
        setSellers(sellers)
        setOrders(orders)
        setUsers(users)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) return <div className="app"><div className="loading">Загрузка...</div></div>
  if (error) return <div className="app"><div className="error">Ошибка: {error}</div></div>

  return (
    <div className="app">
      <header>
        <div className="app" style={{padding:'0'}}>
          <h1>🛒 Маркетплейс — Панель</h1>
          <span style={{opacity:0.8}}>Данные из БД bigdata</span>
        </div>
      </header>

      <div className="stats">
        <div className="stat-card">
          <h3>Товары</h3>
          <div className="value">{products.length}</div>
        </div>
        <div className="stat-card">
          <h3>Категории</h3>
          <div className="value">{categories.length}</div>
        </div>
        <div className="stat-card">
          <h3>Продавцы</h3>
          <div className="value">{sellers.length}</div>
        </div>
        <div className="stat-card">
          <h3>Заказы</h3>
          <div className="value">{orders.length}</div>
        </div>
        <div className="stat-card">
          <h3>Пользователи</h3>
          <div className="value">{users.length}</div>
        </div>
      </div>

      <div className="table-section">
        <h2>📦 Последние заказы</h2>
        <table>
          <thead>
            <tr><th>ID</th><th>Статус</th><th>Сумма</th></tr>
          </thead>
          <tbody>
            {orders.map(o => (
              <tr key={o.id}>
                <td style={{fontFamily:'monospace',fontSize:12}}>{o.id.slice(0,8)}...</td>
                <td><span className={`badge badge-${o.status}`}>{o.status}</span></td>
                <td>{o.total_amount ? `${Number(o.total_amount).toLocaleString('ru-RU')} ₽` : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="table-section">
        <h2>🏷️ Категории</h2>
        <table>
          <thead><tr><th>ID</th><th>Название</th></tr></thead>
          <tbody>
            {categories.map(c => (
              <tr key={c.id}><td style={{fontFamily:'monospace',fontSize:12}}>{c.id.slice(0,8)}...</td><td>{c.name}</td></tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="table-section">
        <h2>👥 Продавцы</h2>
        <table>
          <thead><tr><th>ID</th><th>Имя</th><th>Email</th></tr></thead>
          <tbody>
            {sellers.map(s => (
              <tr key={s.id}>
                <td style={{fontFamily:'monospace',fontSize:12}}>{s.id.slice(0,8)}...</td>
                <td>{s.name}</td>
                <td>{s.email}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="table-section">
        <h2>📋 Пользователи</h2>
        <table>
          <thead><tr><th>ID</th><th>Email</th><th>Имя</th><th>Регион</th></tr></thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id}>
                <td style={{fontFamily:'monospace',fontSize:12}}>{u.id.slice(0,8)}...</td>
                <td>{u.email}</td>
                <td>{u.full_name || '—'}</td>
                <td>{u.region || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
