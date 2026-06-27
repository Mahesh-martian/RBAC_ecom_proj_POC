import { Request, Response } from "express";
import catchAsync from "../../../shared/catchAsync";
import { FollowServices } from "./follow.service";
import sendResponse from "../../../shared/sendResponse";

const follow = catchAsync(
  async (req: Request & { user?: any }, res: Response) => {
    const result = await FollowServices.follow(req.user, req.body);

    sendResponse(res, {
      statusCode: 201,
      success: true,
      message: "Vendor followed successfully",
      data: result,
    });
  }
);

const getFollowers = catchAsync(async (req: Request &{user?: any}, res: Response) => {

  const result = await FollowServices.getFollowers(req.user.vendor.id);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Follower count fetched successfully",
    data: result,

  });
});
const getFollowersOfAShop = catchAsync(async (req: Request, res: Response) => {

  const result = await FollowServices.getFollowersOfAShop(req.params.vendorId);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Follower count fetched successfully",
    data: result,

  });
});

const unfollow = catchAsync(async (req: Request & { user?: any }, res: Response) => {
  const { vendorId } = req.params;

  const result = await FollowServices.unfollow(vendorId, req.user.customer.id);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Vendor unfollowed successfully",
    data: result,
  });
});


export const FollowController = {
  follow, unfollow, getFollowers,getFollowersOfAShop
};
