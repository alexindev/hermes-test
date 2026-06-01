import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getSellers, type Seller } from '../api/client'

export default function SellersPage() {
  const [sellers, setSellers] = useState<Seller[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getSellers()
      .then(setSellers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading">Загрузка...</div>
  if (error) return <div className="error">Ошибка: {error}</div>

  return (
    <div>
      <h2 style={{ marginBottom: 20 }}>Продавцы</h2>
      <div className="seller-grid">
        {sellers.map((s) => (
          <div key={s.id} className="seller-card">
            <h3>{s.name}</h3>
            <div className="meta" style={{ fontSize: 13, color: 'var(--text2)', marginBottom: 8 }}>
              {s.email}
            </div>
            <div className="stats">
              <span>🏪 {s.store_count} магазинов</span>
              <span>📦 {s.product_count} товаров</span>
              {s.rating != null && s.rating > 0 && (
                <span className="rating">★ {s.rating} ({s.review_count})</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}