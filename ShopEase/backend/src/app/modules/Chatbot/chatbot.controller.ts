import  {Request, Response} from "express"
import catchAsync from "../../../shared/catchAsync"
import { ChatBotServices } from "./chatbot.service"
import sendResponse from "../../../shared/sendResponse"

const chat  = catchAsync(async (req: Request & { user?: any }, res: Response) => {
  // const userId = req.user.customer.id;

  // const result = await ChatBotServices.chat(userId, req.body)
  const result = await ChatBotServices.chat(req.body.message)

  console.log('result', result)

  sendResponse(res, {
    statusCode: 201,
    success: true,
    message: "Chat saved successfully.",
    data: result
  })
})

// Get chat history
const getChatHistory = catchAsync(async (req: Request & { user?: any }, res: Response) => {
  const userId = req.user.customer.id;

  const result = await ChatBotServices.getChatHistory(userId);

  sendResponse(res, {
    statusCode: 200,
    success: true,
    message: "Chat history retrieved successfully.",
    data: result,
  });
});

export const ChatBotController = {
  chat, getChatHistory
}