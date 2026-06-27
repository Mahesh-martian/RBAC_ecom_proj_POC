import { Request, Response } from "express";
import catchAsync from "../../../shared/catchAsync";
import { PaymentServices } from "./payment.service";
import sendResponse from "../../../shared/sendResponse";
import pick from "../../../shared/pick";


const createPaymentIntent = catchAsync(
  async (req: Request, res: Response) => {
    const result = await PaymentServices.createPaymentIntent(req.body);

    sendResponse(res, {
      statusCode: 201,
      success: true,
      message: "Payment Intent Created Successfully.",
      data: result,
    });
  }
);

const paymentConfirm = catchAsync(
  async (req: Request, res: Response) => {
    const result = await PaymentServices.savePaymentInfo(req.body);

    sendResponse(res, {
      statusCode: 201,
      success: true,
      message: "Payment Saved Successfully.",
      data: result,
    });
  }
);

const getAllTransactions = catchAsync (async (req: Request & {user?: any}, res: Response) => {
    const options = pick(req.query, ["limit", "page", "sortBy", "sortOrder"]);

    const result = await PaymentServices.getAllTransactions(options, req.user)

    sendResponse(res, {
      statusCode: 200,
      success: true,
      message: "Transactions fetched successfully",
      data: result.data,
      meta: result.meta,
    });
  }
)

export const PaymentController = {
  createPaymentIntent, paymentConfirm, getAllTransactions
};
