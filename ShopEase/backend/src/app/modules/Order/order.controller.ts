import { Request, Response } from "express";
import catchAsync from "../../../shared/catchAsync";
import { OrderServices } from "./order.service";
import sendResponse from "../../../shared/sendResponse";
import pick from "../../../shared/pick";
import { orderFilterableFields } from "./order.constant";

const createOrder = catchAsync(
  async (req: Request & { user?: any }, res: Response) => {
    const result = await OrderServices.createOrder(req.user, req);

    sendResponse(res, {
      statusCode: 201,
      success: true,
      message: "Order created successfully",
      data: result,
    });
  }
);

const getOrders = catchAsync(async (req: Request & { user?: any }, res: Response) => {
  const filters = pick(req.query, orderFilterableFields);
  const options = pick(req.query, ["limit", "page", "sortBy", "sortOrder"]);

  const result = await OrderServices.getOrders(filters, options, req.user);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Orders fetched successfully",
    data: result.data,
    meta: result.meta,
  });
});




export const OrderController = {
  createOrder,
  getOrders
};
