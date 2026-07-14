import { FollowerCountResponse, FollowResponse } from "@/types";
import { baseApi } from "./baseApi";

export const followApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    followShop: builder.mutation<FollowResponse, { vendorId: string }>({
      query: (body) => ({
        url: "/follows",
        method: "POST",
        body,
      }),
      invalidatesTags: ["Shop"],
    }),
    unfollowShop: builder.mutation<FollowResponse, { id: string }>({
      query: ({ id }) => ({
        url: `/follows/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["Shop"],
    }),
    getShopFollowerCount: builder.query<number, { vendorId: string }>({
      query: ({ vendorId }) => ({
        url: `/follows/${vendorId}`,
        method: "GET",
      }),
      transformResponse: (response: FollowerCountResponse) => {
        return response.data.data;
      },
      providesTags: ["Shop"],
    }),
  }),
});

export const {
  useFollowShopMutation,
  useUnfollowShopMutation,
  useGetShopFollowerCountQuery,
} = followApi;
