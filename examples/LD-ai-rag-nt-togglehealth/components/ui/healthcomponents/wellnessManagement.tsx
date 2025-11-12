import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { WellnessManagementGraphDataType } from "./WellnessManagementGraph";

interface WellnessManagementSheetProps {
	data: WellnessManagementGraphDataType[];
	aiPrompt: string;
	submitQuery: (query: any) => Promise<string>;
	prompt: string;
	loading: boolean;
	aiResponse: string;
}

export default function WellnessManagementSheet({
	data,
	aiPrompt,
	submitQuery,
	prompt,
	loading,
	aiResponse,
}: WellnessManagementSheetProps) {
	const [showAnalysis, setShowAnalysis] = useState(false);

	const handleAnalysis = async () => {
		if (!showAnalysis) {
			await submitQuery(prompt);
		}
		setShowAnalysis(!showAnalysis);
	};

	return (
		<Card className="h-full">
			<CardHeader>
				<CardTitle className="text-lg font-semibold text-green-600">
					Health Analytics
				</CardTitle>
			</CardHeader>
			<CardContent className="space-y-4">
				<div className="space-y-3">
					<div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
						<div>
							<p className="font-medium text-sm">Current Wellness Score</p>
							<p className="text-2xl font-bold text-green-600">
								{data[data.length - 1]?.wellnessScore || 0}
							</p>
						</div>
						<div className="text-right">
							<p className="text-sm text-gray-500">Trend</p>
							<p className="text-sm font-medium text-green-600">+7 points</p>
						</div>
					</div>

					<div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
						<div>
							<p className="font-medium text-sm">Active Prescriptions</p>
							<p className="text-2xl font-bold text-blue-600">3</p>
						</div>
						<div className="text-right">
							<p className="text-sm text-gray-500">Status</p>
							<p className="text-sm font-medium text-blue-600">Good</p>
						</div>
					</div>

					<div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
						<div>
							<p className="font-medium text-sm">Upcoming Appointments</p>
							<p className="text-2xl font-bold text-purple-600">2</p>
						</div>
						<div className="text-right">
							<p className="text-sm text-gray-500">Next</p>
							<p className="text-sm font-medium text-purple-600">Tomorrow</p>
						</div>
					</div>
				</div>

				<Button
					onClick={handleAnalysis}
					disabled={loading}
					className="w-full bg-green-600 hover:bg-green-700"
				>
					{loading ? "Analyzing..." : showAnalysis ? "Hide Analysis" : "Get Health Analysis"}
				</Button>

				{showAnalysis && aiResponse && (
					<div className="p-4 bg-gray-50 rounded-lg">
						<h4 className="font-medium text-sm text-gray-700 mb-2">AI Health Analysis</h4>
						<p className="text-sm text-gray-600">{aiResponse}</p>
					</div>
				)}
			</CardContent>
		</Card>
	);
} 