import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { SingleProductData } from "@/types";

interface CartItem extends SingleProductData {
  quantity: number;
}

interface CartState {
  items: CartItem[];
  couponCode: string | null;
  couponDiscount: number;
  vendorId: string | null;
}

// Utility to load cart from local storage
const loadCartFromLocalStorage = (): CartState => {
  if (typeof window !== "undefined") {
    const storedCart = localStorage.getItem("cart");
    if (storedCart) {
      return JSON.parse(storedCart);
    }
  }
  return {
    items: [],
    couponCode: null,
    couponDiscount: 0,
    vendorId: null,
  };
};

// Utility to save cart to local storage
const saveCartToLocalStorage = (cart: CartState) => {
  if (typeof window !== "undefined") {
    localStorage.setItem("cart", JSON.stringify(cart));
  }
};

const initialState: CartState = loadCartFromLocalStorage();

const cartSlice = createSlice({
  name: "cart",
  initialState,
  reducers: {
    addToCart: (
      state,
      action: PayloadAction<{ product: SingleProductData; quantity: number }>,
    ) => {
      const { product, quantity } = action.payload;

      if (state.vendorId && state.vendorId !== product.shopId) {
        throw new Error("VendorMismatch");
      }

      const existingItem = state.items.find(
        (item) => item.productId === product.productId,
      );

      if (existingItem) {
        existingItem.quantity += quantity;
      } else {
        state.items.push({ ...product, quantity });
      }

      // Set the vendorId if not already set
      if (!state.vendorId) {
        state.vendorId = product.shopId;
      }

      // Save to local storage
      saveCartToLocalStorage(state);
    },
    replaceCart: (
      state,
      action: PayloadAction<{ product: SingleProductData; quantity: number }>,
    ) => {
      const { product, quantity } = action.payload;

      // Clear the cart and set the new product and vendor
      state.items = [{ ...product, quantity }];
      state.vendorId = product.shopId;

      // Save to local storage
      saveCartToLocalStorage(state);
    },
    clearCart: (state) => {
      state.items = [];
      state.vendorId = null;
      state.couponCode = null;
      state.couponDiscount = 0;

      // Save to local storage
      saveCartToLocalStorage(state);
    },
    removeFromCart: (state, action: PayloadAction<string>) => {
      state.items = state.items.filter(
        (item) => item.productId !== action.payload,
      );
      if (state.items.length === 0) {
        state.vendorId = null;
      }

      // Save to local storage
      saveCartToLocalStorage(state);
    },
    updateQuantity: (
      state,
      action: PayloadAction<{ productId: string; quantity: number }>,
    ) => {
      const item = state.items.find(
        (item) => item.productId === action.payload.productId,
      );
      if (item) {
        item.quantity = Math.max(1, action.payload.quantity);
      }

      // Save to local storage
      saveCartToLocalStorage(state);
    },
    applyCoupon: (
      state,
      action: PayloadAction<{ code: string; discount: number }>,
    ) => {
      state.couponCode = action.payload.code;
      state.couponDiscount = action.payload.discount;

      // Save to local storage
      saveCartToLocalStorage(state);
    },
    clearCoupon: (state) => {
      state.couponCode = null;
      state.couponDiscount = 0;

      // Save to local storage
      saveCartToLocalStorage(state);
    },
  },
});

export const {
  addToCart,
  replaceCart,
  clearCart,
  removeFromCart,
  updateQuantity,
  applyCoupon,
  clearCoupon,
} = cartSlice.actions;

export default cartSlice.reducer;
