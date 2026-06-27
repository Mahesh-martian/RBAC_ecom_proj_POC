import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { productApi } from '@api/client'
import { useCartStore } from '@stores/cartStore'
import type { ProductReview } from '@/types'

export default function ProductDetail() {
  const { id } = useParams<{ id: string }>()
  const [quantity, setQuantity] = useState(1)
  const addItem = useCartStore((state) => state.addItem)

  const { data: product, isLoading } = useQuery({
    queryKey: ['product', id],
    queryFn: () => productApi.getById(parseInt(id!)),
  })

  const { data: reviews } = useQuery({
    queryKey: ['reviews', id],
    queryFn: () => productApi.getReviews(parseInt(id!)),
  })

  const handleAddToCart = async () => {
    if (product) {
      await addItem(product.id, quantity)
      alert('Added to cart!')
    }
  }

  if (isLoading) {
    return (
      <div className="container flex items-center justify-center h-96">
        <div className="loading"></div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="container text-center py-12">
        <p className="text-gray-500 text-lg">Product not found</p>
        <Link to="/products" className="btn-primary btn-md mt-4">
          Back to Products
        </Link>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="mb-8">
        <Link to="/products" className="text-primary-600 hover:text-primary-700 font-medium">
          ← Back to Products
        </Link>
      </div>

      <div className="grid gap-8 md:grid-cols-2">
        {/* Images */}
        <div>
          <div className="card overflow-hidden bg-gray-100 aspect-square">
            {product.images?.[0]?.url ? (
              <img src={product.images[0].url} alt={product.name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-400">
                No image
              </div>
            )}
          </div>
          <div className="mt-4 grid grid-cols-4 gap-4">
            {product.images?.map((img: { url: string }, idx: number) => (
              <div key={idx} className="card overflow-hidden bg-gray-100 aspect-square">
                <img src={img.url} alt={`${product.name} ${idx + 1}`} className="w-full h-full object-cover" />
              </div>
            ))}
          </div>
        </div>

        {/* Details */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900">{product.name}</h1>
          <p className="mt-2 text-gray-600">{product.description}</p>

          <div className="mt-6 flex items-center gap-4">
            <p className="text-4xl font-bold text-gray-900">${product.price.toFixed(2)}</p>
            {product.cost && product.cost < product.price && (
              <p className="text-lg text-gray-500 line-through">${(product.price * 1.2).toFixed(2)}</p>
            )}
          </div>

          <div className="mt-4 flex items-center gap-4">
            <span className="text-2xl text-yellow-500">★ {product.rating.toFixed(1)}</span>
            <span className="text-gray-600">({product.rating_count} reviews)</span>
          </div>

          {product.stock_qty > 0 ? (
            <div className="badge badge-success mt-4">In Stock</div>
          ) : (
            <div className="badge badge-primary mt-4">Out of Stock</div>
          )}

          {/* Add to Cart */}
          {product.stock_qty > 0 && (
            <div className="mt-8 space-y-4">
              <div className="flex items-center gap-4">
                <label className="font-medium text-gray-900">Quantity</label>
                <div className="flex items-center border border-gray-300 rounded-lg">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="px-4 py-2 text-gray-600 hover:text-gray-900"
                  >
                    −
                  </button>
                  <input
                    type="number"
                    value={quantity}
                    onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                    min="1"
                    max={product.stock_qty}
                    className="w-16 text-center border-0 focus:outline-none"
                  />
                  <button
                    onClick={() => setQuantity(Math.min(product.stock_qty, quantity + 1))}
                    className="px-4 py-2 text-gray-600 hover:text-gray-900"
                  >
                    +
                  </button>
                </div>
              </div>

              <button
                onClick={handleAddToCart}
                className="btn-primary btn-lg w-full"
              >
                Add to Cart
              </button>
            </div>
          )}

          {/* Product Info */}
          <div className="mt-12 space-y-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">SKU</h3>
              <p className="text-gray-600">{product.sku}</p>
            </div>

            {product.tags && product.tags.length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Tags</h3>
                <div className="flex gap-2 flex-wrap">
                  {product.tags.map((tag: string) => (
                    <span key={tag} className="badge badge-primary">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Reviews Section */}
      <section className="mt-16">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Customer Reviews</h2>
        <div className="grid gap-6">
          {reviews?.map((review: ProductReview) => (
            <div key={review.id} className="card p-6">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-semibold text-gray-900">Rating: {review.rating}/5</p>
                  {review.title && <h3 className="text-lg font-semibold text-gray-900">{review.title}</h3>}
                </div>
                {review.is_verified_purchase && (
                  <span className="badge badge-success">✓ Verified Purchase</span>
                )}
              </div>
              {review.content && <p className="text-gray-600">{review.content}</p>}
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
