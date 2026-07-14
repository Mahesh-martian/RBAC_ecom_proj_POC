import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Cart } from '@/types'
import { cartApi } from '@api/client'

interface CartStore {
  cart: Cart | null
  isLoading: boolean
  error: string | null

  // Actions
  initCart: (cartId?: string) => Promise<void>
  addItem: (productId: number, quantity: number, variantOptions?: Record<string, string>) => Promise<void>
  updateItem: (index: number, quantity: number) => Promise<void>
  removeItem: (index: number) => Promise<void>
  clearCart: () => Promise<void>
  refreshCart: () => Promise<void>
  setError: (error: string | null) => void
}

export const useCartStore = create<CartStore>()(
  persist(
    (set, get) => ({
      cart: null,
      isLoading: false,
      error: null,

      initCart: async (_cartId?: string) => {
        set({ isLoading: true, error: null })
        try {
          const cart = await cartApi.create()
          set({ cart: cart as Cart, isLoading: false })
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to create cart', isLoading: false })
        }
      },

      addItem: async (productId: number, quantity: number, variantOptions?: Record<string, string>) => {
        const state = get()
        if (!state.cart) {
          throw new Error('Cart not initialized')
        }

        set({ isLoading: true, error: null })
        try {
          const updated = await cartApi.addItem(state.cart.id, {
            product_id: productId,
            quantity,
            variant_options: variantOptions,
          })
          set({ cart: updated as Cart, isLoading: false })
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to add item', isLoading: false })
          throw error
        }
      },

      updateItem: async (index: number, quantity: number) => {
        const state = get()
        if (!state.cart) throw new Error('Cart not initialized')

        set({ isLoading: true, error: null })
        try {
          const updated = await cartApi.updateItem(state.cart.id, index, { quantity })
          set({ cart: updated as Cart, isLoading: false })
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to update item', isLoading: false })
          throw error
        }
      },

      removeItem: async (index: number) => {
        const state = get()
        if (!state.cart) throw new Error('Cart not initialized')

        set({ isLoading: true, error: null })
        try {
          const updated = await cartApi.removeItem(state.cart.id, index)
          set({ cart: updated as Cart, isLoading: false })
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to remove item', isLoading: false })
          throw error
        }
      },

      clearCart: async () => {
        const state = get()
        if (!state.cart) throw new Error('Cart not initialized')

        set({ isLoading: true, error: null })
        try {
          await cartApi.clear(state.cart.id)
          set({ cart: null, isLoading: false })
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to clear cart', isLoading: false })
          throw error
        }
      },

      refreshCart: async () => {
        const state = get()
        if (!state.cart) return

        try {
          const cart = await cartApi.getById(state.cart.id)
          set({ cart: cart as Cart })
        } catch (error: any) {
          set({ error: error.response?.data?.message || 'Failed to refresh cart' })
        }
      },

      setError: (error) => set({ error }),
    }),
    {
      name: 'cart-storage',
      partialize: (state) => ({ cart: state.cart }),
    }
  )
)
