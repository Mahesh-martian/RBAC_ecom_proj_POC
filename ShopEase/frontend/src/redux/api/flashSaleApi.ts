import { baseApi } from "./baseApi";

export interface CreateFlashSaleResponse {
  success: boolean;
  message: string;
  data: FlashSale;
}

export interface CreateFlashSale {
  productId: string;
  discount: number;
  startTime: string;
  endTime: string;
}

export interface FlashSale {
  id: string;
  productId: string;
  discount: number;
  startTime: string;
  endTime: string;
  createdAt: string;
  updatedAt: string;
}

export interface UpdateFlashSaleResponse {
  success: boolean;
  message: string;
  data: FlashSale;
}

export interface GetAllFlashSalesResponse {
  success: boolean;
  message: string;
  meta: MetaData;
  data: FlashSaleWithProduct[];
}

export interface MetaData {
  page: number;
  limit: number;
  total: number;
}

export interface FlashSaleWithProduct extends FlashSale {
  product: Product;
}

export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  discount: number;
  categoryId: string;
  inventory: number;
  image: string[];
  vendorId: string;
  shopId: string;
  createdAt: string;
  updatedAt: string;
  deletedAt: string | null;
}

export interface GetSingleFlashSaleResponse {
  success: boolean;
  message: string;
  data: FlashSaleWithProduct;
}

export const flashSaleApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Create a Flash Sale
    createFlashSale: builder.mutation<CreateFlashSaleResponse, CreateFlashSale>(
      {
        query: (flashSale) => ({
          url: "/flash-sale",
          method: "POST",
          body: flashSale,
        }),
      },
    ),

    // Update a Flash Sale
    updateFlashSale: builder.mutation<
      UpdateFlashSaleResponse,
      { id: string; updates: Partial<FlashSale> }
    >({
      query: ({ id, updates }) => ({
        url: `/flash-sale/${id}`,
        method: "PATCH",
        body: updates,
      }),
      invalidatesTags: ["Flash Sale"],
    }),

    // Get all Flash Sales
    getAllFlashSales: builder.query<
      GetAllFlashSalesResponse,
      { limit?: number; page?: number }
    >({
      query: ({ limit = 10, page = 1 }) => ({
        url: `/flash-sale`,
        method: "GET",
        params: { limit, page },
      }),
      providesTags: ["Flash Sale"],
    }),

    // Get a specific Flash Sale
    getAFlashSale: builder.query<GetSingleFlashSaleResponse, string>({
      query: (id) => ({
        url: `/flash-sale/${id}`,
        method: "GET",
      }),
    }),
  }),
});

export const {
  useCreateFlashSaleMutation,
  useUpdateFlashSaleMutation,
  useGetAllFlashSalesQuery,
  useGetAFlashSaleQuery,
} = flashSaleApi;
