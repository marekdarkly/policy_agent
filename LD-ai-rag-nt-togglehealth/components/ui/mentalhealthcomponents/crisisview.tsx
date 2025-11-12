import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../card";
import { Button } from "../button";
import { Badge } from "../badge";
import { motion } from "framer-motion";

export const CrisisMonitoringAccount = () => {
	const [isExpanded, setIsExpanded] = useState(false);

	const crisisData = {
		status: "Active",
		lastCheck: "2 hours ago",
		riskLevel: "Low",
		interventions: 3,
		contacts: 2,
		alerts: 1
	};

	return (
		<motion.div
			whileHover={{ scale: 1.02 }}
			className="w-full"
		>
			<Card className="h-full border-2 border-purple-200 hover:border-purple-300 transition-colors">
				<CardHeader className="pb-3">
					<div className="flex items-center justify-between">
						<CardTitle className="text-lg font-semibold text-purple-800">
							Crisis Monitoring
						</CardTitle>
						<Badge 
							variant={crisisData.status === "Active" ? "default" : "secondary"}
							className="bg-green-100 text-green-800"
						>
							{crisisData.status}
						</Badge>
					</div>
				</CardHeader>
				<CardContent className="space-y-4">
					<div className="grid grid-cols-2 gap-4 text-sm">
						<div>
							<p className="text-gray-600">Risk Level</p>
							<p className="font-semibold text-purple-700">{crisisData.riskLevel}</p>
						</div>
						<div>
							<p className="text-gray-600">Last Check</p>
							<p className="font-semibold text-purple-700">{crisisData.lastCheck}</p>
						</div>
						<div>
							<p className="text-gray-600">Interventions</p>
							<p className="font-semibold text-purple-700">{crisisData.interventions}</p>
						</div>
						<div>
							<p className="text-gray-600">Emergency Contacts</p>
							<p className="font-semibold text-purple-700">{crisisData.contacts}</p>
						</div>
					</div>
					
					{isExpanded && (
						<motion.div
							initial={{ opacity: 0, height: 0 }}
							animate={{ opacity: 1, height: "auto" }}
							className="space-y-3 pt-4 border-t border-gray-200"
						>
							<div className="flex items-center justify-between">
								<span className="text-sm text-gray-600">Recent Alerts</span>
								<Badge variant="outline" className="text-orange-600 border-orange-300">
									{crisisData.alerts} new
								</Badge>
							</div>
							<div className="text-xs text-gray-500 space-y-1">
								<p>• Safety plan updated 3 days ago</p>
								<p>• Crisis hotline contacted 1 week ago</p>
								<p>• Wellness check completed 2 weeks ago</p>
							</div>
						</motion.div>
					)}
					
					<Button
						variant="outline"
						size="sm"
						className="w-full border-purple-300 text-purple-700 hover:bg-purple-50"
						onClick={() => setIsExpanded(!isExpanded)}
					>
						{isExpanded ? "Show Less" : "View Details"}
					</Button>
				</CardContent>
			</Card>
		</motion.div>
	);
};
