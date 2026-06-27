import express from "express";
import { AdminController } from "./admin.controller";
import validateRequest from "../../middlewares/validateRequest";
import { userValidation } from "../User/user.validation"
import auth from "../../middlewares/auth";
import { UserRole } from "@prisma/client";
import { adminValidation } from "./admin.validation";

const router = express.Router();

// !User related routes
router.get("/users", auth(UserRole.ADMIN), AdminController.getAllUser)
router.get("/users/:userId", auth(UserRole.ADMIN), AdminController.getUserById)
router.patch("/users/:userId", auth(UserRole.ADMIN), validateRequest(userValidation.updateUser), AdminController.updateUserIntoDB)
router.delete("/users/:userId", auth(UserRole.ADMIN), AdminController.deleteUserFromDB)

// !Vendor related routes 
router.patch("/shop/:shopId", auth(UserRole.ADMIN), validateRequest(adminValidation.blacklistVendorShop), AdminController.blacklistVendorShop)

// !Categories related routes
router.post("/categories", auth(UserRole.ADMIN), validateRequest(adminValidation.createCategory), AdminController.createACategory)
router.get("/categories", auth(UserRole.ADMIN), AdminController.getAllCategories)
router.get("/categories/:categoryId", auth(UserRole.ADMIN), AdminController.getACategory)
router.patch("/categories/:categoryId", auth(UserRole.ADMIN), validateRequest(adminValidation.updateCategory), AdminController.updateACategory)
router.delete("/categories/:categoryId", auth(UserRole.ADMIN), AdminController.deleteACategory)

export const AdminRoutes = router;
