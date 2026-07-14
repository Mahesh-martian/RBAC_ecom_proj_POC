import { PaymentMetadata, PaymentResponse } from "@/types";
import { baseApi } from "./baseApi";

interface Transaction {
  id: string;
  orderId: string;
  customerId: string;
  amount: number;
  paymentMethod: string;
  transactionId: string;
  metadata: PaymentMetadata;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface TransactionsResponse {
  success: boolean;
  message: string;
  meta: {
    page: number;
    limit: number;
    total: number;
  };
  data: Transaction[];
}

export const paymentApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    createPaymentIntent: builder.mutation<PaymentResponse, { amount: number }>({
      query: (data) => ({
        url: "/payment/create-payment-intent",
        method: "POST",
        body: data,
      }),
    }),
    savePayment: builder.mutation<any, any>({
      query: (paymentData) => ({
        url: `/payment/payment-confirm`,
        method: "POST",
        body: paymentData,
      }),
    }),
    getPayments: builder.query<
      {
        data: Transaction[];
        meta: { page: number; limit: number; total: number };
      },
      { page: number; limit: number }
    >({
      query: ({ page, limit }) => ({
        url: "/payment",
        method: "GET",
        params: { page, limit },
      }),
      transformResponse: (response: TransactionsResponse) => ({
        data: response.data,
        meta: response.meta,
      }),
    }),
  }),
});

export const {
  useCreatePaymentIntentMutation,
  useSavePaymentMutation,
  useGetPaymentsQuery,
} = paymentApi;
