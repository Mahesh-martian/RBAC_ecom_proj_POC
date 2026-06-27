import { z } from "zod";

export const signInSchema = z.object({
  email: z.string().email({ message: "Invalid email address." }),
  password: z
    .string()
    .min(6, { message: "Password must be at least 6 characters." }),
});

// Optionally, export the type for TypeScript
export type SignInData = z.infer<typeof signInSchema>;
