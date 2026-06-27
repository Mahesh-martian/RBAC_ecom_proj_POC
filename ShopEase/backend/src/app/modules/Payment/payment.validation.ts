import { z } from "zod"

const createPaymentIntent = z.object({
  amount: z.number({
    required_error: "Amount is required",
    invalid_type_error: "Amount must be a number",
  }).positive("Amount must be greater than zero"),
  
})

const paymentMetadataSchema = z.object({
  id: z.string({
    required_error: "PaymentIntent ID is required",
  }),
  object: z.string({
    required_error: "Object type is required",
  }),
  amount: z.number({
    required_error: "Amount is required",
  }).positive("Amount must be greater than zero"),
  amount_capturable: z.number().nonnegative(),
  amount_details: z.object({
    tip: z.record(z.any()).optional(),
  }),
  amount_received: z.number().nonnegative(),
  application: z.string().nullable(),
  application_fee_amount: z.number().nullable(),
  automatic_payment_methods: z.any().nullable(),
  canceled_at: z.number().nullable(),
  cancellation_reason: z.string().nullable(),
  capture_method: z.string(),
  client_secret: z.string(),
  confirmation_method: z.string(),
  created: z.number(),
  currency: z.string(),
  customer: z.string().nullable(),
  description: z.string().nullable(),
  invoice: z.string().nullable(),
  last_payment_error: z.any().nullable(),
  latest_charge: z.string().nullable(),
  livemode: z.boolean(),
  metadata: z.record(z.any()).optional(),
  next_action: z.any().nullable(),
  on_behalf_of: z.string().nullable(),
  payment_method: z.string().nullable(),
  payment_method_configuration_details: z.any().nullable(),
  payment_method_options: z.object({
    card: z.object({
      installments: z.any().nullable(),
      mandate_options: z.any().nullable(),
      network: z.string().nullable(),
      request_three_d_secure: z.string(),
    }),
  }),
  payment_method_types: z.array(z.string()),
  processing: z.any().nullable(),
  receipt_email: z.string().nullable(),
  review: z.any().nullable(),
  setup_future_usage: z.any().nullable(),
  shipping: z.any().nullable(),
  source: z.any().nullable(),
  statement_descriptor: z.string().nullable(),
  statement_descriptor_suffix: z.string().nullable(),
  status: z.string(),
  transfer_data: z.any().nullable(),
  transfer_group: z.string().nullable(),
});

const confirmPayment = z.object({
  orderId: z.string({
    required_error: "Order ID is required",
  }),
  customerId: z.string({
    required_error: "Customer ID is required",
  }),
  amount: z.number({
    required_error: "Amount is required",
  }).positive("Amount must be greater than zero"),
  transactionId: z.string().nullable(),
  status: z.enum(["PENDING", "SUCCESS", "FAILED", "REFUNDED"], {
    required_error: "Status is required",
  }),
  metadata: paymentMetadataSchema,
});


export const paymentValidation = {
  createPaymentIntent, confirmPayment
}