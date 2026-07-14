import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCartStore } from '@stores/cartStore'
import { useAuthStore } from '@stores/authStore'
import { orderApi, paymentApi } from '@api/client'

export default function Checkout() {
  const navigate = useNavigate()
  const cart = useCartStore((state) => state.cart)
  const user = useAuthStore((state) => state.user)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    street: user?.address?.street || '',
    city: user?.address?.city || '',
    state: user?.address?.state || '',
    zip: user?.address?.zip || '',
    country: user?.address?.country || '',
  })

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      if (!cart) throw new Error('Cart is empty')
      if (!user) {
        navigate('/auth/login')
        return
      }

      // Create order
      const order = await orderApi.create({
        cart_id: cart.id,
        shipping_address: formData,
      })

      // Create payment intent
      await paymentApi.createIntent({ order_id: order.id })

      // TODO: Integrate Stripe payment
      // For now, just redirect to success page
      alert('Order created! Payment integration coming soon.')
      navigate(`/orders/${order.id}`)
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'response' in err) {
        const response = (err as { response?: { data?: { message?: string } } }).response
        setError(response?.data?.message || 'Failed to place order')
      } else {
        setError('Failed to place order')
      }
    } finally {
      setIsLoading(false)
    }
  }

  if (!cart || !cart.items.length) {
    return (
      <div className="container text-center py-12">
        <p className="text-gray-500">Your cart is empty</p>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="container text-center py-12">
        <p className="text-gray-500">Please log in to checkout</p>
      </div>
    )
  }

  return (
    <div className="container">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Checkout</h1>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Form */}
        <div className="lg:col-span-2">
          <form onSubmit={handlePlaceOrder} className="space-y-6">
            {error && (
              <div className="card bg-red-50 border border-red-200 text-red-700 p-4">
                {error}
              </div>
            )}

            <div className="card p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Shipping Address</h2>
              <div className="space-y-4">
                <input
                  type="text"
                  name="street"
                  placeholder="Street Address"
                  value={formData.street}
                  onChange={handleInputChange}
                  className="input"
                  required
                />
                <div className="grid gap-4 md:grid-cols-2">
                  <input
                    type="text"
                    name="city"
                    placeholder="City"
                    value={formData.city}
                    onChange={handleInputChange}
                    className="input"
                    required
                  />
                  <input
                    type="text"
                    name="state"
                    placeholder="State"
                    value={formData.state}
                    onChange={handleInputChange}
                    className="input"
                    required
                  />
                </div>
                <div className="grid gap-4 md:grid-cols-2">
                  <input
                    type="text"
                    name="zip"
                    placeholder="ZIP Code"
                    value={formData.zip}
                    onChange={handleInputChange}
                    className="input"
                    required
                  />
                  <input
                    type="text"
                    name="country"
                    placeholder="Country"
                    value={formData.country}
                    onChange={handleInputChange}
                    className="input"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="card p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Payment Method</h2>
              <p className="text-gray-600 mb-4">Stripe payment integration coming soon</p>
              <div className="border border-gray-300 rounded-lg p-6 text-center text-gray-500">
                Payment form will appear here
              </div>
            </div>

            <button type="submit" disabled={isLoading} className="btn-primary btn-lg w-full">
              {isLoading ? 'Processing...' : 'Place Order'}
            </button>
          </form>
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <div className="card p-6 sticky top-24">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Order Summary</h2>

            <div className="space-y-3 mb-6 pb-6 border-b border-gray-200">
              {cart.items.map((item, idx) => (
                <div key={idx} className="flex justify-between text-sm">
                  <span className="text-gray-600">
                    {item.product_name} × {item.quantity}
                  </span>
                  <span className="font-semibold">${item.subtotal.toFixed(2)}</span>
                </div>
              ))}
            </div>

            <div className="space-y-3">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal</span>
                <span>${cart.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Tax</span>
                <span>${cart.tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Shipping</span>
                <span>${cart.shipping.toFixed(2)}</span>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between">
              <span className="font-bold text-gray-900">Total</span>
              <span className="text-2xl font-bold text-primary-600">${cart.total.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
