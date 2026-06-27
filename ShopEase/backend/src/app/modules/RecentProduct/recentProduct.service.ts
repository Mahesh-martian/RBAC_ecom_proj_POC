import prisma from "../../../shared/prisma";

const saveRecentProduct = async (user: any, payload: string[]) => {
  const { id } = user;

  const recentProductsData = payload.map((productId) => ({
    userId: id,
    productId,
    visitedAt: new Date(),
  }));

  const savedData = await prisma.recentProduct.createMany({
    data: recentProductsData,
    skipDuplicates: true,
  });

  return;
};
const getRecentProduct = async (user: any) => {
  const { id: userId } = user;

  const recentProducts = await prisma.recentProduct.findMany({
    where: {
      userId,
    },
    orderBy: {
      visitedAt: "desc",
    },
    include: { product: true },
    take: 10,
  });

  

  return recentProducts;
};

export const RecentProductServices = {
  saveRecentProduct,
  getRecentProduct,
};
