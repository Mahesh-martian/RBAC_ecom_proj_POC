import { Prisma } from "@prisma/client";
import { paginationHelper } from "../../../helpers/paginationHelper";
import prisma from "../../../shared/prisma";
import ApiError from "../../errors/ApiError";
import { TPaginationOptions } from "../../types/pagination";
import { Request } from "express";
import { TFile } from "../../types/file";
import { fileUploader } from "../../../helpers/fileUploader";
import { TProductFilterRequest } from "./product.type";
import { productSearchableFields } from "./product.constant";
import { findProductById } from "../../../helpers/productHelpers";

const createAProduct = async (user: any, req: Request) => {
  // upload files to cloudinary
  // add cloudinary link to data
  // add it into db
  const files = req.files as TFile[];
  if (files?.length === 0)
    throw new ApiError(400, "At least one image is required");

  const vendorId = user.vendor.id;

  const shop = await prisma.shop.findFirst({
    where: { vendorId },
    select: {
      id: true,
    },
  });

  if (!shop) throw new ApiError(404, "Shop not found");

  const shopId = shop.id;

  const uploadedFiles = await fileUploader.uploadMultipleToCloudinary(files);

  const imageUrls = uploadedFiles.map((file) => file.secure_url);

  const productData = {
    ...req.body,
    image: imageUrls,
    vendorId,
    shopId,
  };

  const product = await prisma.product.create({
    data: productData,
  });

  return product;
};

const getAllProducts = async (
  params: TProductFilterRequest,
  options: TPaginationOptions
) => {
  // create filter condition
  // get product data
  // get meta data
  const { page, limit, skip } = paginationHelper.calculatePagination(options);
  const { searchTerm, ...filterData } = params;

  const andConditions: Prisma.ProductWhereInput[] = [];

  if (params.searchTerm) {
    andConditions.push({
      OR: productSearchableFields.map((field) => ({
        [field]: {
          contains: params.searchTerm,
          mode: "insensitive",
        },
      })),
    });
  }

  if (Object.keys(filterData).length > 0) {
    andConditions.push({
      AND: Object.keys(filterData).map((key) => ({
        [key]: {
          equals: (filterData as any)[key],
        },
      })),
    });
  }

  const whereConditions: Prisma.ProductWhereInput = { AND: andConditions };

  const result = await prisma.product.findMany({
    where: whereConditions,
    skip,
    take: limit,
    orderBy:
      options.sortBy && options.sortOrder
        ? { [options.sortBy]: options.sortOrder }
        : { createdAt: "desc" },
  });

  const total = await prisma.product.count({
    where: whereConditions,
  });

  return {
    data: result,
    meta: { page, limit, total },
  };
};



const getAllVendorProducts = async (options: TPaginationOptions, user: any) => {
  // get product data based on vendor id
  // get meta data
  const { page, limit, skip } = paginationHelper.calculatePagination(options);

  const result = await prisma.product.findMany({
    where: {
      vendorId: user.vendor.id,
    },
    skip,
    take: limit,
    orderBy:
      options.sortBy && options.sortOrder
        ? { [options.sortBy]: options.sortOrder }
        : { createdAt: "desc" },
    include: {
      category: {
        select: {
          name: true,
        },
      },
    },
  });

  const total = await prisma.product.count({
    where: {
      vendorId: user.vendor.id,
    },
  });

  return {
    data: result.map((product) => ({
      ...product,
      categoryName: product.category.name,
    })),
    meta: { page, limit, total },
  };
};

const getAProduct = async (id: string) => {
  const product = await prisma.product.findUnique({
    where: { id },
    include: {
      reviews: {
        include: {
          customer: {
            select: {
              id: true,
              name: true,
              profilePhoto: true,
            },
          },
        },
      },
      shop: true,
      category: true,
    },
  });

  if (!product || product.deletedAt !== null)
    throw new ApiError(404, "product Not Found");

  return product;
};

const duplicateAProduct = async (id: string) => {
  // find existing product
  // remove id, createdAt, updatedAt, deletedAt
  // add the data to db
  const result = await findProductById(id);

  const {
    id: _,
    updatedAt: __,
    createdAt: ___,
    deletedAt: ____,
    ...duplicateData
  } = result;

  return await prisma.product.create({
    data: duplicateData,
  });
};

const updateAProduct = async (id: string, user: any, req: Request) => {
  // get product
  // update data

  const result = await findProductById(id);

  const files = req.files as TFile[];
  let imageUrls: string[] = [];

  if (files?.length > 0) {
    const uploadedFiles = await fileUploader.uploadMultipleToCloudinary(files);

    imageUrls = uploadedFiles.map((file) => file.secure_url);
  }

  const updatedImages = [...result.image, ...imageUrls];

  const productData = {
    ...req.body,
    image: updatedImages,
  };

  const updatedProduct = await prisma.product.update({
    where: { id },
    data: productData,
  });

  return updatedProduct;
};

export const ProductServices = {
  createAProduct,
  duplicateAProduct,
  getAllProducts,
  getAllVendorProducts,
  getAProduct,
  updateAProduct,
};
