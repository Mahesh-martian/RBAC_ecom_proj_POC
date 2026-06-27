import { z } from "zod";

const baseFlashSaleSchema = z.object({
  discount: z
    .number({
      invalid_type_error: "Discount must be a number",
    })
    .min(0, "Discount must be greater than or equal to 0")
    .max(100, "Discount cannot exceed 100")
    .optional(),

  productId: z.string({
    required_error: "Product ID is required",
    invalid_type_error: "Product ID must be a string",
  }),

  startTime: z.preprocess(
    (val) => (typeof val === "string" ? new Date(val) : val),
    z.date({
      required_error: "Start date is required",
      invalid_type_error: "Start date must be a valid date",
    })
  ),

  endTime: z.preprocess(
    (val) => (typeof val === "string" ? new Date(val) : val),
    z.date({
      required_error: "End date is required",
      invalid_type_error: "End date must be a valid date",
    })
  ),
});

// Add superRefine for additional validations
const createFlashSale = baseFlashSaleSchema.superRefine((data, ctx) => {
  if (data.startTime < new Date()) {
    ctx.addIssue({
      code: "custom",
      path: ["startTime"],
      message: "Start Time cannot be in the past",
    });
  }

  if (data.endTime <= data.startTime) {
    ctx.addIssue({
      code: "custom",
      path: ["endTime"],
      message: "End Time must be after start Time",
    });
  }
});

// For the update schema
const baseUpdateFlashSaleSchema = z
  .object({
    discount: z
      .number({
        invalid_type_error: "Discount must be a number",
      })
      .min(0, "Discount must be greater than or equal to 0")
      .optional(),

   

    startTime: z
      .preprocess(
        (val) => (typeof val === "string" ? new Date(val) : val),
        z.date().optional()
      ),

    endTime: z
      .preprocess(
        (val) => (typeof val === "string" ? new Date(val) : val),
        z.date().optional()
      ),
  })
  .partial();

// Schema with .superRefine for stricter validation
// const updateFlashSale = baseUpdateFlashSaleSchema.superRefine((data, ctx) => {
//   if (data.startDate && data.startDate < new Date()) {
//     ctx.addIssue({
//       code: "custom",
//       path: ["startDate"],
//       message: "Start date cannot be in the past",
//     });
//   }

//   if (data.startDate && data.endDate && data.endDate <= data.startDate) {
//     ctx.addIssue({
//       code: "custom",
//       path: ["endDate"],
//       message: "End date must be after start date",
//     });
//   }
// });

export const flashSaleValidation = {
  createFlashSale: baseFlashSaleSchema,
  updateFlashSale: baseUpdateFlashSaleSchema
};
