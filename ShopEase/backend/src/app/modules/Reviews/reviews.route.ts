import express from "express";
import validateRequest from "../../middlewares/validateRequest";
import auth from "../../middlewares/auth";
import { UserRole } from "@prisma/client";
import { reviewValidation } from "./reviews.validation";
import { ReviewController } from "./reviews.controller";

const router = express.Router();

router.post("/",auth(UserRole.CUSTOMER), validateRequest(reviewValidation.createReview), ReviewController.createReview)


router.get("/", auth(UserRole.VENDOR, UserRole.ADMIN), ReviewController.getReviews);


export const ReviewRoutes = router;
