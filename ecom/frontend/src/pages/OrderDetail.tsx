import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { orderApi } from '@api/client'
import type { OrderItem } from '@/types'

export default function OrderDetail() {
  const { id } = useParams<{ id: string }>()
  const { data: order, isLoading } = useQuery({
    queryKey: ['order', id],
    queryFn: () => orderApi.getById(parseInt(id!)),
  })

  if (isLoading) {
    return (
      <div className="container flex items-center justify-center h-96">
        <div className="loading"></div>
      </div>
    )
  }

  if (!order) {
    return (
      <div className="container text-center py-12">
        <p className="text-gray-500">Order not found</p>
        <Link to="/orders" className="btn-primary btn-md mt-4">
          Back to Orders
        </Link>
      </div>
    )
  }

  return (
    <div className="container">
      <Link to="/orders" className="text-primary-600 hover:text-primary-700 font-medium mb-8 block">
        ← Back to Orders
      </Link>

      <div className="grid gap-8 md:grid-cols-3">
        <div className="md:col-span-2 space-y-6">
          {/* Order Header */}
          <div className="card p-6">
            <h1 className="text-2xl font-bold text-gray-900">{order.order_number}</h1>
            <p className="text-gray-600 mt-2">{new Date(order.created_at).toLocaleDateString()}</p>
            <span className="badge badge-success mt-4">
              {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
            </span>
          </div>

          {/* Items */}
          <div className="card p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Order Items</h2>
            <div className="space-y-4">
              {order.items.map((item: OrderItem, idx: number) => (
                <div key={idx} className="flex justify-between border-b border-gray-200 pb-4">
                  <div>
                    <h3 className="font-semibold text-gray-900">{item.product_name}</h3>
                    <p className="text-gray-600">${item.unit_price.toFixed(2)} × {item.quantity}</p>
                  </div>
                  <p className="font-semibold text-gray-900">${item.subtotal.toFixed(2)}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Shipping Address */}
          <div className="card p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Shipping Address</h2>
            <div className="text-gray-600">
              <p>{order.shipping_address.street}</p>
              <p>{order.shipping_address.city}, {order.shipping_address.state} {order.shipping_address.zip}</p>
              <p>{order.shipping_address.country}</p>
            </div>
            {order.tracking_number && (
              <div className="mt-4">
                <p className="font-semibold text-gray-900">Tracking Number</p>
                <p className="text-gray-600 font-mono">{order.tracking_number}</p>
              </div>
            )}
          </div>
        </div>

        {/* Summary */}
        <div className="md:col-span-1">
          <div className="card p-6 sticky top-24">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Order Summary</h2>

            <div className="space-y-3 border-b border-gray-200 pb-4">
              <div className="flex justify-between">
                <span className="text-gray-600">Subtotal</span>
                <span>${order.subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tax</span>
                <span>${order.tax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Shipping</span>
                <span>${order.shipping.toFixed(2)}</span>
              </div>
              {order.discount && (
                <div className="flex justify-between text-green-600">
                  <span>Discount</span>
                  <span>-${order.discount.toFixed(2)}</span>
                </div>
              )}
            </div>

            <div className="mt-4 flex justify-between">
              <span className="font-bold text-gray-900">Total</span>
              <span className="text-2xl font-bold text-primary-600">${order.total.toFixed(2)}</span>
            </div>

            {order.status === 'pending' && (
              <button className="btn-primary btn-lg w-full mt-6">
                Complete Payment
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
