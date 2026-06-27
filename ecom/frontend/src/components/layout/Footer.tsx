export default function Footer() {
  return (
    <footer className="border-t border-gray-200 bg-gray-50 mt-16">
      <div className="container py-12">
        <div className="grid md:grid-cols-4 gap-8">
          <div>
            <h3 className="text-lg font-bold text-primary-600 mb-4">FashionStore</h3>
            <p className="text-gray-600 text-sm">Premium online fashion retailer with curated collections.</p>
          </div>

          <div>
            <h4 className="font-semibold text-gray-900 mb-4">Shop</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><a href="#" className="hover:text-primary-600">New Arrivals</a></li>
              <li><a href="#" className="hover:text-primary-600">Best Sellers</a></li>
              <li><a href="#" className="hover:text-primary-600">Sale</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-gray-900 mb-4">Company</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><a href="#" className="hover:text-primary-600">About Us</a></li>
              <li><a href="#" className="hover:text-primary-600">Contact</a></li>
              <li><a href="#" className="hover:text-primary-600">Blog</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-gray-900 mb-4">Legal</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li><a href="#" className="hover:text-primary-600">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-primary-600">Terms of Service</a></li>
              <li><a href="#" className="hover:text-primary-600">Shipping Policy</a></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-200 mt-8 pt-8 text-center text-sm text-gray-600">
          <p>&copy; 2026 FashionStore. All rights reserved.</p>
        </div>
      </div>
    </footer>
  )
}
