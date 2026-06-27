import { Outlet } from 'react-router-dom'

export default function AuthLayout() {
  return (
    <div className="flex min-h-screen">
      {/* Left side - Brand */}
      <div className="hidden w-1/2 bg-gradient-to-br from-primary-600 to-primary-900 lg:flex flex-col items-center justify-center p-12">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-white mb-4">FashionStore</h1>
          <p className="text-xl text-primary-100">Premium Online Fashion</p>
        </div>
      </div>

      {/* Right side - Form */}
      <div className="flex w-full items-center justify-center px-4 py-12 lg:w-1/2">
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
