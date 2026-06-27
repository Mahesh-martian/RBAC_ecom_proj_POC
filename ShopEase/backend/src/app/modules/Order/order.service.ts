import { Prisma } from "@prisma/client";
import { paginationHelper } from "../../../helpers/paginationHelper";
import prisma from "../../../shared/prisma";
import ApiError from "../../errors/ApiError";
import { TPaginationOptions } from "../../types/pagination";
import { Request } from "express";
import { TProductFilterRequest } from "./order.type";

const createOrder = async (user: any, req: Request) => {
  const { vendorId, totalAmount, products } = req.body;

  const customerId = user.customer.id

  if (!Array.isArray(products) || products.length === 0) throw new ApiError(400,"Products array must not be empty.");
  
  return await prisma.$transaction(async (tx) => {
    // Create the order first
    const order = await tx.order.create({
      data: {
        customerId: customerId, 
        vendorId,
        totalAmount,
        status: "PENDING",
      },
    });

    // Create order items
    const orderItems = products.map((item) => ({
      orderId: order.id, 
      productId: item.productId,
      quantity: item.quantity,
      price: item.price,
      discount: item.discount || 0,
    }));

    await tx.orderItem.createMany({
      data: orderItems,
    });

    return order; 
  });

};

const getOrders = async (
  params: TProductFilterRequest,
  options: TPaginationOptions,
  user: any
) => {
  // create filter condition
  // get product data
  // get meta data
  const { page, limit, skip } = paginationHelper.calculatePagination(options);
  const { searchTerm, ...filterData } = params;

  let orders;
  let total = 0;

  if(user.role === "CUSTOMER"){
    const customerId = user.customer.id

    orders = await prisma.order.findMany({
      where: {customerId},
      include:{order_items: true},
      skip,
    take: limit,
    orderBy:
      options.sortBy && options.sortOrder
        ? { [options.sortBy]: options.sortOrder }
        : { createdAt: "desc" },
    })

    total = await prisma.order.count({
    where: {customerId},
  });
  } else if(user.role === "VENDOR"){
    const vendorId = user.vendor.id

    orders = await prisma.order.findMany({
      where: {vendorId},
      include:{order_items: true},
      skip,
    take: limit,
    orderBy:
      options.sortBy && options.sortOrder
        ? { [options.sortBy]: options.sortOrder }
        : { createdAt: "desc" },
    })

    total = await prisma.order.count({
    where: {vendorId},
  });
  } else if(user.role === "ADMIN"){

    orders = await prisma.order.findMany({
      where: {deletedAt: null},
      include:{order_items: true, customer: true, vendor: true},
      skip,
    take: limit,
    orderBy:
      options.sortBy && options.sortOrder
        ? { [options.sortBy]: options.sortOrder }
        : { createdAt: "desc" },
    })

    total = await prisma.order.count({
    where: {deletedAt: null},
  });
  }

   return {
    data: orders,
    meta: { page, limit, total },
  };

  // const andConditions: Prisma.OrderWhereInput[] = [];

  // if (params.searchTerm) {
  //   andConditions.push({
  //     OR: orderFilterableFields.map((field) => ({
  //       [field]: {
  //         contains: params.searchTerm,
  //         mode: "insensitive",
  //       },
  //     })),
  //   });
  // }

  // if (Object.keys(filterData).length > 0) {
  //   andConditions.push({
  //     AND: Object.keys(filterData).map((key) => ({
  //       [key]: {
  //         equals: (filterData as any)[key],
  //       },
  //     })),
  //   });
  // }

  // const whereConditions: Prisma.OrderWhereInput = { AND: andConditions };

  // const result = await prisma.order.findMany({
  //   where: whereConditions,
  //   skip,
  //   take: limit,
  //   orderBy:
  //     options.sortBy && options.sortOrder
  //       ? { [options.sortBy]: options.sortOrder }
  //       : { createdAt: "desc" },
  // });

  // const total = await prisma.order.count({
  //   where: whereConditions,
  // });

  // return {
  //   data: result,
  //   meta: { page, limit, total },
  // };
};



export const OrderServices = {
  createOrder,
  getOrders
};
