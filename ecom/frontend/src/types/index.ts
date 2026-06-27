export interface User {
  id: number
  email: string
  name: string
  phone?: string
  address?: {
    street: string
    city: string
    state: string
    zip: string
    country: string
  }
  subscription_tier: 'free' | 'premium' | 'vip'
  email_verified: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Product {
  id: number
  sku: string
  name: string
  description?: string
  category_id: number
  price: number
  cost?: number
  currency: string
  stock_qty: number
  reorder_level: number
  images?: Array<{ url: string; alt_text?: string; order?: number }>
  tags?: string[]
  metadata?: Record<string, any>
  rating: number
  rating_count: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface CartItem {
  product_id: number
  quantity: number
  price: number
  subtotal: number
  product_name: string
  variant_options?: Record<string, string>
}

export interface Cart {
  id: number
  user_id?: number
  session_id?: string
  items: CartItem[]
  subtotal: number
  tax: number
  shipping: number
  total: number
  created_at: string
  expires_at?: string
}

export interface OrderItem {
  product_id: number
  product_name: string
  quantity: number
  unit_price: number
  subtotal: number
  variant_options?: Record<string, string>
}

export interface Order {
  id: number
  order_number: string
  user_id: number
  status: 'pending' | 'paid' | 'shipped' | 'delivered' | 'canceled' | 'refunded'
  items: OrderItem[]
  subtotal: number
  tax: number
  shipping: number
  discount?: number
  total: number
  payment_intent_id?: string
  shipping_address: {
    street: string
    city: string
    state: string
    zip: string
    country: string
  }
  tracking_number?: string
  created_at: string
  shipped_at?: string
  delivered_at?: string
}

export interface OrderListItem {
  id: number
  order_number: string
  status: 'pending' | 'paid' | 'shipped' | 'delivered' | 'canceled' | 'refunded'
  total: number
  created_at: string
  shipped_at?: string
}

export interface ProductReview {
  id: number
  product_id: number
  user_id: number
  rating: number
  title?: string
  content?: string
  is_verified_purchase: boolean
  created_at: string
  updated_at: string
}

export interface Wishlist {
  id: number
  user_id: number
  product_id: number
  created_at: string
}

export interface PaymentIntent {
  client_secret: string
  order_id: number
  amount: number
  currency: string
  payment_method_types: string[]
  status: string
}

export interface AuthResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
}

export interface ApiError {
  error: string
  message: string
  status_code: number
  timestamp: string
  request_id: string
  details?: Array<{ field: string; message: string }>
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  skip: number
  limit: number
}

export interface ChatRecommendation {
  id: number
  name: string
  sku: string
  price: number
  currency: string
  image_url?: string
}

export interface ChatQueryResponse {
  answer: string
  recommendations: ChatRecommendation[]
  citations: string[]
  conversation_id?: string
}
