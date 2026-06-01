import { useNavigate } from 'react-router-dom'
import type { Product } from '../api/client'

interface Props {
  product: Product
}

export default function ProductCard({ product }: Props) {
  const nav = useNavigate()

  return (
    <div className="product-card" onClick={() => nav(`/product/${product.id}`)}>
      <div className="name">{product.name}</div>
      <div className="price">{Number(product.price).toLocaleString('ru-RU')} ₽</div>
      <div className="meta">
        {product.category_name && <span>{product.category_name}</span>}
        {product.avg_rating != null && product.avg_rating > 0 && (
          <span className="rating">★ {product.avg_rating}</span>
        )}
        {product.review_count > 0 && <span>({product.review_count})</span>}
      </div>
      <div className={`stock ${product.stock > 0 ? 'in' : 'out'}`}>
        {product.stock > 0 ? `В наличии: ${product.stock} шт.` : 'Нет в наличии'}
      </div>
    </div>
  )
}
