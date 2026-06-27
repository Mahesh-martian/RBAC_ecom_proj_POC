import { Request, Response } from "express";
import catchAsync from "../../../shared/catchAsync";
import { ReviewServices } from "./reviews.service";
import sendResponse from "../../../shared/sendResponse";
import pick from "../../../shared/pick";

const createReview = catchAsync(
  async (req: Request & { user?: any }, res: Response) => {
    const result = await ReviewServices.createReview(req.user.customer.id, req.body);

    sendResponse(res, {
      statusCode: 201,
      success: true,
      message: "Review Created Successfully.",
      data: result,
    });
  }
);

const getReviews = catchAsync(
  async (req: Request & { user?: any }, res: Response) => {
    const options = pick(req.query, ["limit", "page", "sortBy", "sortOrder"]);
    const result = await ReviewServices.getReviews(req.user, options);

    sendResponse(res, {
      statusCode: 200,
      success: true,
      message: "Reviews fetched successfully",
      data: result.data,
      meta: result.meta
    });
  }
);

export const ReviewController = {
  createReview,
  getReviews,
};
