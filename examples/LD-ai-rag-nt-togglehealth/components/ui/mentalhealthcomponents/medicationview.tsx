import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../card";
import { Button } from "../button";
import { Badge } from "../badge";
import { motion } from "framer-motion";

export const MedicationAccount = () => {
	const [isExpanded, setIsExpanded] = useState(false);

	const medicationData = {
		status: "Active",
		adherence: "95%",
		nextRefill: "5 days",
		prescriptions: 3,
		pharmacist: "Dr. Michael Chen",
		lastReview: "2 weeks ago"
	};

	return (
		<motion.div
			whileHover={{ scale: 1.02 }}
			className="w-full"
		>
			<Card className="h-full border-2 border-green-200 hover:border-green-300 transition-colors">
				<CardHeader className="pb-3">
					<div className="flex items-center justify-between">
						<CardTitle className="text-lg font-semibold text-green-800">
							Medication
						</CardTitle>
						<Badge 
							variant={medicationData.status === "Active" ? "default" : "secondary"}
							className="bg-green-100 text-green-800"
						>
							{medicationData.status}
						</Badge>
					</div>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="grid grid-cols-2 gap-4 text-sm">
						<div>
							<p className="text-gray-600">Adherence</p>
							<p className="font-semibold text-green-700">{medicationData.adherence}</p>
						</div>
						<div>
							<p className="text-gray-600">Next Refill</p>
							<p className="font-semibold text-green-700">{medicationData.nextRefill}</p>
						</div>
						<div>
							<p className="text-gray-600">Prescriptions</p>
							<p className="font-semibold text-green-700">{medicationData.prescriptions}</p>
						</div>
						<div>
							<p className="text-gray-600">Pharmacist</p>
							<p className="font-semibold text-green-700">{medicationData.pharmacist}</p>
						</div>
					</div>
					
					{isExpanded && (
						<motion.div
							initial={{ opacity: 0, height: 0 }}
							animate={{ opacity: 1, height: "auto" }}
							className="space-y-3 pt-4 border-t border-gray-200"
						>
							<div className="flex items-center justify-between">
								<span className="text-sm text-gray-600">Last Review</span>
								<Badge variant="outline" className="text-blue-600 border-blue-300">
									{medicationData.lastReview}
								</Badge>
							</div>
							<div className="text-xs text-gray-500 space-y-1">
								<p>• Sertraline 50mg - 30 days remaining</p>
								<p>• Bupropion 150mg - 15 days remaining</p>
								<p>• Lorazepam 0.5mg - 45 days remaining</p>
							</div>
						</motion.div>
					)}
					
					<Button
						variant="outline"
						size="sm"
						className="w-full border-green-300 text-green-700 hover:bg-green-50"
						onClick={() => setIsExpanded(!isExpanded)}
					>
						{isExpanded ? "Show Less" : "View Details"}
					</Button>
				</CardContent>
			</Card>
		</motion.div>
	);
};
