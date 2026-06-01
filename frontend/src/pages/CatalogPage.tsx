import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getProducts, getCategories, type Product, type Category } from '../api/client'
import ProductCard from '../components/ProductCard'

const SORT_OPTIONS = [
  { value: 'name', label: 'По названию' },
  { value: 'price_asc', label: 'Сначала дешёвые' },
  { value: 'price_desc', label: 'Сначала дорогие' },
  { value: 'rating', label: 'По рейтингу' },
  { value: 'popular', label: 'По популярности' },
]

export default function CatalogPage() {
  const [params, setParams] = useSearchParams()
  const [products, setProducts] = useState<Product[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const categoryId = params.get('category_id') || undefined
  const search = params.get('search') || ''
  const sort = params.get('sort') || 'name'
  const page = parseInt(params.get('page') || '1', 10)

  useEffect(() => {
    getCategories().then(setCategories).catch(() => {})
  }, [])

  useEffect(() => {
    setLoading(true)
    setError(null)
    getProducts({ category_id: categoryId, search: search || undefined, sort, page, limit: 20 })
      .then(setProducts)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [categoryId, search, sort, page])

  const updateParam = (key: string, value: string) => {
    const next = new URLSearchParams(params)
    if (value) {
      next.set(key, value)
    } else {
      next.delete(key)
    }
    if (key !== 'page') next.delete('page')
    setParams(next)
  }

  return (
    <div className="catalog-layout">
      <aside className="sidebar">
        <h3>Категории</h3>
        <ul>
          <li>
            <Link
              to="?"
              className={!categoryId ? 'active' : ''}
              onClick={(e) => { e.preventDefault(); setParams(new URLSearchParams()) }}
            >
              Все товары
            </Link>
          </li>
          {categories.map((c) => (
            <li key={c.id}>
              <Link
                to={`?category_id=${c.id}`}
                className={categoryId === c.id ? 'active' : ''}
                onClick={(e) => { e.preventDefault(); updateParam('category_id', c.id) }}
              >
                {c.name} <span style={{ color: 'var(--text2)', fontSize: 11 }}>({c.product_count})</span>
              </Link>
            </li>
          ))}
        </ul>
      </aside>

      <main style={{ flex: 1 }}>
        <div className="controls">
          <input
            className="search-input"
            placeholder="Поиск товаров..."
            value={search}
            onChange={(e) => updateParam('search', e.target.value)}
          />
          <select
            className="sort-select"
            value={sort}
            onChange={(e) => updateParam('sort', e.target.value)}
          >
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>{o.label}</option>
            ))}
          </select>
        </div>

        {loading && <div className="loading">Загрузка...</div>}
        {error && <div className="error">Ошибка: {error}</div>}
        {!loading && !error && products.length === 0 && (
          <div className="loading">Товары не найдены</div>
        )}

        <div className="product-grid">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} />
          ))}
        </div>

        <div className="pagination">
          <button disabled={page <= 1} onClick={() => updateParam('page', String(page - 1))}>
            ← Назад
          </button>
          <button onClick={() => updateParam('page', String(page + 1))} disabled={products.length < 20}>
            Вперёд →
          </button>
        </div>
      </main>
    </div>
  )
}