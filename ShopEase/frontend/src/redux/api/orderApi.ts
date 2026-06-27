import {
  CreateOrderApiResponse,
  OrderApiResponse,
  StructuredCartData,
} from "@/types";
import { baseApi } from "./baseApi";

export const orderApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    createOrder: builder.mutation<CreateOrderApiResponse, StructuredCartData>({
      query: (cartData) => {
        return {
          url: `orders`,
          method: "POST",
          body: cartData,
        };
      },
    }),
    getAllOrders: builder.query<
      OrderApiResponse,
      { page?: number; limit?: number }
    >({
      query: ({ page, limit }) => {
        return {
          url: `orders`,
          method: "GET",
          params: {
            limit,
            page,
          },
        };
      },
    }),
  }),
});

export const { useCreateOrderMutation, useGetAllOrdersQuery } = orderApi;
