import express from "express";

import { PaymentController } from "./payment.controller";
import validateRequest from "../../middlewares/validateRequest";
import { paymentValidation } from "./payment.validation";
import auth from "../../middlewares/auth";
import { UserRole } from "@prisma/client";

const router = express.Router();

router.post("/create-payment-intent", validateRequest(paymentValidation.createPaymentIntent),
PaymentController.createPaymentIntent);

router.post("/payment-confirm", validateRequest(paymentValidation.confirmPayment),
PaymentController.paymentConfirm);

router.get("/", auth(UserRole.ADMIN), PaymentController.getAllTransactions)




export const PaymentRoutes = router;
