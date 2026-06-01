import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import CatalogPage from './pages/CatalogPage'
import ProductPage from './pages/ProductPage'
import SellersPage from './pages/SellersPage'

export default function App() {
  return (
    <>
      <Header />
      <div className="container">
        <Routes>
          <Route path="/" element={<CatalogPage />} />
          <Route path="/product/:id" element={<ProductPage />} />
          <Route path="/sellers" element={<SellersPage />} />
        </Routes>
      </div>
    </>
  )
}
