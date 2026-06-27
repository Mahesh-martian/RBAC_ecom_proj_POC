import { UserRole } from "@prisma/client"
import { z } from "zod"

const registerUser = z.object({
  password: z.string({
    required_error: "Password is required"
  }),
  email: z.string({
    required_error: "Email is required"
  }),
  name: z.string({
    required_error: "Name is required"
  }),
  role: z.enum([UserRole.CUSTOMER, UserRole.VENDOR, UserRole.ADMIN])

})
const updateUser = z.object({

isSuspended :  z.boolean()

})
const blacklistVendor = z.object({
  isBlacklisted: z.boolean().optional(),

})


export const userValidation = {
  registerUser, blacklistVendor, updateUser
}