import {
  AllShopsApiResponse,
  CreateShopRequest,
  ShopApiResponse,
  ShopData,
  ShopRouteShopData,
} from "@/types";
import { baseApi } from "./baseApi";

export const shopApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getShop: builder.query<ShopData, void>({
      query: () => "/shop",
      transformResponse: (response: ShopApiResponse) => {
        const { id: shopId, name, logo, description } = response.data;
        const shopData = { shopId, name, description, logo };
        return shopData;
      },
      providesTags: ["Shop"],
    }),

    getAllShop: builder.query<
      { data: ShopRouteShopData[]; meta: AllShopsApiResponse["meta"] },
      { page: number; limit: number }
    >({
      query: ({ page, limit }) => `/shop/all?page=${page}&limit=${limit}`,
      transformResponse: (response: AllShopsApiResponse) => {
        const transformedData = response.data.map((shop) => {
          const {
            id: shopId,
            name,
            logo,
            description,
            products,
            isBlackListed,
            vendor,
          } = shop;
          const productsQuantity = products?.length ?? 0;
          const followers = vendor?.follows?.length ?? 0;

          return {
            shopId,
            name,
            description,
            logo,
            productsQuantity,
            followers,
            isBlackListed,
            vendorId: vendor?.id,
          };
        });

        return { data: transformedData, meta: response.meta };
      },
      providesTags: ["Shop"],
    }),

    createShop: builder.mutation<ShopApiResponse, CreateShopRequest>({
      query: ({ name, description, file }) => {
        const dataObject = JSON.stringify({ name, description });
        const formData = new FormData();
        formData.append("data", dataObject);
        formData.append("file", file);
        return {
          url: "/shop",
          method: "POST",
          body: formData,
        };
      },
      invalidatesTags: ["Shop"],
    }),
    getShopDetails: builder.query<any, { id: string }>({
      query: ({ id }) => ({
        url: `/shop/single/${id}`,
        method: "GET",
      }),
      providesTags: ["Shop"],
    }),
  }),
});

export const {
  useGetShopQuery,
  useCreateShopMutation,
  useGetAllShopQuery,
  useGetShopDetailsQuery,
} = shopApi;
