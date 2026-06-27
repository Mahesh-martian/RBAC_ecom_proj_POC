import prisma from "../../../shared/prisma"
import { Request } from "express";
import { TFile } from "../../types/file";
import { fileUploader } from "../../../helpers/fileUploader";
import ApiError from "../../errors/ApiError";
import Stripe from "stripe";
import config from "../../../config";
import { TPaginationOptions } from "../../types/pagination";
import { paginationHelper } from "../../../helpers/paginationHelper";

const stripe = new Stripe(config.STRIPE_SECRET_KEY as string)

const createPaymentIntent = async (data: {amount: number}) => {
//  upload file to cloudinary
// save data into db


  const paymentIntent = await stripe.paymentIntents.create({
    amount: data.amount *100,
    currency: 'usd',
    payment_method_types: ['card'],
  });
  return paymentIntent;

}


const savePaymentInfo = async(data: any) => {
  const { orderId, status} = data

  return await prisma.$transaction(async (prisma) => {
    // Step 1: Save the payment info
    const payment = await prisma.payment.create({
      data: data,
    });

    // Step 2: If payment is successful, update the order status and link the payment
    if (status === "SUCCESS") {
      // Update order status and link payment
      const order = await prisma.order.update({
        where: {
          id: orderId,
        },
        data: {
          status: "COMPLETED",
          payment: {
            connect: { id: payment.id },
          },
        },
        include: {
          order_items: true,
        },
      });

      // Step 3: Reduce inventory for each product in the order
      for (const orderItem of order.order_items) {
        const { productId, quantity } = orderItem;

        // Reduce the inventory of the product
        await prisma.product.update({
          where: {
            id: productId,
          },
          data: {
            inventory: {
              decrement: quantity, 
            },
          },
        });
      }
    }

    return payment;
  });
}

const getAllTransactions = async (options: TPaginationOptions, user: any) => {
  
  const { page, limit, skip } = paginationHelper.calculatePagination(options)
  const result = await prisma.payment.findMany({
    where: {status: "SUCCESS"},
    skip,
    take: limit,
    orderBy:
      options.sortBy && options.sortOrder
        ? { [options.sortBy]: options.sortOrder }
        : { createdAt: "desc" },
  })

  const total = await prisma.payment.count({
    where:{status: "SUCCESS"}
  })

  return {
    data: result,
    meta: { page, limit, total },
  };

}



export const PaymentServices = {
  createPaymentIntent, savePaymentInfo, getAllTransactions

}