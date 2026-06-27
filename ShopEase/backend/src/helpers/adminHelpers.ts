import ApiError from "../app/errors/ApiError"
import prisma from "../shared/prisma"


export const findCategoryById = async (id: string )=> {
  const category = await prisma.category.findUnique({
    where:{id}
  })

  if(!category || category.deletedAt !== null) throw new ApiError(404, "Category Not Found")
  return category;
}

