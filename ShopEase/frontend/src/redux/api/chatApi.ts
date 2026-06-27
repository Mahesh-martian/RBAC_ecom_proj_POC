import { baseApi } from "./baseApi";

export const chatApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    sendMessage: builder.mutation({
      query: (message) => ({
        url: "/chat-bot",
        method: "POST",
        body: { message },
      }),
      invalidatesTags: [],
    }),
    getChatHistory: builder.query({
      query: () => ({
        url: "/chat-bot",
        method: "GET",
      }),
      providesTags: [],
    }),
  }),
});

export const { useSendMessageMutation, useGetChatHistoryQuery } = chatApi;
