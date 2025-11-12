import { NextApiRequest, NextApiResponse } from "next";

export default async function chatMetricsResponse(req: NextApiRequest, res: NextApiResponse) {
    try {
        const { request_id } = req.query;
        
        if (!request_id || typeof request_id !== 'string') {
            return res.status(400).json({ error: "Missing or invalid 'request_id' parameter." });
        }

        // Call our Python FastAPI backend
        const pythonApiUrl = process.env.PYTHON_API_URL || "http://localhost:8000";
        
        const response = await fetch(`${pythonApiUrl}/api/chat-metrics?request_id=${request_id}`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            }
        });

        if (!response.ok) {
            throw new Error(`Python API responded with status: ${response.status}`);
        }

        const pythonResponse = await response.json();
        
        res.status(200).json(pythonResponse);
    } catch (error) {
        console.error("Error calling Python metrics API:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
} 