import express from "express";
import { AuthController } from "./auth.controller";
import validateRequest from "../../middlewares/validateRequest";
import { userValidation } from "../User/user.validation"
import auth from "../../middlewares/auth";
import { UserRole } from "@prisma/client";

const router = express.Router();

router.post("/register", validateRequest(userValidation.registerUser), AuthController.register);
router.post("/login", AuthController.login);
router.patch("/change-password", auth(UserRole.ADMIN, UserRole.CUSTOMER, UserRole.VENDOR), AuthController.changePassword);
router.post("/forgot-password", AuthController.forgotPassword);
router.post("/reset-password", AuthController.resetPassword);
router.post("/logout", AuthController.logout);


export const AuthRoutes = router;
