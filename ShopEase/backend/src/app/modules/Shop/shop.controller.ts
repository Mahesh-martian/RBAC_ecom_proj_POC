import { Request, Response } from "express";
import catchAsync from "../../../shared/catchAsync";
import { ShopServices } from "./shop.service";
import sendResponse from "../../../shared/sendResponse";
import pick from "../../../shared/pick";

const createShop = catchAsync(
  async (req: Request & { user?: any }, res: Response) => {
    const result = await ShopServices.createShop(req.user, req);

    sendResponse(res, {
      statusCode: 201,
      success: true,
      message: "Shop Created Successfully.",
      data: result,
    });
  }
);

const getAShop = catchAsync(
  async (req: Request & { user?: any }, res: Response) => {
    const result = await ShopServices.getAShop(req.user);
    sendResponse(res, {
      statusCode: 200,
      success: true,
      message: "Shop fetched successfully",
      data: result,
    });
  }
);
const getAShopForShopDetailPage = catchAsync(
  async (req: Request, res: Response) => {
    const { shopId } = req.params;
    const result = await ShopServices.getAShopForShopDetailPage(shopId);
    sendResponse(res, {
      statusCode: 200,
      success: true,
      message: "Shop detail fetched successfully",
      data: result,
    });
  }
);

const getAllShops = catchAsync(async (req: Request, res: Response) => {
  const options = pick(req.query, ["limit", "page", "sortBy", "sortOrder"]);
  const result = await ShopServices.getAllShops(options);
  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "All Shops fetched successfully",
    data: result.data,
    meta: result.meta,
  });
});

export const ShopController = {
  createShop,
  getAShop,
  getAllShops,
  getAShopForShopDetailPage,
};
