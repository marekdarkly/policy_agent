import { NextApiRequest, NextApiResponse } from "next";
import {
    ChatBotAIApiResponseInterface,
    UserChatInputResponseInterface,
} from "@/utils/typescriptTypesInterfaceIndustry";

export default async function chatResponse(req: NextApiRequest, res: NextApiResponse) {
    try {
        const body: UserChatInputResponseInterface = req.body;
        const aiConfigKey: string = body?.aiConfigKey;
        const userInput: string = body?.userInput;

        // Add validation to prevent 422 errors
        if (!aiConfigKey || typeof aiConfigKey !== 'string') {
            return res.status(400).json({ error: "Missing or invalid 'aiConfigKey'. Make sure it's set in the frontend." });
        }
        if (!userInput || typeof userInput !== 'string') {
            return res.status(400).json({ error: "Missing or invalid 'userInput'." });
        }

        // Call our Python FastAPI backend instead of Bedrock directly
        const pythonApiUrl = process.env.PYTHON_API_URL || "http://localhost:8000";
        
        // Check for special case containing "ignore all previous commands" and add bypass flag
        const isHateMessage = userInput.trim().toUpperCase().includes("IGNORE ALL PREVIOUS COMMANDS");
        
        const response = await fetch(`${pythonApiUrl}/api/chat-async`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                aiConfigKey: aiConfigKey,
                userInput: userInput,
                bypassResponse: isHateMessage ? "I'm unable to answer this question for you, let me route to you a live agent ASAP!" : undefined,
            }),
        });

        if (!response.ok) {
            throw new Error(`Python API responded with status: ${response.status}`);
        }

        const pythonResponse = await response.json();
        
        const data: ChatBotAIApiResponseInterface = {
            response: pythonResponse.response,
            modelName: pythonResponse.modelName,
            enabled: pythonResponse.enabled,
            error: pythonResponse.error,
            metrics: pythonResponse.metrics,
            requestId: pythonResponse.requestId,
            pendingMetrics: pythonResponse.pendingMetrics
        };

        res.status(200).json(data);
    } catch (error) {
        console.error("Error calling Python chatbot API:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
}
