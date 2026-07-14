import { createSlice, PayloadAction } from "@reduxjs/toolkit";

type RecentProductsState = {
  productIds: string[];
};

// Utility function to load from local storage
const loadFromLocalStorage = (): string[] => {
  if (typeof window !== "undefined") {
    const data = localStorage.getItem("recentProducts");
    return data ? JSON.parse(data) : [];
  }
  return [];
};

// Utility function to save to local storage
const saveToLocalStorage = (productIds: string[]) => {
  if (typeof window !== "undefined") {
    localStorage.setItem("recentProducts", JSON.stringify(productIds));
  }
};

const initialState: RecentProductsState = {
  productIds: loadFromLocalStorage(), // Load initial state from local storage
};

const recentProductsSlice = createSlice({
  name: "recentProducts",
  initialState,
  reducers: {
    addProductId: (state, action: PayloadAction<string>) => {
      const productId = action.payload;

      // Remove the productId if it already exists
      state.productIds = state.productIds.filter((id) => id !== productId);

      // Add the productId to the beginning of the array
      state.productIds.unshift(productId);

      // Keep only the latest 10 items
      if (state.productIds.length > 10) {
        state.productIds.pop();
      }

      // Save the updated state to local storage
      saveToLocalStorage(state.productIds);
    },
    loadRecentProducts: (state) => {
      // Load products from local storage into state
      state.productIds = loadFromLocalStorage();
    },
  },
});

export const { addProductId, loadRecentProducts } = recentProductsSlice.actions;

export default recentProductsSlice.reducer;
