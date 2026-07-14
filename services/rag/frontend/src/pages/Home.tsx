import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { productApi } from '@api/client'
import type { PaginatedResponse, Product } from '@/types'

export default function Home() {
  const { data: products } = useQuery({
    queryKey: ['products', { limit: 8 }],
    queryFn: (): Promise<PaginatedResponse<Product>> => productApi.list({ limit: 8 }),
  })

  return (
    <div className="container">
      {/* Hero Section */}
      <section className="mb-16 rounded-lg bg-gradient-to-r from-primary-600 to-primary-900 p-12 text-white">
        <div className="max-w-xl">
          <h1 className="mb-4 text-5xl font-bold">Discover Fashion</h1>
          <p className="mb-8 text-xl text-primary-100">
            Explore our curated collection of premium fashion items
          </p>
          <Link to="/products" className="btn-primary btn-lg bg-white text-primary-600 hover:bg-gray-100">
            Shop Now
          </Link>
        </div>
      </section>

      {/* Featured Products */}
      <section>
        <h2 className="mb-8 text-3xl font-bold">Featured Products</h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {products?.items?.map((product: Product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      </section>

      {/* Categories Section */}
      <section className="mt-16">
        <h2 className="mb-8 text-3xl font-bold">Shop by Category</h2>
        <div className="grid gap-6 md:grid-cols-3">
          <CategoryCard name="Apparel" icon="👕" />
          <CategoryCard name="Accessories" icon="👜" />
          <CategoryCard name="Footwear" icon="👟" />
        </div>
      </section>
    </div>
  )
}

function ProductCard({ product }: { product: Product }) {
  return (
    <Link
      to={`/products/${product.id}`}
      className="group card overflow-hidden hover:shadow-lg"
    >
      <div className="relative h-48 overflow-hidden bg-gray-100">
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
        <div className="mt-2 flex items-center">
          <span className="text-sm text-yellow-500">★★★★★</span>
          <span className="ml-2 text-sm text-gray-500">({product.rating_count})</span>
        </div>
        {product.stock_qty === 0 && <span className="badge badge-primary mt-2">Out of Stock</span>}
      </div>
    </Link>
  )
}

function CategoryCard({ name, icon }: { name: string; icon: string }) {
  return (
    <Link
      to={`/products?category=${name.toLowerCase()}`}
      className="group card overflow-hidden p-8 text-center hover:shadow-lg"
    >
      <div className="text-5xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold text-gray-900 group-hover:text-primary-600">{name}</h3>
    </Link>
  )
}
