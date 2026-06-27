import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/types'
import { authApi, apiClient } from '@api/client'
import { useCartStore } from '@stores/cartStore'

function extractApiError(error: any, fallback: string): string {
  const data = error?.response?.data
  const detail = data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d: any) => d?.msg).filter(Boolean).join(', ')
  return data?.message || fallback
}

interface AuthStore {
  user: User | null
  token: string | null
  isLoading: boolean
  error: string | null

  // Actions
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name: string, phone?: string) => Promise<void>
  logout: () => void
  clearError: () => void
  setUser: (user: User | null) => void
  setToken: (token: string) => void
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isLoading: false,
      error: null,

      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authApi.login({ email, password })
          apiClient.setToken(response.access_token)
          set({ token: response.access_token, isLoading: false })

          // Fetch user profile
          const user = await authApi.getProfile()
          set({ user })

          // Bind the cart to the now-authenticated user (replaces any guest cart).
          await useCartStore.getState().initCart()
        } catch (error: any) {
          set({ error: extractApiError(error, 'Login failed'), isLoading: false })
          throw error
        }
      },

      register: async (email: string, password: string, name: string, phone?: string) => {
        set({ isLoading: true, error: null })
        try {
          await authApi.register({ email, password, name, phone })
          // Auto-login after registration
          await (useAuthStore.getState() as any).login(email, password)
        } catch (error: any) {
          set({ error: extractApiError(error, 'Registration failed'), isLoading: false })
          throw error
        }
      },

      logout: () => {
        authApi.logout()
        set({ user: null, token: null })
      },

      clearError: () => set({ error: null }),
      setUser: (user) => set({ user }),
      setToken: (token) => {
        apiClient.setToken(token)
        set({ token })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token, user: state.user }),
    }
  )
)
