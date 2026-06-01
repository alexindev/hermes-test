import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getProduct, type ProductDetail } from '../api/client'

export default function ProductPage() {
  const { id } = useParams<{ id: string }>()
  const [product, setProduct] = useState<ProductDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    setLoading(true)
    setError(null)
    getProduct(id)
      .then(setProduct)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="loading">Загрузка...</div>
  if (error) return <div className="error">Ошибка: {error}</div>
  if (!product) return <div className="error">Товар не найден</div>

  return (
    <div>
      <Link to="/" className="back-btn">← Назад в каталог</Link>

      <div className="product-detail">
        <div className="info">
          <h2>{product.name}</h2>
          <div className="price-big">{Number(product.price).toLocaleString('ru-RU')} ₽</div>

          <dl className="fields">
            <dt>Категория</dt>
            <dd>{product.category_name || '—'}</dd>
            <dt>Магазин</dt>
            <dd>{product.store_name || '—'}</dd>
            <dt>Продавец</dt>
            <dd>{product.seller_name || '—'}</dd>
            <dt>Наличие</dt>
            <dd style={{ color: product.stock > 0 ? 'var(--green)' : 'var(--orange)' }}>
              {product.stock > 0 ? `${product.stock} шт.` : 'Нет в наличии'}
            </dd>
            {product.avg_rating != null && product.avg_rating > 0 && (
              <>
                <dt>Рейтинг</dt>
                <dd><span className="rating">★ {product.avg_rating}</span> ({product.review_count} отзывов)</dd>
              </>
            )}
          </dl>
        </div>
      </div>

      {product.reviews.length > 0 && (
        <div className="reviews-section">
          <h3>Отзывы ({product.review_count})</h3>
          {product.reviews.slice(0, 5).map((r) => (
            <div key={r.id} className="review-card">
              <span className="rating">{'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}</span>
              <span style={{ marginLeft: 8, color: 'var(--text2)', fontSize: 12 }}>
                {r.created_at ? new Date(r.created_at).toLocaleDateString('ru-RU') : ''}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}