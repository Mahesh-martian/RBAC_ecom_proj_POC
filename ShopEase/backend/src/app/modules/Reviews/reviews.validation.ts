import { z } from "zod"

const createReview = z.object({
  productId: z.string({
    required_error: "Product Id is required",
  }),
  comment: z.string({
    required_error: "Comment is required",
  }),
  rating: z
    .number({
      required_error: "Rating is required",
    })
    .min(0, "Rating must be at least 0")
    .max(5, "Rating must be at most 5"), 
});


export const reviewValidation = {
  createReview
}