import express from "express";
import { ChatBotController } from "./chatbot.controller";
import validateRequest from "../../middlewares/validateRequest";
import { userValidation } from "../User/user.validation"
import auth from "../../middlewares/auth";
import { UserRole } from "@prisma/client";

const router = express.Router();

// Save a chat message
router.post("/", ChatBotController.chat);

// Get chat history
// router.get("/", auth(UserRole.CUSTOMER), ChatBotController.getChatHistory);


export const ChatBotRoutes = router;
