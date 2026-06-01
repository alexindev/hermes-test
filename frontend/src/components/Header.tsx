import { Link, useLocation } from 'react-router-dom'

export default function Header() {
  const loc = useLocation()

  const isActive = (path: string) => loc.pathname === path || loc.pathname.startsWith(path + '/')

  return (
    <header className="header">
      <h1>🛒 Hermes Market</h1>
      <nav>
        <Link to="/" className={isActive('/') && !loc.pathname.startsWith('/sellers') ? 'active' : ''}>
          Каталог
        </Link>
        <Link to="/sellers" className={isActive('/sellers') ? 'active' : ''}>
          Продавцы
        </Link>
      </nav>
    </header>
  )
}
