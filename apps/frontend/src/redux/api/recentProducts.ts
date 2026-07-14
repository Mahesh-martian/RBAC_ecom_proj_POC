import { ProductData } from "@/types";
import { baseApi } from "./baseApi";

interface RecentProduct {
  id: string;
  userId: string;
  productId: string;
  visitedAt: string;
  product: ProductData;
}

interface RecentProductApiResponse {
  success: boolean;
  message: string;
  data: RecentProduct[];
  meta?: {
    page: number;
    limit: number;
    total: number;
  };
}

export const recentProductsApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    sendRecentProducts: builder.mutation<void, string[]>({
      query: (recentProducts) => ({
        url: "/recent-products",
        method: "POST",
        body: { products: recentProducts },
      }),
    }),
    // Endpoint for getting recent products
    getRecentProducts: builder.query<RecentProductApiResponse, void>({
      query: () => ({
        url: "/recent-products",
        method: "GET",
      }),
    }),
  }),
});

export const { useSendRecentProductsMutation, useGetRecentProductsQuery } =
  recentProductsApi;
