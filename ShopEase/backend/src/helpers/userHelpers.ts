import ApiError from "../app/errors/ApiError"
import prisma from "../shared/prisma"


export const findUserById = async (id: string )=> {
  const user = await prisma.user.findUnique({
    where:{id},
    include:{vendor: true, customer: true}
  })

  if(!user) throw new ApiError(404, "User Not Found")
  return user;
}

export const findUserByEmail  = async (email: string )=> {
  const user = await prisma.user.findUnique({
    where:{email},
    include:{vendor: true, customer: true}
  })


  if(!user) throw new ApiError(404, "User Not Found")
  return user;
}

export const checkAccountStatus = (user: any) => {
  if(user.role === "VENDOR" && (user.vendor?.isDeleted || user.vender?.isSuspended)) throw new ApiError(403, "Vendor account is suspended or deleted.");

  if (user.role === "CUSTOMER" && (user.customer?.isDeleted || user.customer?.isSuspended)) throw new ApiError(403, "Customer account is suspended or deleted.");
}