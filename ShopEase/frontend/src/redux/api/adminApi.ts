import { baseApi } from "./baseApi";

export interface AdminApiResponse<T = any> {
  success: boolean;
  message: string;
  data: T;
  meta?: {
    page: number;
    limit: number;
    total: number;
  };
}

export interface AdminUser {
  createdAt: string;
  deletedAt: string | null;
  email: string;
  id: string;
  name: string;
  password: string;
  role: "CUSTOMER" | "VENDOR" | "ADMIN";
  updatedAt: string;
}

interface GetAdminUsersParams {
  page?: number;
  limit?: number;
}

interface UpdateUserData {
  isSuspended?: boolean;
}

export const adminApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getAdminUsers: builder.query<
      { data: AdminUser[]; meta?: AdminApiResponse["meta"] },
      GetAdminUsersParams
    >({
      query: ({ page = 1, limit = 10 }) => ({
        url: "/admin/users",
        params: { page, limit },
      }),
      transformResponse: (response: AdminApiResponse<AdminUser[]>) => ({
        data: response.data,
        meta: response.meta,
      }),
      providesTags: ["Admin"],
    }),
    getUserById: builder.query<AdminUser, string>({
      query: (id) => `/admin/users/${id}`,
      transformResponse: (response: AdminApiResponse<AdminUser>) =>
        response.data,
    }),
    updateUser: builder.mutation<
      AdminUser,
      { id: string; data: UpdateUserData }
    >({
      query: ({ id, data }) => ({
        url: `/admin/users/${id}`,
        method: "PATCH",
        body: data,
      }),
      invalidatesTags: ["Admin"],
    }),
    deleteUser: builder.mutation<null, string>({
      query: (id) => ({
        url: `/admin/users/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Admin"],
      transformResponse: (response: AdminApiResponse<null>) => response.data,
    }),
    blacklistVendor: builder.mutation<
      null,
      { shopId: string; isBlackListed: boolean }
    >({
      query: ({ shopId, isBlackListed }) => ({
        url: `/admin/shop/${shopId}`,
        method: "PATCH",
        body: { isBlackListed },
      }),
      invalidatesTags: ["Shop"],
      transformResponse: (response: AdminApiResponse<null>) => response.data,
    }),
  }),
});

export const {
  useGetAdminUsersQuery,
  useGetUserByIdQuery,
  useUpdateUserMutation,
  useDeleteUserMutation,
  useBlacklistVendorMutation,
} = adminApi;
