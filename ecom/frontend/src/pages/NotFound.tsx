import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="container text-center py-32">
      <h1 className="text-6xl font-bold text-gray-900">404</h1>
      <p className="mt-4 text-xl text-gray-600">Page not found</p>
      <Link to="/" className="btn-primary btn-md mt-8">
        Go Home
      </Link>
    </div>
  )
}
