import { Link } from 'react-router-dom'
import { useAuthStore } from '@stores/authStore'
import { useCartStore } from '@stores/cartStore'

export default function Header() {
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)
  const cart = useCartStore((state) => state.cart)

  const cartItemCount = cart?.items.reduce((sum, item) => sum + item.quantity, 0) || 0

  return (
    <header className="sticky top-0 z-50 border-b border-gray-200 bg-white shadow-sm">
      <div className="container flex items-center justify-between py-4">
        {/* Logo */}
        <Link to="/" className="flex items-center space-x-2">
          <div className="text-2xl font-bold text-primary-600">FashionStore</div>
        </Link>

        {/* Navigation */}
        <nav className="hidden md:flex items-center space-x-8">
          <Link to="/products" className="text-gray-700 hover:text-primary-600 font-medium">
            Shop
          </Link>
          {user && (
            <Link to="/orders" className="text-gray-700 hover:text-primary-600 font-medium">
              Orders
            </Link>
          )}
        </nav>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Cart */}
          <Link to="/cart" className="relative p-2 text-gray-700 hover:text-primary-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            {cartItemCount > 0 && (
              <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-secondary-500 rounded-full">
                {cartItemCount}
              </span>
            )}
          </Link>

          {/* User Menu */}
          {user ? (
            <div className="flex items-center space-x-4">
              <Link to="/account" className="text-gray-700 hover:text-primary-600 font-medium">
                {user.name}
              </Link>
              <button
                onClick={logout}
                className="text-gray-700 hover:text-red-600 font-medium"
              >
                Logout
              </button>
            </div>
          ) : (
            <div className="space-x-3">
              <Link to="/auth/login" className="btn-secondary btn-sm">
                Login
              </Link>
              <Link to="/auth/register" className="btn-primary btn-sm">
                Register
              </Link>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
