import { useQuery } from '@tanstack/react-query'
import { orderApi } from '@api/client'
import { Link } from 'react-router-dom'
import type { OrderListItem, PaginatedResponse } from '@/types'

export default function Orders() {
  const { data: result, isLoading } = useQuery({
    queryKey: ['orders'],
    queryFn: (): Promise<PaginatedResponse<OrderListItem>> => orderApi.list({ limit: 50 }),
  })

  if (isLoading) {
    return (
      <div className="container flex items-center justify-center h-96">
        <div className="loading"></div>
      </div>
    )
  }

  return (
    <div className="container">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">My Orders</h1>

      {!result?.items || result.items.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg">You haven't placed any orders yet</p>
          <Link to="/products" className="btn-primary btn-md mt-6">
            Start Shopping
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {result.items.map((order: OrderListItem) => (
            <Link
              key={order.id}
              to={`/orders/${order.id}`}
              className="card p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{order.order_number}</h3>
                  <p className="text-sm text-gray-600">{new Date(order.created_at).toLocaleDateString()}</p>
                </div>

                <div className="text-right">
                  <p className="text-lg font-bold text-gray-900">${order.total.toFixed(2)}</p>
                  <span className={`badge mt-2 ${getStatusColor(order.status)}`}>
                    {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

function getStatusColor(status: string) {
  const colors: Record<string, string> = {
    pending: 'badge-primary',
    paid: 'badge-success',
    shipped: 'badge-primary',
    delivered: 'badge-success',
    canceled: 'badge-primary',
    refunded: 'badge-primary',
  }
  return colors[status] || 'badge-primary'
}
