import { NextApiRequest, NextApiResponse } from "next";

export default async function chatMetricsToggleHealth(req: NextApiRequest, res: NextApiResponse) {
    try {
        const requestId = req.query.request_id as string;

        if (!requestId) {
            return res.status(400).json({ error: "Missing 'request_id' query parameter" });
        }

        // Call Python FastAPI backend metrics endpoint
        const pythonApiUrl = process.env.PYTHON_API_URL || "http://localhost:8000";
        
        const response = await fetch(`${pythonApiUrl}/api/chat-metrics-togglehealth?request_id=${requestId}`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (!response.ok) {
            throw new Error(`Backend responded with status: ${response.status}`);
        }

        const data = await response.json();
        res.status(200).json(data);
    } catch (error) {
        console.error("Error fetching ToggleHealth metrics:", error);
        res.status(500).json({ 
            error: error instanceof Error ? error.message : "Internal Server Error",
            status: "error"
        });
    }
}

