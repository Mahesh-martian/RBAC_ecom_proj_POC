import { z } from "zod";

export const signUpSchema = z.object({
  name: z.string().min(2, { message: "Name must be at least 2 characters." }),
  email: z.string().email({ message: "Invalid email address." }),
  password: z
    .string()
    .min(6, { message: "Password must be at least 6 characters." }),
  role: z.enum(["CUSTOMER", "VENDOR"], {
    required_error: "Role is required.",
  }),
});

// Optionally, export the type for TypeScript
export type SignUpData = z.infer<typeof signUpSchema>;
