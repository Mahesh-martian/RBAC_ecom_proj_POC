interface GetReviewsResponse {
  success: boolean;
  message: string;
  meta: {
    total: number;
    page: number;
    limit: number;
  };
  data: Review[];
}

export interface Review {
  id: string;
  comment: string;
  createdAt: string;
  updatedAt: string;
  rating: number;
  customer: {
    id: string;
    name: string;
    email: string;
    createdAt: string;
    updatedAt: string;
    isDeleted: boolean;
    isSuspended: boolean;
    profilePhoto: string | null;
  };
  product: {
    id: string;
    name: string;
    description: string;
    categoryId: string;
    price: number;
    discount: number;
    inventory: number;
    shopId: string;
    vendorId: string;
    createdAt: string;
    updatedAt: string;
    deletedAt: string | null;
    image: string[];
  };
}

// Interface for the giveReview API response
export interface GiveReviewResponse {
  success: boolean;
  message: string;
  data: Review;
}

// Interface for the request body of giveReview
export interface GiveReviewRequest {
  productId: string;
  rating: number;
  comment?: string;
}

import { baseApi } from "./baseApi";

export const reviewApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    giveReview: builder.mutation<GiveReviewResponse, GiveReviewRequest>({
      query: (review) => ({
        url: "/reviews",
        method: "POST",
        body: review,
      }),
      transformResponse: (response: GiveReviewResponse) => ({
        success: response.success,
        message: response.message,
        data: response.data,
      }),
      invalidatesTags: ["Product"],
    }),
    getReviews: builder.query<
      GetReviewsResponse,
      { page: number; limit: number }
    >({
      query: ({ page, limit }) => ({
        url: `/reviews?page=${page}&limit=${limit}`,
        method: "GET",
      }),
      transformResponse: (response: GetReviewsResponse) => {
        return response;
      },
    }),
  }),
});

export const { useGiveReviewMutation, useGetReviewsQuery } = reviewApi;
