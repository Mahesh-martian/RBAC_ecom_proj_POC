import { GoogleGenerativeAI } from "@google/generative-ai";
import config from "../../../config";
import ApiError from "../../errors/ApiError";

// Initialize the Gemini API
const genAI = new GoogleGenerativeAI(config.GEMINI_API_KEY as string);

// Initialize conversation history with system instructions
let conversationHistory = [
  {
    role: "user",
    parts: [
      {
        text: "You are a helpful shopping assistant. Your job is to assist users with their shopping-related questions, such as product recommendations, price comparisons, and store locations. Be friendly, informative, and concise.",
      },
    ],
  },
  {
    role: "model",
    parts: [
      {
        text: "Sure! How can I assist you with shopping today?",
      },
    ],
  },
];

const chat = async (userPrompt: string) => {

  if (!userPrompt) throw new ApiError(400, "User prompt is required.");

  try {
    // Initialize the model
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

    // Start the chat session with current history
    const chatSession = model.startChat({
      history: conversationHistory, // Send full conversation history
    });

    // Send the user message
    const result = await chatSession.sendMessage(userPrompt);

    // Validate the response
    if (!result || !result.response || !result.response.text) {
      throw new ApiError(500, "Failed to get a valid response from the model.");
    }

    // Extract the model's response
    const modelResponse = result.response.text();

    // Append the new user input and model response to conversation history
    conversationHistory.push({
      role: "user",
      parts: [{ text: userPrompt }],
    });
    
    conversationHistory.push({
      role: "model",
      parts: [{ text: modelResponse }],
    });

    console.log('Conversation chat history', conversationHistory)

    return modelResponse;
  } catch (error) {
    console.error("Error in chat function:", error);
    throw new ApiError(500, "An error occurred while processing the chat.");
  }
};
const getChatHistory = async (userId: string) => {
 
};

export const ChatBotServices = {
  chat,getChatHistory
};
