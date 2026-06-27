import prisma from "../../../shared/prisma";
import { Request } from "express";
import { TFile } from "../../types/file";
import { fileUploader } from "../../../helpers/fileUploader";
import ApiError from "../../errors/ApiError";
import { TPaginationOptions } from "../../types/pagination";
import { paginationHelper } from "../../../helpers/paginationHelper";

const createShop = async (user: any, req: Request) => {
  //  upload file to cloudinary
  // save data into db
  const file = req.file as TFile;

  if (file) {
    const uploadToCloudinary = await fileUploader.uploadToCloudinary(file);
    req.body.logo = uploadToCloudinary?.secure_url;
  }

  req.body.vendorId = user.vendor.id;

  const shop = await prisma.shop.create({ data: req.body });

  return shop;
};

const getAShop = async (payload: any) => {
  // fetch shop data
  // return that data

  const shop = await prisma.shop.findFirst({
    where: { vendorId: payload.vendor.id },
  });

  if (!shop) throw new ApiError(404, "Shop not found");
  return shop;
};

const getAllShops = async (options: TPaginationOptions) => {
  const { page, limit, skip } = paginationHelper.calculatePagination(options);
  const shops = await prisma.shop.findMany({
    where: { isBlackListed: false },
    include: {
      products: {
        include: {
          reviews: true,
        },
      },
      vendor: {
        include: {
          follows: true,
        },
      },
    },
    skip,
    take: limit,
    orderBy:
      options.sortBy && options.sortOrder
        ? { [options.sortBy]: options.sortOrder }
        : { createdAt: "desc" },
  });

  if (!shops) throw new ApiError(404, "shops not found");

  const total = await prisma.shop.count({
    where: { isBlackListed: false },
  });

  return {
    data: shops,
    meta: { page, limit, total },
  };
};

const getAShopForShopDetailPage = async (payload: string) => {
  const shop = await prisma.shop.findUnique({
    where: { id: payload },
    include: {
      products: {
        include: {
          reviews: true,
        },
      },
      vendor: {
        include: {
          follows: true,
        },
      },
    },
  });

  if (!shop) throw new ApiError(404, "shop not found");
  return shop;
};

export const ShopServices = {
  createShop,
  getAShop,
  getAllShops,
  getAShopForShopDetailPage,
};
