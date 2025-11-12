import { NextApiRequest, NextApiResponse } from "next";

export default async function chatMultiagentResponse(req: NextApiRequest, res: NextApiResponse) {
    try {
        const body = req.body;
        const aiConfigKey: string = body?.aiConfigKey;
        const userInput: string = body?.userInput;

        // Validation
        if (!aiConfigKey || typeof aiConfigKey !== 'string') {
            return res.status(400).json({ error: "Missing or invalid 'aiConfigKey'" });
        }
        if (!userInput || typeof userInput !== 'string') {
            return res.status(400).json({ error: "Missing or invalid 'userInput'" });
        }

        // Call Python FastAPI backend multi-agent endpoint
        const pythonApiUrl = process.env.PYTHON_API_URL || "http://localhost:8000";
        
        const response = await fetch(`${pythonApiUrl}/api/chat-multiagent`, {
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
            throw new Error(`Multi-agent API responded with status: ${response.status}`);
        }

        const pythonResponse = await response.json();
        
        // Forward the response from Python backend
        const data = {
            response: pythonResponse.response,
            modelName: pythonResponse.modelName,
            enabled: pythonResponse.enabled,
            requestId: pythonResponse.requestId,
            agentFlow: pythonResponse.agentFlow || [],
            metrics: pythonResponse.metrics,
            pendingMetrics: pythonResponse.pendingMetrics || false,
            error: pythonResponse.error
        };

        res.status(200).json(data);
    } catch (error) {
        console.error("Error calling multi-agent API:", error);
        res.status(500).json({ 
            error: "Internal Server Error",
            response: "I'm sorry, an error occurred while processing your request.",
            modelName: "",
            enabled: false,
            requestId: ""
        });
    }
}

