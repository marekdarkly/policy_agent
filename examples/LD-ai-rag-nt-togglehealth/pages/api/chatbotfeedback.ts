import { NextApiRequest, NextApiResponse } from "next";
import { UserAIChatBotFeedbackResponseInterface } from "@/utils/typescriptTypesInterfaceIndustry";

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
    try {
        const body: UserAIChatBotFeedbackResponseInterface = JSON.parse(req.body);
        const feedback: string = body?.feedback;
        const aiConfigKey: string = body?.aiConfigKey;

        // Call our Python FastAPI backend for feedback handling
        const pythonApiUrl = process.env.PYTHON_API_URL || "http://localhost:8000";
        
        const response = await fetch(`${pythonApiUrl}/api/chatbotfeedback`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                feedback: feedback,
                aiConfigKey: aiConfigKey,
            }),
        });

        if (!response.ok) {
            throw new Error(`Python API responded with status: ${response.status}`);
        }

        const pythonResponse = await response.json();
        
        res.status(200).json({ message: "Feedback received and processed" });
    } catch (error) {
        console.error("Error calling Python feedback API:", error);
        res.status(500).json({ error: "Internal server error" });
    }
}
