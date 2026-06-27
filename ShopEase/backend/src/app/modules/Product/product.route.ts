import express, { NextFunction, Request, Response } from "express";
import {  ProductController } from "./product.controller";
import validateRequest from "../../middlewares/validateRequest";
import auth from "../../middlewares/auth";
import { UserRole } from "@prisma/client";
import {  productValidation } from "./product.validation";
import { fileUploader } from "../../../helpers/fileUploader";

const router = express.Router();


router.post("/", auth(UserRole.VENDOR),
fileUploader.upload.array("images", 10), 
(req: Request, res: Response, next: NextFunction)=>{
  req.body = productValidation.createProduct.parse(JSON.parse(req.body.data))
  return ProductController.createAProduct(req, res, next)
})

router.post("/duplicate/:productId", auth(UserRole.VENDOR), ProductController.duplicateAProduct)

router.get("/",   ProductController.getAllProducts)
router.get("/vendor-product", auth(UserRole.VENDOR),  ProductController.getAllVendorProducts)

router.get("/:productId",   ProductController.getAProduct)

router.patch("/:productId", auth(UserRole.VENDOR),
fileUploader.upload.array("images", 10), 
(req: Request, res: Response, next: NextFunction)=>{
  req.body = productValidation.updateProduct.parse(JSON.parse(req.body.data))
  return ProductController.updateAProduct(req, res, next)
})


export const ProductRoutes = router;
