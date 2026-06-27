import { z } from "zod"

const productSchema = z.object({
  productId: z.string({
    required_error: "Product ID is required",
  }),
  quantity: z
    .number({
      required_error: "Quantity is required",
    })
    .int("Quantity must be an integer")
    .positive("Quantity must be greater than zero"),
  price: z
    .number({
      required_error: "Price is required",
    })
    .positive("Price must be greater than zero"),
  discount: z
    .number({
      required_error: "Discount is required",
    })
    .min(0, "Discount cannot be negative"),
});

const createOrder = z.object({
  vendorId: z.string({
    required_error: "Vendor ID is required",
  }),
  totalAmount: z
    .number({
      required_error: "Total amount is required",
    })
    .positive("Total amount must be greater than zero"),
  products: z
    .array(productSchema, {
      required_error: "Products are required",
    })
    .nonempty("At least one product is required"),
});



export const OrderValidation = {
  createOrder
}