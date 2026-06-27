import express from "express";
import {  FollowController,  } from "./follow.controller";
import auth from "../../middlewares/auth";
import { UserRole } from "@prisma/client";

const router = express.Router();

router.post("/", auth(UserRole.CUSTOMER), FollowController.follow)

router.get("/", auth(UserRole.VENDOR), FollowController.getFollowers)
router.get("/:vendorId", FollowController.getFollowersOfAShop)

router.delete("/:vendorId", auth(UserRole.CUSTOMER), FollowController.unfollow)

export const FollowRoutes = router;
