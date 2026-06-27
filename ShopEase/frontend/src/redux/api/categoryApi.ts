import { baseApi } from "./baseApi";

export interface CategoryApiResponse<T = any> {
  success: boolean;
  message: string;
  data: T;
  meta?: {
    page: number;
    limit: number;
    total: number;
  };
}

export interface Category {
  id: string;
  name: string;
  description: string;
  createdAt: string; // ISO date string
  updatedAt: string; // ISO date string
  deletedAt: string | null; // null if not deleted
}

export interface GetCategoriesParams {
  page: number;
  limit: number;
}

export const categoryApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getCategories: builder.query<
      { data: Category[]; meta?: CategoryApiResponse["meta"] },
      GetCategoriesParams
    >({
      query: ({ page, limit }) => ({
        url: "/admin/categories",
        params: { page, limit },
      }),
      transformResponse: (response: CategoryApiResponse<Category[]>) => {
        const { data, meta } = response;
        return { data, meta };
      },
      providesTags: ["Categories"],
    }),
    getCategoryById: builder.query<Category, string>({
      query: (id) => `/admin/categories/${id}`,
      transformResponse: (response: CategoryApiResponse<Category>) =>
        response.data,
    }),
    createCategory: builder.mutation<Category, Partial<Category>>({
      query: (categoryData) => ({
        url: "/admin/categories",
        method: "POST",
        body: categoryData,
      }),
      transformResponse: (response: CategoryApiResponse<Category>) =>
        response.data,
    }),
    updateCategory: builder.mutation<
      Category,
      { id: string; data: Partial<Category> }
    >({
      query: ({ id, data }) => ({
        url: `/admin/categories/${id}`,
        method: "PATCH",
        body: data,
      }),
      invalidatesTags: ["Categories"],
      transformResponse: (response: CategoryApiResponse<Category>) =>
        response.data,
    }),
    deleteCategory: builder.mutation<null, string>({
      query: (id) => ({
        url: `/admin/categories/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Categories"],
      transformResponse: (response: CategoryApiResponse<null>) => response.data,
    }),
  }),
});

export const {
  useGetCategoriesQuery,
  useGetCategoryByIdQuery,
  useCreateCategoryMutation,
  useUpdateCategoryMutation,
  useDeleteCategoryMutation,
} = categoryApi;
