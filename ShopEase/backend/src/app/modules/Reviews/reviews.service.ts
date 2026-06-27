import prisma from "../../../shared/prisma"
import { Request } from "express";
import { TFile } from "../../types/file";
import { fileUploader } from "../../../helpers/fileUploader";
import ApiError from "../../errors/ApiError";
import { TReview } from "./reviews.type";
import { TPaginationOptions } from "../../types/pagination";
import { paginationHelper } from "../../../helpers/paginationHelper";



const createReview = async (customerId: string, data: TReview) => {

  const { productId, comment, rating } = data;

  const hasPurchased = await prisma.order.findFirst({
    where: {
      customerId: customerId,
      order_items: {
        some: {
          productId: productId,
        },
      },
      status: "COMPLETED", 
    },
  });

  if (!hasPurchased) throw new ApiError(400, "You can only review products you have purchased.");

  const existingReview = await prisma.review.findFirst({
    where: {
      customerId,
      productId,
    },
  });

  if (existingReview) {
    throw new Error("You have already reviewed this product.");
  }

  const review = await prisma.review.create({
    data: {
      customerId,
      productId,
      comment,
      rating,
    },
  });

  return review;

}


const getReviews = async (user:any, options: TPaginationOptions) => {
const { page, limit, skip } = paginationHelper.calculatePagination(options)

let reviews;
let total = 0;

 if(user.role === "VENDOR"){
  const vendorId = user.vendor.id

  reviews = await prisma.review.findMany({
    where: {
      product: {
        vendorId: vendorId, 
      },
    },
    skip,
    take: limit,
    include: {
      product: true, 
      customer: true, 
    },
  });

  // Count total reviews for vendor's products
  total = await prisma.review.count({
    where: {
      product: {
        vendorId: vendorId,
      },
    },
  });
  
 } else if(user.role === "ADMIN"){
  reviews = await prisma.review.findMany({
    skip,
    take: limit,
    include: {
      product: true, 
      customer: true, 
    },
  });

  // Count total reviews
  total = await prisma.review.count();
 }

 return {
  data: reviews,
  meta: {total, page, limit}
 
};

}



export const ReviewServices = {
  createReview,
  getReviews,
}