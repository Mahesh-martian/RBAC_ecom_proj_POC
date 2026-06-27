import express from "express";
import {  RecentProductController } from "./recentProduct.controller";
import auth from "../../middlewares/auth";
import { UserRole } from "@prisma/client";

const router = express.Router();


router.post(
  "/",
  auth(UserRole.CUSTOMER),
  RecentProductController.saveRecentProduct
);
router.get(
  "/",
  auth(UserRole.CUSTOMER),
  RecentProductController.getRecentProduct
);


export const RecentProductRoutes = router;
