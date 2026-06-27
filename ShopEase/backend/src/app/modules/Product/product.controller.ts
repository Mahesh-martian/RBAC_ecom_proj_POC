import { Request, Response } from "express";
import catchAsync from "../../../shared/catchAsync";
import {  ProductServices } from "./product.service";
import sendResponse from "../../../shared/sendResponse";
import pick from "../../../shared/pick";
import { productFilterableFields } from "./product.constant";

const createAProduct = catchAsync(async (req: Request &{user?: any}, res: Response) => {
  const result = await ProductServices.createAProduct(req.user, req);

  sendResponse(res, {
    statusCode: 201,
    success: true,
    message: "Product created successfully",
    data: result,
  });
});

const getAllProducts = catchAsync(async (req: Request, res: Response) => {
  const filters = pick(req.query, productFilterableFields)
  const options = pick(req.query, ["limit", "page", "sortBy", "sortOrder"]);

  const result = await ProductServices.getAllProducts(filters, options);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Products fetched successfully",
    data: result.data,
    meta: result.meta,
  });
});

const getAllVendorProducts = catchAsync(async (req: Request &{user?: any}, res: Response) => {
   const options = pick(req.query, ["limit", "page", "sortBy", "sortOrder"]);

  const result = await ProductServices.getAllVendorProducts(options, req.user);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Products fetched successfully for vendor",
    data: result.data,
    meta: result.meta,
  });
});

const getAProduct = catchAsync(async (req: Request, res: Response) => {
  const { productId } = req.params;

  const result = await ProductServices.getAProduct(productId);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Product fetched successfully",
    data: result,
  });
});

const duplicateAProduct = catchAsync(async (req: Request, res: Response) => {
  const { productId } = req.params;

  const result = await ProductServices.duplicateAProduct(productId);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Product duplicated successfully",
    data: result,
  });
});

const updateAProduct = catchAsync(async (req: Request &{user?: any}, res: Response) => {
  const { productId } = req.params;

  const result = await ProductServices.updateAProduct(productId, req.user, req);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Product updated successfully",
    data: result,
  });
});



export const ProductController = {
  createAProduct,
  duplicateAProduct,
  getAllProducts,
  getAllVendorProducts,
  getAProduct,
  updateAProduct
};
