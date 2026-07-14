import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { productApi } from '@api/client'
import type { PaginatedResponse, Product } from '@/types'
import { Link } from 'react-router-dom'

export default function ProductList() {
  const [filters, setFilters] = useState({
    skip: 0,
    limit: 12,
    search: '',
    min_price: undefined as number | undefined,
    max_price: undefined as number | undefined,
    sort_by: 'created_at',
    sort_order: 'desc',
  })

  const { data: result, isLoading } = useQuery({
    queryKey: ['products', filters],
    queryFn: (): Promise<PaginatedResponse<Product>> => productApi.list(filters),
  })

  const handleSearch = (value: string) => {
    setFilters({ ...filters, search: value, skip: 0 })
  }

  const handlePriceFilter = (min?: number, max?: number) => {
    setFilters({ ...filters, min_price: min, max_price: max, skip: 0 })
  }

  return (
    <div className="container">
      <div className="flex gap-8">
        {/* Sidebar Filters */}
        <aside className="w-64">
          <div className="card p-6 space-y-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Search</h3>
              <input
                type="text"
                placeholder="Search products..."
                value={filters.search}
                onChange={(e) => handleSearch(e.target.value)}
                className="input"
              />
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Price Range</h3>
              <div className="space-y-2">
                <div className="flex gap-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={filters.min_price || ''}
                    onChange={(e) => handlePriceFilter(e.target.value ? parseFloat(e.target.value) : undefined, filters.max_price)}
                    className="input w-1/2"
                  />
                  <input
                    type="number"
                    placeholder="Max"
                    value={filters.max_price || ''}
                    onChange={(e) => handlePriceFilter(filters.min_price, e.target.value ? parseFloat(e.target.value) : undefined)}
                    className="input w-1/2"
                  />
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Sort By</h3>
              <select
                value={filters.sort_by}
                onChange={(e) => setFilters({ ...filters, sort_by: e.target.value })}
                className="input"
              >
                <option value="created_at">Newest</option>
                <option value="price">Price (Low to High)</option>
                <option value="rating">Rating</option>
                <option value="name">Name</option>
              </select>
            </div>
          </div>
        </aside>

        {/* Products Grid */}
        <main className="flex-1">
          {isLoading ? (
            <div className="flex items-center justify-center h-96">
              <div className="loading"></div>
            </div>
          ) : result?.items.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">No products found</p>
            </div>
          ) : (
            <>
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {result?.items.map((product: Product) => (
                  <Link
                    key={product.id}
                    to={`/products/${product.id}`}
                    className="group card overflow-hidden hover:shadow-lg"
                  >
                    <div className="relative h-64 overflow-hidden bg-gray-100">
                      {product.images?.[0]?.url ? (
                        <img
                          src={product.images[0].url}
                          alt={product.name}
                          className="h-full w-full object-cover group-hover:scale-110 transition-transform duration-300"
                        />
                      ) : (
                        <div className="h-full w-full flex items-center justify-center text-gray-400">
                          No image
                        </div>
                      )}
                    </div>
                    <div className="p-4">
                      <h3 className="font-semibold text-gray-900 group-hover:text-primary-600">{product.name}</h3>
                      <p className="mt-2 text-lg font-bold text-gray-900">${product.price.toFixed(2)}</p>
                      <div className="mt-2 flex items-center justify-between">
                        <span className="text-sm text-yellow-500">★ {product.rating.toFixed(1)}</span>
                        <span className="text-sm text-gray-500">({product.stock_qty})</span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>

              {/* Pagination */}
              {result && (
                <div className="mt-8 flex items-center justify-center gap-4">
                  <button
                    disabled={filters.skip === 0}
                    onClick={() => setFilters({ ...filters, skip: Math.max(0, filters.skip - filters.limit) })}
                    className="btn-secondary btn-md disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="text-gray-600">
                    Page {Math.floor(filters.skip / filters.limit) + 1} of {Math.ceil(result.total / filters.limit)}
                  </span>
                  <button
                    disabled={filters.skip + filters.limit >= result.total}
                    onClick={() => setFilters({ ...filters, skip: filters.skip + filters.limit })}
                    className="btn-secondary btn-md disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  )
}
