import ApiError from "../app/errors/ApiError"
import prisma from "../shared/prisma"


export const findProductById = async (id: string )=> {
  const product = await prisma.product.findUnique({
    where:{id}
  })

  if(!product || product.deletedAt !== null) throw new ApiError(404, "product Not Found")
  return product;
}

