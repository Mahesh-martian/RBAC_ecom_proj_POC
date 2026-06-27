import { Request, Response } from "express";
import catchAsync from "../../../shared/catchAsync";
import { AdminServices } from "./admin.service";
import sendResponse from "../../../shared/sendResponse";
import pick from "../../../shared/pick";
import { adminFilterableFields } from "./admin.constant";

// ! User related controller
const getAllUser = catchAsync(async (req: Request, res: Response) => {
  const filters = pick(req.query, adminFilterableFields);
  const options = pick(req.query, ["limit", "page", "sortBy", "sortOrder"]);

  const result = await AdminServices.getAllUser(filters, options);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "User data fetched successfully",
    data: result.data,
    meta: result.meta,
  });
});

const getUserById = catchAsync(async (req: Request, res: Response) => {
  const { userId } = req.params;

  const result = await AdminServices.getUserById(userId);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "User data fetched successfully",
    data: result,
  });
});

const updateUserIntoDB = catchAsync(async (req: Request, res: Response) => {
  const { userId } = req.params;

  const result = await AdminServices.updateUserIntoDB(userId, req.body);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "User Data Updated Successfully",
    data: result,
  });
});

const deleteUserFromDB = catchAsync(async (req: Request, res: Response) => {
  const { userId } = req.params;

  await AdminServices.deleteUserFromDB(userId);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "User successfully deleted",
    data: null,
  });
});

// ! Vendor related controller
const blacklistVendorShop = catchAsync(async (req: Request, res: Response) => {
  const { shopId } = req.params;

  await AdminServices.blacklistVendorShop(shopId, req.body);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Vendor shop blacklisted successfully",
    data: null,
  });
});

// ! Category related controller

const createACategory = catchAsync(async (req: Request, res: Response) => {

const   result = await AdminServices.createACategory( req.body);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Category created successfully",
    data: result,
  });
});

const getAllCategories = catchAsync(async (req: Request, res: Response) => {
  const options = pick(req.query, ["limit", "page", "sortBy", "sortOrder"])

  const result = await AdminServices.getAllCategories(options);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Categories fetched successfully",
    data: result.data,
    meta: result.meta
  });
});

const getACategory = catchAsync(async (req: Request, res: Response) => {
  const { categoryId } = req.params;

  const result = await AdminServices.getACategory(categoryId);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Category fetched successfully",
    data: result,
  });
});

const updateACategory = catchAsync(async (req: Request, res: Response) => {
  const { categoryId } = req.params;

  const result = await AdminServices.updateACategory(categoryId, req.body);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Category updated successfully",
    data: result,
  });
});

const deleteACategory = catchAsync(async (req: Request, res: Response) => {
  const { categoryId } = req.params;

  const result = await AdminServices.deleteACategory(categoryId);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Category deleted successfully",
    data: result,
  });
});

export const AdminController = {
  getAllUser,
  getUserById,
  updateUserIntoDB,
  blacklistVendorShop,
  deleteUserFromDB,
  createACategory,
  getAllCategories,
  getACategory,
  updateACategory,
  deleteACategory,
};
