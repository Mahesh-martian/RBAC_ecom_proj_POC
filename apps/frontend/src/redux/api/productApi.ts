import {
  EditProductRequest,
  ProductApiResponse,
  ProductData,
  SingleProductApiResponse,
  SingleProductData,
  VendorProductApiResponse,
  VendorProductData,
} from "@/types";
import { baseApi } from "./baseApi";

export const productApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    createProduct: builder.mutation<
      ProductApiResponse,
      {
        name: string;
        description: string;
        price: number;
        discount?: number;
        categoryId: string;
        inventory: number;
        images: File[];
      }
    >({
      query: ({
        name,
        description,
        price,
        discount,
        categoryId,
        inventory,
        images,
      }) => {
        // Construct FormData for product creation
        const dataObject = JSON.stringify({
          name,
          description,
          price,
          discount,
          categoryId,
          inventory,
        });
        const formData = new FormData();
        formData.append("data", dataObject);
        images.forEach((file) => {
          formData.append("images", file);
        });

        return {
          url: `/products`,
          method: "POST",
          body: formData,
        };
      },
      invalidatesTags: ["Product"],
    }),

    getProducts: builder.query<
      ProductData[],
      Partial<{
        categoryId?: string;
        searchTerm?: string;
        page?: number;
        limit?: number;
        name?: string;
        price?: number;
        discount?: number;
      }>
    >({
      query: (params = {}) => {
        // Construct the query string dynamically
        const queryString = Object.entries(params)
          .map(
            ([key, value]) =>
              `${encodeURIComponent(key)}=${encodeURIComponent(value)}`,
          )
          .join("&");

        return `/products${queryString ? `?${queryString}` : ""}`;
      },
      transformResponse: (response: ProductApiResponse) => {
        return response.data.map((data) => {
          const {
            id: productId,
            name,
            description,
            categoryId,
            discount,
            image,
            inventory,
            price,
            shopId,
            vendorId,
          } = data;
          return {
            productId,
            name,
            description,
            categoryId,
            discount,
            image,
            inventory,
            price,
            shopId,
            vendorId,
          };
        });
      },
    }),

    getSingleProduct: builder.query<SingleProductData, { id: string }>({
      query: ({ id }) => `/products/${id}`,
      transformResponse: (response: SingleProductApiResponse) => {
        const {
          id: productId,
          name,
          description,
          categoryId,
          discount,
          image,
          inventory,
          price,
          shopId,
          reviews,
          category,
          shop,
          vendorId,
        } = response.data;

        const productData: SingleProductData = {
          productId,
          name,
          description,
          categoryId,
          discount,
          image,
          inventory,
          price,
          shopId,
          vendorId,
          reviews: reviews?.map((review) => ({
            id: review.id,
            rating: review.rating,
            comment: review.comment,
            createdAt: review.createdAt,
            customer: {
              id: review.customer.id,
              name: review.customer.name,
              profilePhoto: review.customer.profilePhoto,
            },
          })),
          category: {
            name: category.name,
            description: category.description,
          },
          shop: {
            name: shop.name,
            description: shop.description,
            logo: shop.logo,
          },
        };

        return productData;
      },
      providesTags: ["Product"],
    }),
    getVendorProducts: builder.query<
      {
        data: VendorProductData[];
        meta: { page: number; limit: number; total: number };
      },
      { page: number; limit: number }
    >({
      query: ({ page, limit }) =>
        `/products/vendor-product?page=${page}&limit=${limit}`,
      transformResponse: (response: VendorProductApiResponse) => {
        const { data, meta } = response;
        const transformedData = data.map((product) => {
          const {
            id: productId,
            name,
            description,
            categoryId,
            discount,
            image,
            inventory,
            price,
            shopId,
            categoryName,
          } = product;

          return {
            productId,
            name,
            description,
            categoryId,
            discount,
            image,
            inventory,
            price,
            shopId,
            categoryName,
          };
        });

        return { data: transformedData, meta };
      },
      providesTags: ["Product"],
    }),
    editProduct: builder.mutation<ProductApiResponse, EditProductRequest>({
      query: ({
        productId,
        name,
        description,
        discount,
        inventory,
        price,
        additionalImages,
      }) => {
        const dataObject = JSON.stringify({
          name,
          description,
          discount,
          inventory,
          price,
        });
        const formData = new FormData();
        formData.append("data", dataObject);
        additionalImages.forEach((file) => {
          formData.append("images", file);
        });

        return {
          url: `/products/${productId}`,
          method: "PATCH",
          body: formData,
        };
      },
      invalidatesTags: ["Product"],
    }),
    duplicateProduct: builder.mutation<
      ProductApiResponse,
      { productId: string }
    >({
      query: ({ productId }) => {
        return {
          url: `/products/duplicate/${productId}`,
          method: "POST",
        };
      },

      invalidatesTags: ["Product"],
    }),
  }),
});

export const {
  useCreateProductMutation,
  useGetProductsQuery,
  useGetVendorProductsQuery,
  useEditProductMutation,
  useDuplicateProductMutation,
  useGetSingleProductQuery,
} = productApi;
