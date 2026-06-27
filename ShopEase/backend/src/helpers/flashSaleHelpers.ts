import ApiError from "../app/errors/ApiError"
import prisma from "../shared/prisma"


export const findFlashSaleById = async (id: string )=> {
  const result = await prisma.flashSale.findUnique({
    where:{id}, include:{product:true}
  })

  if(!result) throw new ApiError(404, "Flash sale Not Found")
  return result;
}

