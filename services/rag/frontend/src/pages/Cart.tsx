import { Link } from 'react-router-dom'
import { useCartStore } from '@stores/cartStore'

export default function Cart() {
  const cart = useCartStore((state) => state.cart)
  const updateItem = useCartStore((state) => state.updateItem)
  const removeItem = useCartStore((state) => state.removeItem)

  if (!cart || cart.items.length === 0) {
    return (
      <div className="container text-center py-16">
        <svg className="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
        <h1 className="text-2xl font-bold text-gray-900">Your cart is empty</h1>
        <p className="mt-2 text-gray-600">Start shopping to add items to your cart</p>
        <Link to="/products" className="btn-primary btn-md mt-6">
          Continue Shopping
        </Link>
      </div>
    )
  }

  return (
    <div className="container">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Shopping Cart</h1>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Items */}
        <div className="lg:col-span-2 space-y-4">
          {cart.items.map((item, idx) => (
            <div key={idx} className="card p-6 flex gap-6">
              <div className="h-24 w-24 bg-gray-100 rounded-lg flex-shrink-0">
                {/* Product image would go here */}
              </div>

              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{item.product_name}</h3>
                <p className="text-gray-600">${item.price.toFixed(2)} each</p>

                <div className="mt-4 flex items-center gap-4">
                  <div className="flex items-center border border-gray-300 rounded-lg">
                    <button
                      onClick={() => updateItem(idx, Math.max(1, item.quantity - 1))}
                      className="px-3 py-1 text-gray-600 hover:text-gray-900"
                    >
                      −
                    </button>
                    <span className="px-4 py-1">{item.quantity}</span>
                    <button
                      onClick={() => updateItem(idx, item.quantity + 1)}
                      className="px-3 py-1 text-gray-600 hover:text-gray-900"
                    >
                      +
                    </button>
                  </div>

                  <button
                    onClick={() => removeItem(idx)}
                    className="text-red-600 hover:text-red-700 font-medium"
                  >
                    Remove
                  </button>
                </div>
              </div>

              <div className="text-right">
                <p className="text-lg font-bold text-gray-900">${item.subtotal.toFixed(2)}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="lg:col-span-1">
          <div className="card p-6 sticky top-24">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Order Summary</h2>

            <div className="space-y-4 border-b border-gray-200 pb-4">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span className="font-semibold">${cart.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tax</span>
                <span className="font-semibold">${cart.tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Shipping</span>
                <span className="font-semibold">${cart.shipping.toFixed(2)}</span>
              </div>
            </div>

            <div className="mt-4 mb-6 flex justify-between">
              <span className="text-lg font-bold text-gray-900">Total</span>
              <span className="text-2xl font-bold text-primary-600">${cart.total.toFixed(2)}</span>
            </div>

            <Link to="/checkout" className="btn-primary btn-lg w-full">
              Proceed to Checkout
            </Link>

            <Link to="/products" className="btn-secondary btn-lg w-full mt-3">
              Continue Shopping
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
