import { NextApiRequest, NextApiResponse } from "next";
import {
    ChatBotAIApiResponseInterface,
    UserChatInputResponseInterface,
} from "@/utils/typescriptTypesInterfaceIndustry";

export default async function chatToggleHealth(req: NextApiRequest, res: NextApiResponse) {
    try {
        const body: UserChatInputResponseInterface = req.body;
        const aiConfigKey: string = body?.aiConfigKey;
        const userInput: string = body?.userInput;

        // Validation
        if (!aiConfigKey || typeof aiConfigKey !== 'string') {
            return res.status(400).json({ error: "Missing or invalid 'aiConfigKey'." });
        }
        if (!userInput || typeof userInput !== 'string') {
            return res.status(400).json({ error: "Missing or invalid 'userInput'." });
        }

        // Call Python FastAPI backend (ToggleHealth multi-agent endpoint)
        const pythonApiUrl = process.env.PYTHON_API_URL || "http://localhost:8000";
        
        const response = await fetch(`${pythonApiUrl}/api/chat-togglehealth`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                aiConfigKey: aiConfigKey,
                userInput: userInput,
            }),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            throw new Error(errorData.error || `Backend responded with status: ${response.status}`);
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
        console.error("Error calling ToggleHealth multi-agent API:", error);
        res.status(500).json({ 
            error: error instanceof Error ? error.message : "Internal Server Error"
        });
    }
}

