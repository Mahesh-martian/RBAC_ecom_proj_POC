import { Request, Response } from "express";
import catchAsync from "../../../shared/catchAsync";

import sendResponse from "../../../shared/sendResponse";
import { RecentProductServices } from "./recentProduct.service";

const saveRecentProduct = catchAsync(
  async (req: Request & { user?: any }, res: Response) => {
    const { products } = req.body;
    await RecentProductServices.saveRecentProduct(req.user, products);

    sendResponse(res, {
      statusCode: 201,
      success: true,
      message: "Recent products saved successfully.",
      data: "",
    });
  }
);

const getRecentProduct = catchAsync(
  async (req: Request & { user?: any }, res: Response) => {
    const result = await RecentProductServices.getRecentProduct(req.user);

    sendResponse(res, {
      statusCode: 201,
      success: true,
      message: "Recent products saved successfully.",
      data: result,
    });
  }
);

export const RecentProductController = {
  saveRecentProduct,
  getRecentProduct,
};
