import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  AuthResponse,
  ApiError,
  Cart,
  ChatQueryResponse,
  Order,
  OrderListItem,
  PaginatedResponse,
  PaymentIntent,
  Product,
  ProductReview,
  User,
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000')

class ApiClient {
  private client: AxiosInstance
  private token: string | null = null

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: API_TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth token
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`
      }
      return config
    })

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          // Token expired, clear it
          this.clearToken()
          window.location.href = '/auth/login'
        }
        return Promise.reject(error)
      }
    )

    // Load token from localStorage
    this.loadToken()
  }

  private loadToken() {
    this.token = localStorage.getItem('access_token')
  }

  setToken(token: string) {
    this.token = token
    localStorage.setItem('access_token', token)
  }

  clearToken() {
    this.token = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  getToken(): string | null {
    return this.token
  }

  async get<T>(path: string, params?: Record<string, any>) {
    const response = await this.client.get<T>(path, { params })
    return response.data
  }

  async post<T>(path: string, data?: any) {
    const response = await this.client.post<T>(path, data)
    return response.data
  }

  async patch<T>(path: string, data?: any) {
    const response = await this.client.patch<T>(path, data)
    return response.data
  }

  async delete<T>(path: string) {
    const response = await this.client.delete<T>(path)
    return response.data
  }
}

export const apiClient = new ApiClient()

// Auth endpoints
export const authApi = {
  register: (data: { email: string; password: string; name: string; phone?: string }) =>
    apiClient.post<AuthResponse>('/auth/register', data),

  login: (data: { email: string; password: string }) =>
    apiClient.post<AuthResponse>('/auth/login', data),

  logout: () => {
    apiClient.clearToken()
  },

  refreshToken: () =>
    apiClient.post<AuthResponse>('/auth/refresh'),

  getProfile: () =>
    apiClient.get<User>('/auth/me'),
}

// Product endpoints
export const productApi = {
  list: (params?: {
    skip?: number
    limit?: number
    category_id?: number
    min_price?: number
    max_price?: number
    search?: string
    sort_by?: string
    sort_order?: string
    in_stock_only?: boolean
  }) =>
    apiClient.get<PaginatedResponse<Product>>('/products', params),

  getById: (id: number) =>
    apiClient.get<Product>(`/products/${id}`),

  getReviews: (productId: number, params?: { skip?: number; limit?: number }) =>
    apiClient.get<ProductReview[]>(`/products/${productId}/reviews`, params),

  createReview: (productId: number, data: { rating: number; title?: string; content?: string }) =>
    apiClient.post<ProductReview>(`/products/${productId}/reviews`, data),

  create: (data: any) =>
    apiClient.post<Product>('/products', data),

  update: (id: number, data: any) =>
    apiClient.patch<Product>(`/products/${id}`, data),

  delete: (id: number) =>
    apiClient.delete<void>(`/products/${id}`),
}

// Cart endpoints
export const cartApi = {
  create: (data?: { user_id?: number }) =>
    apiClient.post<Cart>('/carts', data),

  getById: (id: number) =>
    apiClient.get<Cart>(`/carts/${id}`),

  addItem: (cartId: number, data: { product_id: number; quantity: number; variant_options?: Record<string, string> }) =>
    apiClient.post<Cart>(`/carts/${cartId}/items`, data),

  updateItem: (cartId: number, index: number, data: { quantity: number }) =>
    apiClient.patch<Cart>(`/carts/${cartId}/items/${index}`, data),

  removeItem: (cartId: number, index: number) =>
    apiClient.delete<Cart>(`/carts/${cartId}/items/${index}`),

  clear: (cartId: number) =>
    apiClient.delete<void>(`/carts/${cartId}`),
}

// Order endpoints
export const orderApi = {
  create: (data: { cart_id: number; shipping_address: any; shipping_method?: string }) =>
    apiClient.post<Order>('/orders', data),

  list: (params?: { skip?: number; limit?: number }) =>
    apiClient.get<PaginatedResponse<OrderListItem>>('/orders', params),

  getById: (id: number) =>
    apiClient.get<Order>(`/orders/${id}`),

  cancel: (id: number) =>
    apiClient.post<Order>(`/orders/${id}/cancel`),

  listAdmin: (params?: { skip?: number; limit?: number; status?: string }) =>
    apiClient.get<PaginatedResponse<OrderListItem>>('/orders/admin/all', params),

  updateStatus: (id: number, data: { status: string; tracking_number?: string }) =>
    apiClient.patch<Order>(`/orders/${id}/status`, data),

  getStats: (params?: { days?: number }) =>
    apiClient.get('/orders/admin/stats', params),
}

// Payment endpoints
export const paymentApi = {
  createIntent: (data: { order_id: number }) =>
    apiClient.post<PaymentIntent>('/payments/intent', data),

  confirm: (data: { order_id: number; payment_intent_id: string; payment_method_id?: string }) =>
    apiClient.post('/payments/confirm', data),

  refund: (orderId: number, data?: { reason?: string }) =>
    apiClient.post(`/payments/${orderId}/refund`, data),

  webhook: (data: any) =>
    apiClient.post('/payments/webhook', data),
}

// Chat endpoints
export const chatApi = {
  query: (data: { query: string; product_id?: number; category?: string; conversation_id?: string }) =>
    apiClient.post<ChatQueryResponse>('/chat/query', data),
}

// Health check
export const healthApi = {
  check: () =>
    apiClient.get('/health'),

  info: () =>
    apiClient.get('/info'),
}
