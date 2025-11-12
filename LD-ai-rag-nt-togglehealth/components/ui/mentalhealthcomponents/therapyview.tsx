import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../card";
import { Button } from "../button";
import { Badge } from "../badge";
import { motion } from "framer-motion";

export const TherapyAccount = () => {
	const [isExpanded, setIsExpanded] = useState(false);

	const therapyData = {
		status: "Active",
		nextSession: "Tomorrow, 2:00 PM",
		sessionsCompleted: 12,
		therapist: "Dr. Sarah Johnson",
		modality: "CBT",
		progress: "Good"
	};

	return (
		<motion.div
			whileHover={{ scale: 1.02 }}
			className="w-full"
		>
			<Card className="h-full border-2 border-blue-200 hover:border-blue-300 transition-colors">
				<CardHeader className="pb-3">
					<div className="flex items-center justify-between">
						<CardTitle className="text-lg font-semibold text-blue-800">
							Therapy
						</CardTitle>
						<Badge 
							variant={therapyData.status === "Active" ? "default" : "secondary"}
							className="bg-blue-100 text-blue-800"
						>
							{therapyData.status}
						</Badge>
					</div>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="grid grid-cols-2 gap-4 text-sm">
						<div>
							<p className="text-gray-600">Next Session</p>
							<p className="font-semibold text-blue-700">{therapyData.nextSession}</p>
						</div>
						<div>
							<p className="text-gray-600">Sessions</p>
							<p className="font-semibold text-blue-700">{therapyData.sessionsCompleted}</p>
						</div>
						<div>
							<p className="text-gray-600">Therapist</p>
							<p className="font-semibold text-blue-700">{therapyData.therapist}</p>
						</div>
						<div>
							<p className="text-gray-600">Modality</p>
							<p className="font-semibold text-blue-700">{therapyData.modality}</p>
						</div>
					</div>
					
					{isExpanded && (
						<motion.div
							initial={{ opacity: 0, height: 0 }}
							animate={{ opacity: 1, height: "auto" }}
							className="space-y-3 pt-4 border-t border-gray-200"
						>
							<div className="flex items-center justify-between">
								<span className="text-sm text-gray-600">Progress</span>
								<Badge variant="outline" className="text-green-600 border-green-300">
									{therapyData.progress}
								</Badge>
							</div>
							<div className="text-xs text-gray-500 space-y-1">
								<p>• Last session: 3 days ago</p>
								<p>• Homework completed: 2/3 tasks</p>
								<p>• Mood tracking: 7 days streak</p>
							</div>
						</motion.div>
					)}
					
					<Button
						variant="outline"
						size="sm"
						className="w-full border-blue-300 text-blue-700 hover:bg-blue-50"
						onClick={() => setIsExpanded(!isExpanded)}
					>
						{isExpanded ? "Show Less" : "View Details"}
					</Button>
				</CardContent>
			</Card>
		</motion.div>
	);
};
