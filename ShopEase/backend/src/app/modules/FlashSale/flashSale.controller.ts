import { Request, Response } from "express";
import catchAsync from "../../../shared/catchAsync";
import { FlashSaleServices } from "./flashSale.service";
import sendResponse from "../../../shared/sendResponse";
import pick from "../../../shared/pick";
import { productFilterableFields } from "./flashSale.constant";

const createAFlashSale = catchAsync(
  async (req: Request, res: Response) => {
    const result = await FlashSaleServices.createAFlashSale(req.body);

    sendResponse(res, {
      statusCode: 201,
      success: true,
      message: "Flash Sale created successfully",
      data: result,
    });
  }
);

const getAllFlashSale = catchAsync(async (req: Request, res: Response) => {
  const options = pick(req.query, ["limit", "page", "sortBy", "sortOrder"]);

  const result = await FlashSaleServices.getAllFlashSale(options);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "All Flash Sale fetched successfully",
    data: result.data,
    meta: result.meta,
  });
});

const getAFlashSale = catchAsync(async (req: Request, res: Response) => {
  const { id } = req.params;

  const result = await FlashSaleServices.getAFlashSale(id);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Flash Sale fetched successfully",
    data: result,
  });
});

const updateAFlashSale = catchAsync(
  async (req: Request, res: Response) => {
    const { id } = req.params;

    const result = await FlashSaleServices.updateAFlashSale(
      id,
      req.body
    );

    sendResponse(res, {
      statusCode: 200,
      success: true,
      message: "Flash Sale updated successfully",
      data: result,
    });
  }
);

export const FlashSaleController = {
  createAFlashSale,  
  getAllFlashSale,
  getAFlashSale,
  updateAFlashSale,
};
