import { useAuthStore } from '@stores/authStore'
import { Link } from 'react-router-dom'

export default function Account() {
  const user = useAuthStore((state) => state.user)

  if (!user) {
    return (
      <div className="container text-center py-12">
        <p className="text-gray-500">Please log in to view your account</p>
      </div>
    )
  }

  return (
    <div className="container max-w-2xl">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">My Account</h1>

      <div className="card p-6 space-y-6">
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-4">Personal Information</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm text-gray-600">Full Name</label>
              <p className="text-lg font-semibold text-gray-900">{user.name}</p>
            </div>
            <div>
              <label className="text-sm text-gray-600">Email</label>
              <p className="text-lg font-semibold text-gray-900">{user.email}</p>
            </div>
            <div>
              <label className="text-sm text-gray-600">Phone</label>
              <p className="text-lg font-semibold text-gray-900">{user.phone || 'Not provided'}</p>
            </div>
            <div>
              <label className="text-sm text-gray-600">Member Since</label>
              <p className="text-lg font-semibold text-gray-900">
                {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-200 pt-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Shipping Address</h2>
          {user.address ? (
            <div className="text-gray-900">
              <p>{user.address.street}</p>
              <p>{user.address.city}, {user.address.state} {user.address.zip}</p>
              <p>{user.address.country}</p>
            </div>
          ) : (
            <p className="text-gray-600">No address on file</p>
          )}
        </div>

        <div className="border-t border-gray-200 pt-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Subscription</h2>
          <div className="flex items-center justify-between">
            <span className="text-gray-900">
              Plan: <span className="font-semibold capitalize">{user.subscription_tier}</span>
            </span>
            <button className="btn-secondary btn-md">Upgrade</button>
          </div>
        </div>

        <div className="border-t border-gray-200 pt-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Actions</h2>
          <div className="space-y-2">
            <Link to="/orders" className="btn-secondary btn-md block text-center">
              View Orders
            </Link>
            <button className="btn-secondary btn-md w-full">Edit Profile</button>
            <button className="btn-secondary btn-md w-full">Change Password</button>
          </div>
        </div>
      </div>
    </div>
  )
}
