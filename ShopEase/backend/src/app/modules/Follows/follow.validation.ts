import { z } from "zod"


const createProduct = z.object({
  name: z.string({
    required_error: "Name is required",
  }),
  description: z.string({
    required_error: "Description is required",
  }),
  price: z
    .number({
      required_error: "Price is required",
      invalid_type_error: "Price must be a number",
    })
    .min(0, "Price must be greater than or equal to 0"),
  discount: z
    .number({
           invalid_type_error: "Discount must be a number",
    })
    .min(0, "Discount must be greater than or equal to 0").optional(),
  categoryId: z.string({
    required_error: "Category ID is required",
  }),
  inventory: z
    .number({
      required_error: "Inventory count is required",
      invalid_type_error: "Inventory must be a number",
    })
    .min(0, "Inventory must be greater than or equal to 0"),
 
});

const duplicateProduct = z.object({
  name: z.string({
    required_error: "Name is required",
  }),
  description: z.string({
    required_error: "Description is required",
  }),
  price: z
    .number({
      required_error: "Price is required",
      invalid_type_error: "Price must be a number",
    })
    .min(0, "Price must be greater than or equal to 0"),
  discount: z
    .number({
           invalid_type_error: "Discount must be a number",
    })
    .min(0, "Discount must be greater than or equal to 0").optional(),
  categoryId: z.string({
    required_error: "Category ID is required",
  }),
  image: z
  .array(z.string().url({ message: "Each image must be a valid URL" }))
  .min(1, "At least one image is required"),
  inventory: z
    .number({
      required_error: "Inventory count is required",
      invalid_type_error: "Inventory must be a number",
    })
    .min(0, "Inventory must be greater than or equal to 0"),

  vendorId: z.string({
    required_error: "Vendor ID is required",
  }),
  shopId: z.string({
    required_error: "Shop ID is required",
  }) 
});



const updateProduct = z.object({
  name: z.string().optional(),
  description: z.string().optional(),
  price: z
    .number({
      invalid_type_error: "Price must be a number",
    })
    .min(0, "Price must be greater than or equal to 0")
    .optional(),
  discount: z
    .number({
      invalid_type_error: "Discount must be a number",
    })
    .min(0, "Discount must be greater than or equal to 0").optional(),
    inventory: z
    .number({
      invalid_type_error: "Inventory must be a number",
    })
    .min(0, "Inventory must be greater than or equal to 0")
    .optional(),
  image: z
    .array(z.string().url({ message: "Each image must be a valid URL" }))
    .optional(),
}).partial(); 


export const productValidation = {
  createProduct,duplicateProduct,updateProduct
}