import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '@stores/authStore'
import { useCartStore } from '@stores/cartStore'

// Layouts
import MainLayout from '@components/layout/MainLayout'
import AuthLayout from '@components/layout/AuthLayout'

// Pages
import Home from '@pages/Home'
import ProductList from '@pages/ProductList'
import ProductDetail from '@pages/ProductDetail'
import Cart from '@pages/Cart'
import Checkout from '@pages/Checkout'
import Orders from '@pages/Orders'
import OrderDetail from '@pages/OrderDetail'
import Login from '@pages/auth/Login'
import Register from '@pages/auth/Register'
import Account from '@pages/Account'
import NotFound from '@pages/NotFound'

function App() {
  const token = useAuthStore((state) => state.token)
  const initCart = useCartStore((state) => state.initCart)

  // Initialize cart on mount
  useEffect(() => {
    const initializeApp = async () => {
      await initCart()
    }
    initializeApp()
  }, [])

  return (
    <Router>
      <Routes>
        {/* Auth Routes */}
        <Route element={<AuthLayout />}>
          <Route path="/auth/login" element={<Login />} />
          <Route path="/auth/register" element={<Register />} />
        </Route>

        {/* Main Routes */}
        <Route element={<MainLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<ProductList />} />
          <Route path="/products/:id" element={<ProductDetail />} />
          <Route path="/cart" element={<Cart />} />
          <Route path="/checkout" element={<Checkout />} />
          
          {/* Protected Routes */}
          {token && (
            <>
              <Route path="/orders" element={<Orders />} />
              <Route path="/orders/:id" element={<OrderDetail />} />
              <Route path="/account" element={<Account />} />
            </>
          )}

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
